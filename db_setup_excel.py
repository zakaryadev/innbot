import sqlite3
import pandas as pd
import os
from config import DB_PATH
import glob

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def cyrillic_to_latin(text):
    if not isinstance(text, str):
        return text
    
    mapping = {
        'А': 'A', 'а': 'a',
        'Ә': 'Á', 'ә': 'á',
        'Б': 'B', 'б': 'b',
        'В': 'V', 'в': 'v',
        'Г': 'G', 'г': 'g',
        'Ғ': 'Ǵ', 'ғ': 'ǵ',
        'Д': 'D', 'д': 'd',
        'Е': 'E', 'е': 'e',
        'Ё': 'Yo', 'ё': 'yo',
        'Ж': 'J', 'ж': 'j',
        'З': 'Z', 'з': 'z',
        'И': 'I', 'и': 'i',
        'Й': 'Y', 'й': 'y',
        'К': 'K', 'к': 'k',
        'Қ': 'Q', 'қ': 'q',
        'Л': 'L', 'л': 'l',
        'М': 'M', 'м': 'm',
        'Н': 'N', 'н': 'n',
        'Ң': 'Ń', 'ң': 'ń',
        'О': 'O', 'о': 'o',
        'Ө': 'Ó', 'ө': 'ó',
        'П': 'P', 'п': 'p',
        'Р': 'R', 'р': 'r',
        'С': 'S', 'с': 's',
        'Т': 'T', 'т': 't',
        'У': 'U', 'у': 'u',
        'Ү': 'Ú', 'ү': 'ú',
        'Ў': 'W', 'ў': 'w',
        'Ф': 'F', 'ф': 'f',
        'Х': 'X', 'х': 'x',
        'Ҳ': 'H', 'ҳ': 'h',
        'Ц': 'C', 'ц': 'c',
        'Ч': 'Ch', 'ч': 'ch',
        'Ш': 'Sh', 'ш': 'sh',
        'Щ': 'Sh', 'щ': 'sh',
        'Ъ': '', 'ъ': '',
        'Ы': 'I', 'ы': 'ı',
        'Ь': '', 'ь': '',
        'Э': 'E', 'э': 'e',
        'Ю': 'Yu', 'ю': 'yu',
        'Я': 'Ya', 'я': 'ya',
    }
    
    # Handle 'ts' and 'ch' specific combinations if necessary, but letter-by-letter is fine
    res = ''.join(mapping.get(c, c) for c in text)
    
    # Replace the broken '?' with normal characters if possible
    # (Though we prefer original files, if someone passes ?, it stays ?)
    return res

def setup_database():
    print("Searching for original Excel files...")
    
    # Find any xlsx files relative to script location
    excel_files = glob.glob(os.path.join(BASE_DIR, "*.xlsx"))
    if not excel_files:
        print(f"Xatolik: Original Excel fayllari topilmadi in {BASE_DIR}!")
        print(f"Barcha fayllar: {os.listdir(BASE_DIR)}")
        return
        
    dfs = []
    for file in excel_files:
        try:
            print(f"Fayl o'qilmoqda...")
            df = pd.read_excel(file)
            
            # Identify columns
            col_mapping = {}
            for col in df.columns:
                col_str = str(col).lower()
                if 'tashkilot' in col_str or 'столбец2' in col_str: col_mapping[col] = 'name'
                elif 'inn' in col_str or 'столбец3' in col_str: col_mapping[col] = 'inn'
                elif 'telefon' in col_str: col_mapping[col] = 'phone'
                elif '№' in col_str or 'столбец1' in col_str: col_mapping[col] = 'id'
            
            df = df.rename(columns=col_mapping)
            
            # Ensure required columns exist
            if 'name' not in df.columns:
                df['name'] = "Noma'lum"
            if 'inn' not in df.columns:
                df['inn'] = "Noma'lum"
            if 'phone' not in df.columns:
                df['phone'] = "N/A"
            if 'id' not in df.columns:
                df['id'] = "0"
                
            dfs.append(df[['id', 'name', 'inn', 'phone']])
        except Exception as e:
            print(f"Xatolik yuz berdi faylda: {e}")

    if not dfs:
        print("Hech qanday ma'lumot o'qilmadi.")
        return
        
    final_df = pd.concat(dfs, ignore_index=True)
    
    # Clean and Transliterate
    final_df = final_df.dropna(subset=['name', 'inn'])
    final_df['inn'] = final_df['inn'].astype(str).str.replace(r'\.0$', '', regex=True)
    final_df['phone'] = final_df['phone'].fillna("N/A").astype(str)
    
    # TRANSLITERATE ALL NAMES TO KARAKALPAK LATIN
    final_df['name'] = final_df['name'].apply(cyrillic_to_latin)

    # Database operations
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

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

    final_df.to_sql('organizations', conn, if_exists='append', index=False)
    
    cursor.execute("CREATE INDEX idx_name ON organizations(name);")
    cursor.execute("CREATE INDEX idx_inn ON organizations(inn);")
    
    conn.commit()
    conn.close()
    
    print(f"Baza tayyor! {len(final_df)} ta tashkilot Lotin alifbosiga o'girilib joylandi.")

if __name__ == "__main__":
    setup_database()
