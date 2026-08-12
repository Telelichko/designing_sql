#!/usr/bin/env python3
"""
Read all pages from Data/In/data_pack (or specified source) → clean, validate,
deduplicate → load into PostgreSQL → export schema.
Optional: save cleaned (all) and unique data to CSV files in Data/Out/csv_results
(use --save-csv flag).
Also writes a data anomalies report to ANOMALIES.md.

USAGE EXAMPLES
--------------
  python script.py                         # use default source (Data/In/data_pack)
  python script.py --source /path/to/data  # custom local directory or file
  python script.py --source https://example.com/data.xlsx   # download remote file
  python script.py --save-csv              # also save CSV exports
  python script.py --source data.csv --save-csv
"""

import json
import re
import subprocess
import hashlib
import argparse
import tempfile
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.types import VARCHAR, NUMERIC, INTEGER

# ── Configuration ─────────────────────────────────────────────────────────────
DEFAULT_SRC = Path("Data/In/data_pack")
DSN = "postgresql+psycopg2://myuser:mypassword@127.0.0.1:54321/datapack"
TABLE = "companies"
CSV_OUT_DIR = Path("Data/Out/csv_results")


# ── 1. Read all files / all pages ────────────────────────────────────────────
def read_all(path: Path) -> pd.DataFrame:
    """Read a directory (all supported files) or a single file."""
    frames = []
    if path.is_file():
        files_to_read = [path]
    elif path.is_dir():
        files_to_read = sorted(path.iterdir())
    else:
        raise ValueError(f"Source does not exist: {path}")

    for f in files_to_read:
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
    print(f"Read {len(df)} rows from all files in {path}")
    return df


def download_source(url: str) -> Path:
    """Download a file from URL to a temporary directory and return its path."""
    temp_dir = Path(tempfile.mkdtemp(prefix="data_pack_download_"))
    filename = url.split('/')[-1] or "downloaded_file"
    local_path = temp_dir / filename
    print(f"Downloading {url} to {local_path} ...")
    urllib.request.urlretrieve(url, local_path)
    print("Download complete.")
    return local_path


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


# ── 3. Filter valid emails (prints each invalid row as id + url) ────────────
def filter_valid_emails(df: pd.DataFrame) -> pd.DataFrame:
    """Remove rows with invalid email format.
    Prints each invalid row as 'id, invalid email: {email}' (and site if available).
    """
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    valid_mask = df['email'].str.match(email_regex, na=False)
    invalid_mask = ~valid_mask
    invalid_count = invalid_mask.sum()

    if invalid_count > 0:
        invalid_rows = df.loc[invalid_mask, ['id', 'email', 'site']].copy()
        # Drop rows where email is NaN (should not happen)
        invalid_rows = invalid_rows[invalid_rows['email'].notna()]

        print(f"\n⚠️ Found {invalid_count} rows with invalid email (these will be dropped)")
        if len(invalid_rows) > 0:
            print("   Invalid emails (id, email, site):")
            for idx, row in invalid_rows.head(10).iterrows():
                site_info = f", site: {row['site']}" if pd.notna(row['site']) and str(row['site']).strip() else ""
                print(f"     {row['id']}, invalid email: {row['email']}{site_info}")
            if len(invalid_rows) > 10:
                print(f"     ... and {len(invalid_rows) - 10} more")
        else:
            print("   (No rows with non-null email among invalid rows)")
        print()

        df_valid = df[valid_mask].copy()
    else:
        df_valid = df.copy()

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

    # Drop rows with NULL id before loading if 'id' column exists
    if 'id' in df.columns:
        null_id_count = df['id'].isna().sum()
        if null_id_count > 0:
            print(f"⚠️ Dropping {null_id_count} rows with NULL 'id' before loading.")
            df = df[df['id'].notna()].copy()
            # Append to ANOMALIES.md
            with open("ANOMALIES.md", "a", encoding="utf-8") as f:
                f.write(f"\n## NULL IDs Dropped\n")
                f.write(f"Before loading, {null_id_count} rows with NULL 'id' were removed.\n")

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
            # Drop any existing primary key constraint with the default name
            pk_name = f"{TABLE}_pkey"
            result = conn.execute(text(f"""
                SELECT 1 FROM pg_constraint WHERE conname = '{pk_name}'
            """))
            if result.scalar() is not None:
                conn.execute(text(f'ALTER TABLE "{TABLE}" DROP CONSTRAINT {pk_name}'))
                print(f"Dropped existing primary key {pk_name}")

            # Now it's safe to add primary key because we have no NULL ids
            conn.execute(text(f'ALTER TABLE "{TABLE}" ADD PRIMARY KEY ("id")'))
            print("Primary key on 'id' added")
        else:
            # No 'id' column – add surrogate key
            conn.execute(text(f'ALTER TABLE "{TABLE}" ADD COLUMN "_row_id" SERIAL PRIMARY KEY'))
            print("Surrogate primary key added (no 'id' column present)")

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


