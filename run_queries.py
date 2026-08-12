"""Execute queries from a given SQL file and save results to CSV files in Data/Out/query_results."""

import argparse
import re
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text

DSN = 'postgresql+psycopg2://myuser:mypassword@127.0.0.1:54321/datapack'
OUTPUT_DIR = Path('Data/Out/query_results/')


def run_queries(sql_file: str = 'queries.sql'):
    """Read SQL file, execute each query, and save results as CSV."""
    print('Connecting to database...')
    eng = create_engine(DSN)

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f'Output directory ensured: {OUTPUT_DIR.resolve()}')

    # Read the SQL file
    sql_path = Path(sql_file)
    if not sql_path.exists():
        print(f'Error: SQL file "{sql_file}" not found.')
        return

    with open(sql_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    # Split queries by semicolon
    raw_queries = sql_content.split(';')

    query_counter = 1
    for raw_q in raw_queries:
        query = raw_q.strip()
        if not query:
            continue

        # Strip comments to detect empty blocks
        clean_query = re.sub(r'--.*', '', query)
        clean_query = re.sub(r'/\*.*?\*/', '', clean_query, flags=re.DOTALL)
        if not clean_query.strip():
            continue

        print(f'\n{"=" * 60}')
        print(f'Executing Query {query_counter}...')
        print(f'{"=" * 60}')

        try:
            df = pd.read_sql(text(query), eng)
            print(df.to_string(index=False))

            csv_file = OUTPUT_DIR / f'result_query_{query_counter}.csv'
            df.to_csv(csv_file, index=False, encoding='utf-8')
            print(f'\n✓ Results saved to {csv_file.resolve()}')

            query_counter += 1

        except Exception as e:
            print(f'✗ Error executing query {query_counter}: {e}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Execute SQL queries from a file and save results to CSV.'
    )
    parser.add_argument(
        'sql_file',
        nargs='?',
        default='queries.sql',
        help='Path to the SQL file (default: queries.sql)'
    )
    args = parser.parse_args()
    run_queries(args.sql_file)
    