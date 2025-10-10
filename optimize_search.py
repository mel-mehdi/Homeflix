#!/usr/bin/env python3
"""
Create full-text search (FTS) virtual tables for ultra-fast search
"""
import sqlite3
import os

def create_fts_tables():
    """Create FTS5 virtual tables for movies and tvshows"""
    db_path = 'homeflix.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 Creating Full-Text Search (FTS) tables...")
        
        # Drop existing FTS tables if they exist
        cursor.execute("DROP TABLE IF EXISTS movies_fts")
        cursor.execute("DROP TABLE IF EXISTS tvshows_fts")
        
        # Create FTS5 virtual table for movies
        cursor.execute("""
            CREATE VIRTUAL TABLE movies_fts USING fts5(
                imdb_id UNINDEXED,
                tmdb_id UNINDEXED,
                title,
                content=movies,
                content_rowid=id
            )
        """)
        print("✅ Created FTS table for movies")
        
        # Create FTS5 virtual table for tvshows
        cursor.execute("""
            CREATE VIRTUAL TABLE tvshows_fts USING fts5(
                imdb_id UNINDEXED,
                tmdb_id UNINDEXED,
                title,
                content=tvshows,
                content_rowid=id
            )
        """)
        print("✅ Created FTS table for tvshows")
        
        # Populate FTS tables with existing data
        print("📊 Populating FTS tables with existing data...")
        
        cursor.execute("""
            INSERT INTO movies_fts(rowid, imdb_id, tmdb_id, title)
            SELECT id, imdb_id, tmdb_id, title FROM movies
        """)
        movies_count = cursor.rowcount
        print(f"✅ Indexed {movies_count} movies")
        
        cursor.execute("""
            INSERT INTO tvshows_fts(rowid, imdb_id, tmdb_id, title)
            SELECT id, imdb_id, tmdb_id, title FROM tvshows
        """)
        tvshows_count = cursor.rowcount
        print(f"✅ Indexed {tvshows_count} TV shows")
        
        # Create triggers to keep FTS tables in sync
        print("🔗 Creating triggers to keep FTS tables synchronized...")
        
        # Triggers for movies
        cursor.execute("""
            CREATE TRIGGER movies_fts_insert AFTER INSERT ON movies BEGIN
                INSERT INTO movies_fts(rowid, imdb_id, tmdb_id, title)
                VALUES (new.id, new.imdb_id, new.tmdb_id, new.title);
            END
        """)
        
        cursor.execute("""
            CREATE TRIGGER movies_fts_delete AFTER DELETE ON movies BEGIN
                DELETE FROM movies_fts WHERE rowid = old.id;
            END
        """)
        
        cursor.execute("""
            CREATE TRIGGER movies_fts_update AFTER UPDATE ON movies BEGIN
                DELETE FROM movies_fts WHERE rowid = old.id;
                INSERT INTO movies_fts(rowid, imdb_id, tmdb_id, title)
                VALUES (new.id, new.imdb_id, new.tmdb_id, new.title);
            END
        """)
        
        # Triggers for tvshows
        cursor.execute("""
            CREATE TRIGGER tvshows_fts_insert AFTER INSERT ON tvshows BEGIN
                INSERT INTO tvshows_fts(rowid, imdb_id, tmdb_id, title)
                VALUES (new.id, new.imdb_id, new.tmdb_id, new.title);
            END
        """)
        
        cursor.execute("""
            CREATE TRIGGER tvshows_fts_delete AFTER DELETE ON tvshows BEGIN
                DELETE FROM tvshows_fts WHERE rowid = old.id;
            END
        """)
        
        cursor.execute("""
            CREATE TRIGGER tvshows_fts_update AFTER UPDATE ON tvshows BEGIN
                DELETE FROM tvshows_fts WHERE rowid = old.id;
                INSERT INTO tvshows_fts(rowid, imdb_id, tmdb_id, title)
                VALUES (new.id, new.imdb_id, new.tmdb_id, new.title);
            END
        """)
        
        print("✅ Created synchronization triggers")
        
        conn.commit()
        conn.close()
        
        print("\n✅ Full-Text Search optimization complete!")
        print("🚀 Search will now be BLAZING FAST! ⚡")
        
    except Exception as e:
        print(f"❌ Error creating FTS tables: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    create_fts_tables()
