import sqlite3
from config import DB_PATH

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

from thefuzz import fuzz
from thefuzz import process

def normalize_text(text: str) -> str:
    text = text.lower()
    mapping = {
        "o'": "o", "g'": "g", "ı": "i", "n'": "n", "q": "k",
        "ў": "o", "ғ": "g", "қ": "k", "ҳ": "h"
    }
    for k, v in mapping.items():
        text = text.replace(k, v)
    return text

def search_organizations(query: str, limit: int = 10):
    """
    Search for organizations by ID, INN, or partial Name.
    Returns a list of dictionary-like objects.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    query_clean = query.strip()
    
    # Eger 9 xanalı san bolsa, bul INN bolıwı múmkin
    if query_clean.isdigit() and len(query_clean) == 9:
        cursor.execute(
            "SELECT * FROM organizations WHERE inn = ? LIMIT ?",
            (query_clean, limit)
        )
        results = cursor.fetchall()
        
        # Eger INN boyınsha tabılsa, birden qaytaramız
        if results:
            conn.close()
            ret = []
            for row in results:
                d = dict(row)
                d['similarity'] = 100
                ret.append(d)
            return ret
    
    # Fuzzy Search for text
    cursor.execute("SELECT * FROM organizations")
    all_rows = cursor.fetchall()
    conn.close()

    if not all_rows:
        return []
        
    LAYOUT_CYR_TO_LATIN = str.maketrans(
        "йцукенгшщзхъфывапролджэячсмитьбюЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮ",
        "qwertyuiop[]asdfghjkl;'zxcvbnm,.QWERTYUIOP[]ASDFGHJKL;'ZXCVBNM,."
    )
    
    def transliterate_cyr_to_lat(text: str) -> str:
        mapping = {
            'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo', 'ж': 'j', 'з': 'z',
            'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r',
            'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'x', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sh',
            'ъ': '', 'ы': 'i', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
            'қ': 'q', 'ғ': "g'", 'ҳ': 'h', 'ў': "o'",
            'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'Yo', 'Ж': 'J', 'З': 'Z',
            'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M', 'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R',
            'С': 'S', 'Т': 'T', 'У': 'U', 'Ф': 'F', 'Х': 'X', 'Ц': 'Ts', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Sh',
            'Ъ': '', 'Ы': 'I', 'Ь': '', 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya',
            'Қ': 'Q', 'Ғ': "G'", 'Ҳ': 'H', 'Ў': "O'"
        }
        return "".join(mapping.get(c, c) for c in text)

    # Map row index to its normalized name
    choices = {i: normalize_text(row['name']) for i, row in enumerate(all_rows)}
    
    queries_to_test = [normalize_text(query_clean)]
    
    has_cyrillic = any('\u0400' <= c <= '\u04FF' or '\u0500' <= c <= '\u052F' for c in query_clean)
    
    if has_cyrillic:
        # Layout fallback ("еуя" -> "tez")
        q_layout = normalize_text(query_clean.translate(LAYOUT_CYR_TO_LATIN))
        if q_layout not in queries_to_test:
            queries_to_test.append(q_layout)
            
        # Transliteration ("тез" -> "tez")
        q_translit = normalize_text(transliterate_cyr_to_lat(query_clean))
        if q_translit not in queries_to_test:
            queries_to_test.append(q_translit)

    best_results = {}
    
    for q in queries_to_test:
        best_matches = process.extract(
            q,
            choices,
            limit=limit,
            scorer=fuzz.partial_ratio
        )
        for match_str, score, idx in best_matches:
            if score >= 60:
                if idx not in best_results or score > best_results[idx]:
                    best_results[idx] = score
                    
    # Sort best_results by score descending
    sorted_results = sorted(best_results.items(), key=lambda x: x[1], reverse=True)
    
    results = []
    for idx, score in sorted_results[:limit]:
        d = dict(all_rows[idx])
        d['similarity'] = score
        results.append(d)
            
    return results


# --- Phone Numbers ---

def init_phone_table():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS phone_numbers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            org_id TEXT NOT NULL,
            phone_name TEXT NOT NULL,
            phone_number TEXT NOT NULL,
            FOREIGN KEY (org_id) REFERENCES organizations(id)
        )
    """)
    conn.commit()
    conn.close()


def get_org_by_id(org_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM organizations WHERE id = ?", (org_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_phones_by_org(org_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM phone_numbers WHERE org_id = ? ORDER BY id",
        (org_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_phone(org_id: str, phone_name: str, phone_number: str) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO phone_numbers (org_id, phone_name, phone_number) VALUES (?, ?, ?)",
        (org_id, phone_name, phone_number)
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id


def update_phone(phone_id: int, phone_name: str, phone_number: str):
    conn = get_connection()
    conn.execute(
        "UPDATE phone_numbers SET phone_name = ?, phone_number = ? WHERE id = ?",
        (phone_name, phone_number, phone_id)
    )
    conn.commit()
    conn.close()


def delete_phone(phone_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM phone_numbers WHERE id = ?", (phone_id,))
    conn.commit()
    conn.close()


def get_phone_by_id(phone_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM phone_numbers WHERE id = ?", (phone_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


# --- Organization CRUD ---

def get_next_org_id() -> str:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(CAST(id AS INTEGER)) FROM organizations")
    row = cursor.fetchone()
    conn.close()
    max_id = row[0] if row[0] else 0
    return str(max_id + 1)


def add_organization(name: str, inn: str) -> str:
    conn = get_connection()
    cursor = conn.cursor()
    new_id = get_next_org_id()
    cursor.execute(
        "INSERT INTO organizations (id, name, inn, phone) VALUES (?, ?, ?, ?)",
        (new_id, name, inn, "N/A")
    )
    conn.commit()
    conn.close()
    return new_id


def update_organization(org_id: str, name: str, inn: str):
    conn = get_connection()
    conn.execute(
        "UPDATE organizations SET name = ?, inn = ? WHERE id = ?",
        (name, inn, org_id)
    )
    conn.commit()
    conn.close()


def delete_organization(org_id: str):
    conn = get_connection()
    conn.execute("DELETE FROM phone_numbers WHERE org_id = ?", (org_id,))
    conn.execute("DELETE FROM organizations WHERE id = ?", (org_id,))
    conn.commit()
    conn.close()
