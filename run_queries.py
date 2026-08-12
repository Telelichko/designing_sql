'''Execute queries from queries.sql and save results to CSV files in Data/In.'''

import re
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text

DSN = 'postgresql+psycopg2://myuser:mypassword@127.0.0.1:54321/datapack'
OUTPUT_DIR = Path('Data/Out/query_results/')

def run_queries():
    print('Connecting to database...')
    eng = create_engine(DSN)
    
    # Check and create the output directory if it does not exist
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f'Output directory ensured: {OUTPUT_DIR.resolve()}')
    
    # Read queries.sql
    with open('queries.sql', 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # Split by semicolons
    raw_queries = sql_content.split(';')
    
    query_counter = 1
    for raw_q in raw_queries:
        query = raw_q.strip()
        if not query:
            continue
            
        # Remove single-line (--) and multi-line (/* */) comments to check if it is real SQL
        clean_query = re.sub(r'--.*', '', query)
        clean_query = re.sub(r'/\*.*?\*/', '', clean_query, flags=re.DOTALL)
        
        # If nothing remains after removing comments, skip this block
        if not clean_query.strip():
            continue
            
        print(f'\n{"="*60}')
        print(f'Executing Query {query_counter}...')
        print(f'{"="*60}')
        
        try:
            # Execute the original query (PostgreSQL handles the comments fine)
            df = pd.read_sql(text(query), eng)
            print(df.to_string(index=False))
            
            # Save to CSV in the Data/In directory
            csv_file = OUTPUT_DIR / f'result_query_{query_counter}.csv'
            df.to_csv(csv_file, index=False, encoding='utf-8')
            print(f'\n✓ Results saved to {csv_file.resolve()}')
            
            query_counter += 1
            
        except Exception as e:
            print(f'✗ Error executing query {query_counter}: {e}')

if __name__ == '__main__':
    run_queries()