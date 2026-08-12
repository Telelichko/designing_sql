"""Execute queries from a given SQL file and save results to CSV files in Data/Out/query_results."""

import argparse
import re
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text

DSN = 'postgresql+psycopg2://myuser:mypassword@127.0.0.1:54321/datapack'
OUTPUT_DIR = Path('Data/Out/query_results/')


def read_queries_by_blocks(sql_file: Path):
    """Split SQL file into blocks using the separator line."""
    with open(sql_file, 'r', encoding='utf-8') as f:
        content = f.read()

    blocks = content.split('-- ============================================================================')
    queries = []
    for block in blocks:
        cleaned = block.strip()
        if cleaned:
            queries.append(cleaned)
    return queries


def remove_comments(sql: str) -> str:
    """Remove single-line (--) and multi-line (/* */) comments from SQL."""
    # Remove -- comments (from -- to end of line)
    sql = re.sub(r'--[^\n]*', '', sql)
    # Remove /* */ comments (non-greedy)
    sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)
    return sql


def is_empty_query(query_text: str) -> bool:
    """Check if query contains only comments and whitespace."""
    cleaned = remove_comments(query_text).strip()
    return len(cleaned) == 0


def is_select_query(query_text: str) -> bool:
    """Check if the query is a SELECT or WITH statement (case-insensitive)."""
    cleaned = remove_comments(query_text).strip()
    if not cleaned:
        return False
    upper = cleaned.upper()
    return upper.startswith('SELECT') or upper.startswith('WITH')


def run_queries(sql_file: str = 'queries.sql'):
    print('Connecting to database...')
    eng = create_engine(DSN)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f'Output directory ensured: {OUTPUT_DIR.resolve()}')

    sql_path = Path(sql_file)
    if not sql_path.exists():
        print(f'Error: SQL file "{sql_file}" not found.')
        return

    queries = read_queries_by_blocks(sql_path)
    if not queries:
        print('No valid queries found in the file.')
        return

    query_counter = 1
    for query_text in queries:
        # Skip blocks that contain only comments
        if is_empty_query(query_text):
            print(f'\n⚠️ Skipping empty or comment-only block')
            continue

        print(f'\n{"=" * 60}')
        print(f'Executing Query {query_counter}...')
        print(f'{"=" * 60}')

        try:
            if is_select_query(query_text):
                # For SELECT queries, fetch results as DataFrame
                df = pd.read_sql(text(query_text), eng)
                print(df.to_string(index=False))

                csv_file = OUTPUT_DIR / f'result_query_{query_counter}.csv'
                df.to_csv(csv_file, index=False, encoding='utf-8')
                print(f'\n✓ Results saved to {csv_file.resolve()}')
            else:
                # For DDL/DML (non-SELECT), execute without fetching results
                with eng.connect() as conn:
                    conn.execute(text(query_text))
                    conn.commit()
                print(f'✓ Query executed successfully (no rows returned)')

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