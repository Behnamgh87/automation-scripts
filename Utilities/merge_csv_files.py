import os
import csv

# Prompt the user for the folder path
folder = input("Enter the path to the folder containing CSV files (leave blank for current directory): ").strip()
if not folder:
    folder = os.getcwd()

output_file = os.path.join(folder, 'merge.csv')

# Find all CSV files in the folder (excluding the output file)
csv_files = [f for f in os.listdir(folder) if f.endswith('.csv') and f != 'merge.csv']

all_rows = []
all_headers = set()

# Read all CSV files and collect headers and rows
for filename in csv_files:
    with open(os.path.join(folder, filename), 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        all_rows.extend(rows)
        all_headers.update(reader.fieldnames or [])

all_headers = list(all_headers)

# Write merged CSV
with open(output_file, 'w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=all_headers)
    writer.writeheader()
    for row in all_rows:
        # Fill missing columns with empty string
        full_row = {header: row.get(header, '') for header in all_headers}
        writer.writerow(full_row)

print(f"Merged {len(csv_files)} CSV files into {output_file}") 