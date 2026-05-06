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
    
    # Check if query is fully numeric
    if query.strip().isdigit():
        # Search by ID or INN
        cursor.execute(
            "SELECT * FROM organizations WHERE id = ? OR inn = ? LIMIT ?",
            (query.strip(), query.strip(), limit)
        )
        results = cursor.fetchall()
        
        # If found by exact number, return immediately
        if results:
            conn.close()
            return [dict(row) for row in results]
    
    # Fuzzy Search for text
    cursor.execute("SELECT * FROM organizations")
    all_rows = cursor.fetchall()
    conn.close()

    if not all_rows:
        return []

    query_norm = normalize_text(query.strip())
    
    # Map row index to its normalized name
    choices = {i: normalize_text(row['name']) for i, row in enumerate(all_rows)}
    
    # Get matches using partial_ratio
    best_matches = process.extract(
        query_norm,
        choices,
        limit=limit,
        scorer=fuzz.partial_ratio
    )
    
    results = []
    for match_str, score, idx in best_matches:
        # 60 is a good threshold for partial matches with typos
        if score >= 60:
            results.append(dict(all_rows[idx]))
            
    return results
