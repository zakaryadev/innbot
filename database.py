import sqlite3
from config import DB_PATH

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

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
    
    # If not fully numeric or no results found, search by partial name
    # SQLite LIKE is case-insensitive for ASCII, but we can also use LOWER for safety if needed, 
    # though standard LIKE works well enough.
    cursor.execute(
        "SELECT * FROM organizations WHERE name LIKE ? LIMIT ?",
        (f"%{query.strip()}%", limit)
    )
    results = cursor.fetchall()
    
    conn.close()
    return [dict(row) for row in results]
