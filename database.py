from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime, Boolean, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from datetime import datetime
from contextlib import contextmanager
from config import db_config

Base = declarative_base()

class Movie(Base):
    __tablename__ = 'movies'
    
    id = Column(Integer, primary_key=True)
    imdb_id = Column(String(20), unique=True, index=True, nullable=False)
    tmdb_id = Column(Integer, unique=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    overview = Column(Text)
    release_date = Column(String(20), index=True)  # Index for sorting by date
    year = Column(String(4))
    rating = Column(String(10))
    duration = Column(String(20))
    genres = Column(JSON)
    poster_path = Column(String(255))
    backdrop_path = Column(String(255))
    vote_average = Column(Float)
    vote_count = Column(Integer)
    popularity = Column(Float, index=True)  # Index for sorting by popularity
    quality = Column(String(10), default='HD')
    is_trending = Column(Boolean, default=False, index=True)  # Index for filtering trending
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Composite indexes for common query patterns
    __table_args__ = (
        Index('idx_movie_trending_popularity', 'is_trending', 'popularity'),
        Index('idx_movie_release_date', 'release_date'),
    )
    
    def to_dict(self):
        return {
            'imdb_id': self.imdb_id,
            'tmdb_id': self.tmdb_id,
            'title': self.title,
            'overview': self.overview,
            'release_date': self.release_date,
            'year': self.year,
            'rating': self.rating,
            'duration': self.duration,
            'genres': self.genres,
            'poster_url': f'/poster/movie/{self.tmdb_id}' if self.tmdb_id and self.poster_path else None,
            'backdrop_url': f'/backdrop/movie/{self.tmdb_id}' if self.tmdb_id and self.backdrop_path else None,
            'vote_average': self.vote_average,
            'popularity': self.popularity,
            'quality': self.quality,
            'is_trending': self.is_trending,
        }

class TVShow(Base):
    __tablename__ = 'tvshows'
    
    id = Column(Integer, primary_key=True)
    imdb_id = Column(String(20), unique=True, index=True, nullable=False)
    tmdb_id = Column(Integer, unique=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    overview = Column(Text)
    first_air_date = Column(String(20), index=True)  # Index for sorting by date
    year = Column(String(4))
    rating = Column(String(10))
    number_of_seasons = Column(Integer)
    genres = Column(JSON)
    poster_path = Column(String(255))
    backdrop_path = Column(String(255))
    vote_average = Column(Float)
    vote_count = Column(Integer)
    popularity = Column(Float, index=True)  # Index for sorting by popularity
    is_trending = Column(Boolean, default=False, index=True)  # Index for filtering trending
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Composite indexes for common query patterns
    __table_args__ = (
        Index('idx_tvshow_trending_popularity', 'is_trending', 'popularity'),
        Index('idx_tvshow_first_air_date', 'first_air_date'),
    )
    
    def to_dict(self):
        return {
            'imdb_id': self.imdb_id,
            'tmdb_id': self.tmdb_id,
            'title': self.title,
            'overview': self.overview,
            'first_air_date': self.first_air_date,
            'year': self.year,
            'rating': self.rating,
            'number_of_seasons': self.number_of_seasons,
            'genres': self.genres,
            'poster_url': f'/poster/tv/{self.tmdb_id}' if self.tmdb_id and self.poster_path else None,
            'backdrop_url': f'/backdrop/tv/{self.tmdb_id}' if self.tmdb_id and self.backdrop_path else None,
            'vote_average': self.vote_average,
            'popularity': self.popularity,
            'is_trending': self.is_trending,
        }

class MyList(Base):
    __tablename__ = 'my_list'
    
    id = Column(Integer, primary_key=True)
    media_type = Column(String(10), nullable=False, index=True)  # 'movie' or 'series'
    media_id = Column(String(20), nullable=False, index=True)  # imdb_id
    tmdb_id = Column(Integer)
    title = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)  # Index for sorting
    
    # Composite unique constraint to prevent duplicates
    __table_args__ = (
        Index('idx_mylist_type_id', 'media_type', 'media_id', unique=True),
    )
    
    def to_dict(self):
        # Simple dict representation without nested queries
        return {
            'type': self.media_type,
            'id': self.media_id,
            'imdb_id': self.media_id,
            'tmdb_id': self.tmdb_id,
            'title': self.title,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class WatchHistory(Base):
    """Track user's watch history and progress"""
    __tablename__ = 'watch_history'
    
    id = Column(Integer, primary_key=True)
    media_type = Column(String(10), nullable=False, index=True)  # 'movie' or 'series'
    media_id = Column(String(20), nullable=False, index=True)  # imdb_id
    tmdb_id = Column(Integer)
    title = Column(String(255), nullable=False)
    
    # Progress tracking
    progress_seconds = Column(Integer, default=0)  # Current position in seconds
    duration_seconds = Column(Integer, default=0)  # Total duration in seconds
    progress_percent = Column(Float, default=0.0)  # Progress percentage
    
    # Episode tracking (for TV shows)
    season_number = Column(Integer, nullable=True)
    episode_number = Column(Integer, nullable=True)
    
    # Metadata
    poster_path = Column(String(255))
    is_completed = Column(Boolean, default=False)  # Marked as watched if >90% complete
    last_watched = Column(DateTime, default=datetime.utcnow, index=True)  # Index for sorting
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Composite unique constraint for movies, unique per episode for series
    __table_args__ = (
        Index('idx_watch_history_lookup', 'media_type', 'media_id', 'season_number', 'episode_number', unique=True),
        Index('idx_watch_history_last_watched', 'last_watched'),
    )
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        result = {
            'type': self.media_type,
            'id': self.media_id,
            'imdb_id': self.media_id,
            'tmdb_id': self.tmdb_id,
            'title': self.title,
            'progress_seconds': self.progress_seconds,
            'duration_seconds': self.duration_seconds,
            'progress_percent': round(self.progress_percent, 2),
            'is_completed': self.is_completed,
            'last_watched': self.last_watched.isoformat() if self.last_watched else None,
            'poster_url': f'/poster/{self.media_type}/{self.tmdb_id}' if self.tmdb_id else None,
        }
        
        # Add episode info for series
        if self.media_type == 'series' and self.season_number and self.episode_number:
            result['season'] = self.season_number
            result['episode'] = self.episode_number
            result['episode_title'] = f"S{self.season_number}E{self.episode_number}"
        
        return result

class WatchedItems(Base):
    """Track items manually marked as watched by the user"""
    __tablename__ = 'watched_items'
    
    id = Column(Integer, primary_key=True)
    media_type = Column(String(10), nullable=False, index=True)  # 'movie' or 'series'
    media_id = Column(String(20), nullable=False, index=True)  # imdb_id
    tmdb_id = Column(Integer)
    title = Column(String(255), nullable=False)
    
    # Episode tracking (for TV shows)
    season_number = Column(Integer, nullable=True)
    episode_number = Column(Integer, nullable=True)
    
    # Metadata
    marked_at = Column(DateTime, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Composite unique constraint for movies, unique per episode for series
    __table_args__ = (
        Index('idx_watched_items_lookup', 'media_type', 'media_id', 'season_number', 'episode_number', unique=True),
        Index('idx_watched_items_marked_at', 'marked_at'),
    )
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        result = {
            'type': self.media_type,
            'id': self.media_id,
            'imdb_id': self.media_id,
            'tmdb_id': self.tmdb_id,
            'title': self.title,
            'marked_at': self.marked_at.isoformat() if self.marked_at else None,
            'is_watched': True
        }
        
        # Add episode info for series
        if self.media_type == 'series' and self.season_number and self.episode_number:
            result['season'] = self.season_number
            result['episode'] = self.episode_number
            result['episode_title'] = f"S{self.season_number}E{self.episode_number}"
        
        return result


# Database setup with optimized connection pooling
engine = create_engine(
    db_config.URL,
    echo=db_config.ECHO,
    poolclass=QueuePool,
    pool_size=db_config.POOL_SIZE,
    max_overflow=db_config.MAX_OVERFLOW,
    pool_recycle=db_config.POOL_RECYCLE,
    pool_pre_ping=db_config.POOL_PRE_PING,
    connect_args={'check_same_thread': False} if 'sqlite' in db_config.URL else {}
)

# Thread-safe session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
ScopedSession = scoped_session(SessionLocal)


def init_db():
    """Initialize the database with all tables and indexes"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully with optimized indexes")


def get_db():
    """
    Get database session
    Prefer using the context manager for automatic cleanup
    """
    return ScopedSession()


def close_db(db):
    """Close database session and return to pool"""
    if db:
        try:
            db.close()
        except Exception:
            pass


@contextmanager
def get_db_session():
    """
    Context manager for database sessions
    Automatically handles commits and rollbacks
    
    Usage:
        with get_db_session() as session:
            session.query(Movie).all()
    """
    session = get_db()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        close_db(session)
