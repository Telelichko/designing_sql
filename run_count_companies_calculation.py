import json
from pathlib import Path
import pandas as pd

# Define the directory path
data_dir = Path('Data/In/data_pack')

# List to store the results
records = []

# Iterate through all .json files in the directory, sorted by name
for n, file_path in enumerate(sorted(data_dir.glob('*.json')), start=1):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # The provided JSON uses 'items ' (with a trailing space) as the key.
    # We check both 'items' and 'items ' to be safe.
    items_list = data.get('items', data.get('items ', []))
    count = len(items_list) if isinstance(items_list, list) else 0
    
    records.append({
        'N': n,
        'file_name': file_path.name,
        'count_companies': count
    })

# Create the Pandas DataFrame
df_companies_count = pd.DataFrame(records)

# Print the DataFrame
print(df_companies_count.to_string(index=False))

# Print the sum of the 'count_companies' column
print(f"\nSum of count_companies: {df_companies_count['count_companies'].sum()}")