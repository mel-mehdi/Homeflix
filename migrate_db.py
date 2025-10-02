"""Database migration script to add number_of_seasons column"""
import sqlite3
import os

DATABASE_PATH = 'homeflix.db'

def migrate():
    """Add number_of_seasons column to tvshows table"""
    if not os.path.exists(DATABASE_PATH):
        print(f"❌ Database {DATABASE_PATH} not found!")
        return
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(tvshows)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'number_of_seasons' in columns:
            print("✅ Column 'number_of_seasons' already exists in tvshows table")
        else:
            # Add the column
            cursor.execute("ALTER TABLE tvshows ADD COLUMN number_of_seasons INTEGER")
            conn.commit()
            print("✅ Successfully added 'number_of_seasons' column to tvshows table")
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    print("🔄 Starting database migration...")
    migrate()
    print("✅ Migration complete!")
