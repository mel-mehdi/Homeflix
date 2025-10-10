#!/usr/bin/env python3
"""
Add indexes to title columns for faster search performance
"""
import sqlite3
import os

def add_search_indexes():
    """Add indexes to movies.title and tvshows.title for faster searches"""
    db_path = 'homeflix.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 Adding search indexes to database...")
        
        # Check if indexes already exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='ix_movies_title'")
        if cursor.fetchone():
            print("✅ Index on movies.title already exists")
        else:
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_movies_title ON movies(title)")
            print("✅ Added index to movies.title")
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='ix_tvshows_title'")
        if cursor.fetchone():
            print("✅ Index on tvshows.title already exists")
        else:
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_tvshows_title ON tvshows(title)")
            print("✅ Added index to tvshows.title")
        
        conn.commit()
        conn.close()
        
        print("\n✅ Search indexes added successfully!")
        print("🚀 Your search will now be much faster!")
        
    except Exception as e:
        print(f"❌ Error adding indexes: {e}")

if __name__ == '__main__':
    add_search_indexes()
