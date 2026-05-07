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
