"""Read all pages from Data/In/data_pack → clean, validate, deduplicate → load into PostgreSQL → export schema.
Optional: save cleaned (all) and unique data to CSV files in Data/Out/csv_results (use --save-csv flag).
"""

import json
import re
import subprocess
import hashlib
import argparse
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.types import VARCHAR, NUMERIC, INTEGER

# ── Configuration ─────────────────────────────────────────────────────────────
SRC = Path("Data/In/data_pack")
DSN = "postgresql+psycopg2://myuser:mypassword@127.0.0.1:54321/datapack"
TABLE = "companies"
CSV_OUT_DIR = Path("Data/Out/csv_results")


# ── 1. Read all files / all pages ────────────────────────────────────────────
def read_all(path: Path) -> pd.DataFrame:
    frames = []
    for f in sorted(path.iterdir()):
        if f.suffix in (".xlsx", ".xls"):
            xls = pd.ExcelFile(f)
            frames += [xls.parse(sheet_name=s) for s in xls.sheet_names]
        elif f.suffix == ".csv":
            frames.append(pd.read_csv(f))
        elif f.suffix == ".json":
            with open(f, 'r', encoding='utf-8') as jf:
                data = json.load(jf)
            items = data.get('items', data.get('items ', []))
            if isinstance(items, list) and len(items) > 0:
                df_temp = pd.DataFrame(items)
                df_temp.rename(columns=lambda x: x.strip(), inplace=True)
                frames.append(df_temp)
            else:
                frames.append(pd.read_json(f))
    if not frames:
        raise ValueError(f"No supported files (.xlsx, .csv, .json) found in {path}")
    df = pd.concat(frames, ignore_index=True)
    print(f"Read {len(df)} rows from all files")
    return df


