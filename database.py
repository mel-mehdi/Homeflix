from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

Base = declarative_base()

class Movie(Base):
    __tablename__ = 'movies'
    
    id = Column(Integer, primary_key=True)
    imdb_id = Column(String(20), unique=True, index=True)
    tmdb_id = Column(Integer, unique=True, index=True)
    title = Column(String(255), nullable=False)
    overview = Column(Text)
    release_date = Column(String(20))
    year = Column(String(4))
    rating = Column(String(10))
    duration = Column(String(20))
    genres = Column(JSON)
    poster_path = Column(String(255))
    backdrop_path = Column(String(255))
    vote_average = Column(Float)
    vote_count = Column(Integer)
    popularity = Column(Float)
    quality = Column(String(10), default='HD')
    is_trending = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
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
    imdb_id = Column(String(20), unique=True, index=True)
    tmdb_id = Column(Integer, unique=True, index=True)
    title = Column(String(255), nullable=False)
    overview = Column(Text)
    first_air_date = Column(String(20))
    year = Column(String(4))
    rating = Column(String(10))
    number_of_seasons = Column(Integer)
    genres = Column(JSON)
    poster_path = Column(String(255))
    backdrop_path = Column(String(255))
    vote_average = Column(Float)
    vote_count = Column(Integer)
    popularity = Column(Float)
    is_trending = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
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
    media_type = Column(String(10), nullable=False)  # 'movie' or 'series'
    media_id = Column(String(20), nullable=False)  # imdb_id
    tmdb_id = Column(Integer)
    title = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
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

# Database setup
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///homeflix.db')
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize the database"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully")

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        return db
    finally:
        pass

def close_db(db):
    """Close database session"""
    if db:
        db.close()
