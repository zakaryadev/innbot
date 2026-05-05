import sqlite3
import pandas as pd
from config import DB_PATH, CSV_PATH
import os

def setup_database():
    print(f"Setting up database at {DB_PATH} from {CSV_PATH}...")
    
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print("Removed old database file.")

    df = None
    attempts = [
        {'encoding': 'cp1251', 'sep': ';'},
        {'encoding': 'utf-8',   'sep': ';'},
        {'encoding': 'utf-8',   'sep': ','},
        {'encoding': 'latin-1', 'sep': ';'},
        {'encoding': 'latin-1', 'sep': ','},
    ]
    for attempt in attempts:
        try:
            df = pd.read_csv(CSV_PATH, **attempt)
            print(f"Read CSV with encoding={attempt['encoding']}, sep='{attempt['sep']}'")
            break
        except Exception as e:
            print(f"Failed ({attempt['encoding']}/{attempt['sep']}): {e}")

    if df is None:
        print("ERROR: Could not read CSV file with any known encoding. Aborting.")
        return
    
    # Rename columns based on headers we discovered
    # Found columns: ['', 'Tashkilot', 'INN', 'Telefon']
    col_mapping = {}
    for col in df.columns:
        if 'Tashkilot' in col: col_mapping[col] = 'name'
        elif 'INN' in col: col_mapping[col] = 'inn'
        elif 'Telefon' in col: col_mapping[col] = 'phone'
        else: col_mapping[col] = 'id'
    
    df.rename(columns=col_mapping, inplace=True)
    
    # Clean data
    if 'name' in df.columns and 'inn' in df.columns:
        df = df.dropna(subset=['name', 'inn'])
        
        # Ensure inn is string without .0
        df['inn'] = df['inn'].astype(str).str.replace(r'\.0$', '', regex=True)
        # Ensure id is int or string
        if 'id' in df.columns:
            df['id'] = df['id'].fillna(0).astype(int).astype(str)
        if 'phone' in df.columns:
            df['phone'] = df['phone'].fillna("N/A").astype(str)

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE organizations (
                id TEXT,
                name TEXT,
                inn TEXT,
                phone TEXT
            )
        ''')

        df[['id', 'name', 'inn', 'phone']].to_sql('organizations', conn, if_exists='append', index=False)
        
        cursor.execute("CREATE INDEX idx_name ON organizations(name);")
        cursor.execute("CREATE INDEX idx_inn ON organizations(inn);")
        cursor.execute("CREATE INDEX idx_id ON organizations(id);")

        conn.commit()
        conn.close()
        print(f"Successfully inserted {len(df)} records into {DB_PATH}.")
    else:
        print("Error: Could not find required columns in the CSV. Found columns:", df.columns)

if __name__ == "__main__":
    setup_database()