# ── 2. Clean and normalise (no email filtering yet) ──────────────────────────
def clean_and_validate(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise columns, handle missing values, generate email.
    Returns DataFrame with all rows (including those with potentially invalid email).
    """
    df = df.copy()
    df.columns = df.columns.str.strip()

    # Handle missing values
    empty_vals = ['', ' ', 'N/A', 'nan', 'None', 'NULL', 'н/д', 'много']
    df = df.replace(empty_vals, pd.NA)

    # Normalize numeric columns
    if 'rating' in df.columns:
        df['rating'] = df['rating'].astype(str).str.replace(',', '.', regex=False)
        df['rating'] = pd.to_numeric(df['rating'], errors='coerce')
    if 'reviews_count' in df.columns:
        df['reviews_count'] = pd.to_numeric(
            df['reviews_count'].astype(str).str.strip(), errors='coerce'
        )

    # Generate email for every row
    def make_valid_email(row):
        site = str(row.get('site', '')).strip()
        if site and site.startswith('http'):
            try:
                domain = urlparse(site).netloc
                if domain:
                    return f"info@{domain}"
            except Exception:
                pass
        name = str(row.get('name', 'company')).strip()
        slug = re.sub(r'[^a-zA-Z0-9а-яА-ЯёЁ]', '', name).lower().replace(' ', '-')[:30]
        if not slug:
            slug = 'company'
        return f"contact@{slug}.ru"

    df['email'] = df.apply(make_valid_email, axis=1)

    # Normalize remaining string columns
    for col in df.select_dtypes(include=['object', 'string']).columns:
        if col == 'email':
            continue
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].replace(['nan', 'None', 'NA', ''], pd.NA)

    print(f"After cleaning (all rows): {len(df)} rows")
    return df


# ── 3. Filter valid emails ────────────────────────────────────────────────────
def filter_valid_emails(df: pd.DataFrame) -> pd.DataFrame:
    """Remove rows with invalid email format."""
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    valid_mask = df['email'].str.match(email_regex, na=False)
    invalid_count = (~valid_mask).sum()
    if invalid_count:
        print(f"Warning: {invalid_count} rows with invalid email will be dropped")
    df_valid = df[valid_mask].copy()
    print(f"After email filtering: {len(df_valid)} rows")
    return df_valid


# ── 4. Deduplicate (improved: by id, business key, full hash) ──────────────
def row_hash(row: pd.Series) -> str:
    """Compute SHA-256 hash of a row (all values to JSON)."""
    serializable = {}
    for k, v in row.items():
        if pd.isna(v):
            serializable[k] = None
        elif isinstance(v, (dict, list, set, tuple)):
            serializable[k] = json.dumps(v, sort_keys=True, default=str)
        else:
            serializable[k] = str(v)
    return hashlib.sha256(
        json.dumps(serializable, sort_keys=True).encode()
    ).hexdigest()

def dedup(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)

    # Convert unhashable types to JSON strings (safety)
    for col in df.columns:
        mask = df[col].apply(lambda x: isinstance(x, (dict, list)))
        if mask.any():
            df.loc[mask, col] = df.loc[mask, col].apply(
                lambda x: json.dumps(x, sort_keys=True, default=str)
            )

    # Stage 1: drop duplicates by 'id' if exists
    if 'id' in df.columns:
        df = df.drop_duplicates(subset=['id']).reset_index(drop=True)
        print(f"After dedup by id: {len(df)} rows")

    # Stage 2: drop duplicates by business key (name + city + address)
    key_cols = ['name', 'city', 'address']
    key_cols_exist = [c for c in key_cols if c in df.columns]
    if key_cols_exist:
        df = df.drop_duplicates(subset=key_cols_exist).reset_index(drop=True)
        print(f"After dedup by business key {key_cols_exist}: {len(df)} rows")

    # Stage 3: drop exact duplicates across all columns (full hash)
    df['_hash'] = df.apply(row_hash, axis=1)
    df = df.drop_duplicates(subset='_hash').drop(columns='_hash').reset_index(drop=True)

    print(f"Dedup final: {before} → {len(df)} rows")
    return df


# ── 5. Load into PostgreSQL ──────────────────────────────────────────────────
def load(df: pd.DataFrame):
    print(f"Connecting to: {DSN}")
    eng = create_engine(DSN)

    db_schema = {
        'id': VARCHAR(50),
        'name': VARCHAR(255),
        'category': VARCHAR(100),
        'city': VARCHAR(100),
        'address': VARCHAR(255),
        'rating': NUMERIC(5, 2),
        'reviews_count': INTEGER,
        'site': VARCHAR(255),
        'phone': VARCHAR(50),
        'email': VARCHAR(255)
    }
    active_schema = {k: v for k, v in db_schema.items() if k in df.columns}

    df.to_sql(TABLE, eng, if_exists="replace", index=False,
              method="multi", chunksize=5000, dtype=active_schema)
    print(f"Inserted {len(df)} rows into '{TABLE}'")

    # Add PRIMARY KEY on 'id' if exists, else surrogate key
    with eng.begin() as conn:
        if 'id' in df.columns:
            pk_name = f"{TABLE}_pkey"
            result = conn.execute(text(f"""
                SELECT 1 FROM pg_constraint WHERE conname = '{pk_name}'
            """))
            if result.scalar() is not None:
                conn.execute(text(f'ALTER TABLE "{TABLE}" DROP CONSTRAINT {pk_name}'))
            conn.execute(text(f'ALTER TABLE "{TABLE}" ADD PRIMARY KEY ("id")'))
            print("Primary key on 'id' added")
        else:
            conn.execute(text(f'ALTER TABLE "{TABLE}" ADD COLUMN "_row_id" SERIAL PRIMARY KEY'))
            print("Surrogate primary key added")

    # Create indexes on commonly filtered columns
    index_cols = ["category", "city", "rating", "reviews_count", "email"]
    with eng.begin() as conn:
        for col in index_cols:
            if col in df.columns:
                idx_name = f"ix_{TABLE}_{col}"
                result = conn.execute(text(f"""
                    SELECT 1 FROM pg_indexes WHERE indexname = '{idx_name}'
                """))
                if result.scalar() is None:
                    conn.execute(text(f'CREATE INDEX "{idx_name}" ON "{TABLE}" ("{col}")'))
                    print(f"Index {idx_name} created")
                else:
                    print(f"Index {idx_name} already exists, skipping")
    print("Indexes ready.")


# ── 6. Save CSV files ────────────────────────────────────────────────────────
def save_csv(df: pd.DataFrame, filename: str):
    CSV_OUT_DIR.mkdir(parents=True, exist_ok=True)
    filepath = CSV_OUT_DIR / filename
    df.to_csv(filepath, index=False, encoding='utf-8')
    print(f"Saved {len(df)} rows to {filepath.resolve()}")


# ── 7. Export schema to file ──────────────────────────────────────────────────
def export_schema():
    print("Exporting schema to schema.sql...")
    cmd = [
        "docker", "compose", "exec", "-T", "pg",
        "pg_dump", "-U", "myuser", "-d", "datapack", "--schema-only"
    ]
    try:
        with open("schema.sql", "w", encoding="utf-8") as f:
            subprocess.run(cmd, stdout=f, check=True)
        print("Schema exported to schema.sql")
    except subprocess.CalledProcessError as e:
        print(f"Warning: export failed. Error: {e}")


# ── 8. Main ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Load data to PostgreSQL and optionally save CSV exports."
    )
    parser.add_argument(
        "--save-csv",
        action="store_true",
        help="Save cleaned (all) and unique data to CSV files in Data/Out/csv_results"
    )
    args = parser.parse_args()

    # 1. Read raw data
    df_raw = read_all(SRC)

    # 2. Clean and normalise (all rows, no email filtering yet)
    df_all = clean_and_validate(df_raw)

    # 3. If --save-csv, save the full dataset (all rows, including invalid emails)
    if args.save_csv:
        save_csv(df_all, "full_data.csv")

    # 4. Filter only valid emails
    df_valid = filter_valid_emails(df_all)

    # 5. Deduplicate
    df_unique = dedup(df_valid)

    # 6. If --save-csv, save the unique dataset
    if args.save_csv:
        save_csv(df_unique, "unique_data.csv")

    # 7. Load to PostgreSQL and export schema
    load(df_unique)
    export_schema()