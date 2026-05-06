import sqlite3
import pandas as pd
import os
from config import DB_PATH

def import_csv():
    csv_file = r"d:\Projects\2026\TELEGRAM BOT\INN\Нокис хамме мекемелер_latin.csv"
    
    if not os.path.exists(csv_file):
        print("CSV fayli topilmadi!")
        return

    print("CSV fayl o'qilmoqda...")
    # Read CSV
    df = pd.read_csv(csv_file, delimiter=';', header=0)
    
    # Rename columns explicitly based on the first two column indices
    df = df.rename(columns={df.columns[0]: 'name', df.columns[1]: 'inn'})
    
    # Drop completely empty rows based on name and inn
    df = df.dropna(subset=['name', 'inn'], how='all')
    
    # Handle missing or formatting issues
    # Clean up '.0' from ends of INNs if any
    df['inn'] = df['inn'].fillna("Noma'lum").astype(str).str.replace(r'\.0$', '', regex=True)
    df['name'] = df['name'].fillna("Noma'lum").astype(str)
    
    # Add required phone and id fields
    df['phone'] = "N/A"
    df['id'] = range(1, len(df) + 1)
    df['id'] = df['id'].astype(str)

    # Reorder columns to match the database table
    final_df = df[['id', 'name', 'inn', 'phone']]

    print(f"Baza uchun tayyorlangan yozuvlar: {len(final_df)}")
    print(f"Bazaga yozilmoqda: {DB_PATH}")
    
    # Instead of deleting the file, we just connect and drop the table
    # This avoids PermissionError if the file is opened by another program
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("DROP TABLE IF EXISTS organizations;")


    cursor.execute('''
        CREATE TABLE organizations (
            id TEXT,
            name TEXT,
            inn TEXT,
            phone TEXT
        )
    ''')

    # Insert data
    final_df.to_sql('organizations', conn, if_exists='append', index=False)
    
    # Create indexes for fast lookup
    cursor.execute("CREATE INDEX idx_name ON organizations(name);")
    cursor.execute("CREATE INDEX idx_inn ON organizations(inn);")
    
    conn.commit()
    conn.close()
    
    print(f"Baza tayyor! {len(final_df)} ta tashkilot malumotlar bazasiga joylandi.")

if __name__ == "__main__":
    import_csv()