# ── 8. Anomaly detection ────────────────────────────────────────────────────
def detect_anomalies(df: pd.DataFrame) -> str:
    """Generate a Markdown report of data anomalies."""
    lines = []
    lines.append("# Data Anomalies Report")
    lines.append(f"**Generated:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**Total rows:** {len(df)}")
    lines.append("")

    # Missing values
    missing = df.isnull().sum()
    missing = missing[missing > 0]
    if not missing.empty:
        lines.append("## Missing Values")
        for col, count in missing.items():
            pct = count / len(df) * 100
            lines.append(f"- **{col}**: {count} missing ({pct:.1f}%)")
    else:
        lines.append("## Missing Values")
        lines.append("No missing values found.")
    lines.append("")

    # Rating out of 0-5
    if 'rating' in df.columns:
        rating = pd.to_numeric(df['rating'], errors='coerce')
        invalid = rating[(rating < 0) | (rating > 5)].dropna()
        if len(invalid) > 0:
            lines.append("## Rating Out of Range (0–5)")
            lines.append(f"Found {len(invalid)} rows with rating outside 0–5.")
            sample = df.loc[invalid.index, ['id', 'name', 'rating']].head(5)
            for _, row in sample.iterrows():
                lines.append(f"- id: {row['id']}, name: {row['name']}, rating: {row['rating']}")
        else:
            lines.append("## Rating Out of Range")
            lines.append("All ratings are within 0–5.")
        lines.append("")

    # Negative reviews_count
    if 'reviews_count' in df.columns:
        neg = df[df['reviews_count'] < 0]
        if len(neg) > 0:
            lines.append("## Negative Reviews Count")
            lines.append(f"Found {len(neg)} rows with negative reviews_count.")
            sample = neg[['id', 'name', 'reviews_count']].head(5)
            for _, row in sample.iterrows():
                lines.append(f"- id: {row['id']}, name: {row['name']}, reviews_count: {row['reviews_count']}")
        else:
            lines.append("## Negative Reviews Count")
            lines.append("No negative reviews counts.")
        lines.append("")

    # Duplicate IDs (before dedup)
    if 'id' in df.columns:
        dup_mask = df['id'].duplicated()
        if dup_mask.any():
            lines.append("## Duplicate IDs")
            lines.append(f"Found {dup_mask.sum()} duplicate ID entries.")
            dup_examples = df[df['id'].duplicated(keep=False)].sort_values('id')[['id', 'name']].head(10)
            for _, row in dup_examples.iterrows():
                lines.append(f"- id: {row['id']}, name: {row['name']}")
        else:
            lines.append("## Duplicate IDs")
            lines.append("No duplicate IDs found.")
        lines.append("")

    # Missing critical fields (id or name)
    critical = ['id', 'name']
    missing_crit = df[critical].isnull().any(axis=1).sum()
    if missing_crit > 0:
        lines.append("## Missing Critical Fields (id or name)")
        lines.append(f"Found {missing_crit} rows missing either 'id' or 'name'.")
        sample = df[df[critical].isnull().any(axis=1)][['id', 'name']].head(5)
        for _, row in sample.iterrows():
            lines.append(f"- id: {row['id']}, name: {row['name']}")
    else:
        lines.append("## Missing Critical Fields")
        lines.append("All rows have both 'id' and 'name'.")
    lines.append("")

    return "\n".join(lines)


# ── 9. Main ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Load data to PostgreSQL and optionally save CSV exports.\n\n"
            "Examples:\n"
            "  %(prog)s                         # use default source\n"
            "  %(prog)s --source /path/to/data  # custom directory/file\n"
            "  %(prog)s --source https://...    # download remote file\n"
            "  %(prog)s --save-csv              # also save CSV files"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--save-csv",
        action="store_true",
        help="Save cleaned (all) and unique data to CSV files in Data/Out/csv_results"
    )
    parser.add_argument(
        "--source", "-s",
        type=str,
        default=str(DEFAULT_SRC),
        help=(
            "Source path (local file/directory or HTTP/HTTPS URL). "
            "If a URL is given, the file will be downloaded to a temporary location "
            "and processed. Default: Data/In/data_pack"
        )
    )
    args = parser.parse_args()

    # Resolve the source
    src_str = args.source
    if src_str.startswith(('http://', 'https://')):
        source_path = download_source(src_str)
    else:
        source_path = Path(src_str)
        if not source_path.exists():
            raise FileNotFoundError(f"Source path does not exist: {source_path}")

    # 1. Read raw data
    df_raw = read_all(source_path)

    # 2. Clean and normalise (all rows, no email filtering yet)
    df_all = clean_and_validate(df_raw)

    # ── Detect anomalies and write report ──
    anomalies_report = detect_anomalies(df_all)
    with open("ANOMALIES.md", "w", encoding="utf-8") as f:
        f.write(anomalies_report)
    print("Anomalies report written to ANOMALIES.md")

    # 3. If --save-csv, save the full dataset (all rows, including invalid emails)
    if args.save_csv:
        save_csv(df_all, "full_data.csv")

    # 4. Filter only valid emails (prints invalid URLs before dropping)
    df_valid = filter_valid_emails(df_all)

    # 5. Deduplicate
    df_unique = dedup(df_valid)

    # 6. If --save-csv, save the unique dataset
    if args.save_csv:
        save_csv(df_unique, "unique_data.csv")

    # 7. Load to PostgreSQL and export schema
    load(df_unique)
    export_schema()