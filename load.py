"""Read all pages from Data/In/data_pack → deduplicate → load into PostgreSQL."""

import json
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text

SRC = Path("Data/In/data_pack")
# Unique port 54321 and new credentials to bypass local Windows conflicts
DSN = "postgresql+psycopg2://myuser:mypassword@127.0.0.1:54321/datapack"
TABLE = "records"

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
            frames.append(pd.read_json(f))
    
    if not frames:
        raise ValueError(f"No supported files (.xlsx, .csv, .json) found in {path}")
    return pd.concat(frames, ignore_index=True)

# ── 2. Deduplicate ───────────────────────────────────────────────────────────
def dedup(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    
    # Convert unhashable types (dict, list) to JSON strings for correct deduplication
    for col in df.columns:
        mask = df[col].apply(lambda x: isinstance(x, (dict, list)))
        if mask.any():
            df.loc[mask, col] = df.loc[mask, col].apply(
                lambda x: json.dumps(x, sort_keys=True, default=str)
            )
    
    df = df.drop_duplicates().reset_index(drop=True)
    print(f"Dedup: {before} → {len(df)} rows")
    return df

# ── 3. Load + schema + indexes ───────────────────────────────────────────────
def load(df: pd.DataFrame):
    print(f"Connecting to: {DSN}")  # Confirm the script is using the correct settings
    eng = create_engine(DSN)

    # Write table (replace on first run)
    df.to_sql(TABLE, eng, if_exists="replace", index=False, method="multi", chunksize=5000)
    print(f"Inserted {len(df)} rows into '{TABLE}'")

    # Add UNIQUE constraint on all columns (deduplication at the DB level)
    cols = ", ".join(f'"{c}"' for c in df.columns)
    with eng.begin() as c:
        c.execute(text(f'ALTER TABLE "{TABLE}" ADD CONSTRAINT uq_row UNIQUE ({cols})'))
        print("Added UNIQUE constraint on all columns")

    # B-tree index on each column for fast lookups
    for col in df.columns:
        idx = f"ix_{TABLE}_{col}"
        with eng.begin() as c:
            c.execute(text(f'CREATE INDEX IF NOT EXISTS "{idx}" ON "{TABLE}" ("{col}")'))
    
    print("Successfully loaded and indexed data.")

# ── main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    df = read_all(SRC)
    df = dedup(df)
    load(df)