from database import Movie, TVShow, get_db, close_db, init_db, MyList
from sqlalchemy import or_, and_, func
from datetime import datetime, timedelta
import requests
import time

class DatabaseService:
    """Service for database operations"""
    
    def __init__(self):
        self.db = get_db()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        close_db(self.db)
    
    # Movie operations
    def get_movie_by_imdb_id(self, imdb_id):
        """Get movie by IMDB ID"""
        return self.db.query(Movie).filter(Movie.imdb_id == imdb_id).first()
    
    def get_movie_by_tmdb_id(self, tmdb_id):
        """Get movie by TMDB ID"""
        return self.db.query(Movie).filter(Movie.tmdb_id == tmdb_id).first()
    
    def create_or_update_movie(self, movie_data):
        """Create or update a movie"""
        movie = self.get_movie_by_imdb_id(movie_data.get('imdb_id'))
        
        if movie:
            # Update existing movie
            for key, value in movie_data.items():
                if hasattr(movie, key):
                    setattr(movie, key, value)
            movie.updated_at = datetime.utcnow()
        else:
            # Create new movie
            movie = Movie(**movie_data)
            self.db.add(movie)
        
        self.db.commit()
        self.db.refresh(movie)
        return movie
    
    def create_or_update_movies_batch(self, movies_data):
        """Create or update multiple movies in batch"""
        for movie_data in movies_data:
            movie = self.get_movie_by_imdb_id(movie_data.get('imdb_id'))
            
            if movie:
                # Update existing movie
                for key, value in movie_data.items():
                    if hasattr(movie, key):
                        setattr(movie, key, value)
                movie.updated_at = datetime.utcnow()
            else:
                # Create new movie
                movie = Movie(**movie_data)
                self.db.add(movie)
        
        self.db.commit()
        return len(movies_data)
    
    def get_latest_movies(self, page=1, per_page=16):
        """Get latest movies from database"""
        offset = (page - 1) * per_page
        movies = self.db.query(Movie)\
            .order_by(Movie.release_date.desc())\
            .offset(offset)\
            .limit(per_page)\
            .all()
        return [movie.to_dict() for movie in movies]
    
    def get_trending_movies(self, per_page=16):
        """Get trending movies from database"""
        movies = self.db.query(Movie)\
            .filter(Movie.is_trending == True, Movie.imdb_id.isnot(None))\
            .order_by(Movie.popularity.desc())\
            .limit(per_page)\
            .all()
        return [movie.to_dict() for movie in movies]
    
    def search_movies(self, query, page=1, per_page=15):
        """Search movies in database"""
        offset = (page - 1) * per_page
        search_term = f"%{query}%"
        movies = self.db.query(Movie)\
            .filter(Movie.title.ilike(search_term))\
            .order_by(Movie.popularity.desc())\
            .offset(offset)\
            .limit(per_page)\
            .all()
        return [movie.to_dict() for movie in movies]
    
    # TV Show operations
    def get_tvshow_by_imdb_id(self, imdb_id):
        """Get TV show by IMDB ID"""
        return self.db.query(TVShow).filter(TVShow.imdb_id == imdb_id).first()
    
    def get_tvshow_by_tmdb_id(self, tmdb_id):
        """Get TV show by TMDB ID"""
        return self.db.query(TVShow).filter(TVShow.tmdb_id == tmdb_id).first()
    
    def create_or_update_tvshow(self, tvshow_data):
        """Create or update a TV show"""
        tvshow = self.get_tvshow_by_imdb_id(tvshow_data.get('imdb_id'))
        
        if tvshow:
            # Update existing TV show
            for key, value in tvshow_data.items():
                if hasattr(tvshow, key):
                    setattr(tvshow, key, value)
            tvshow.updated_at = datetime.utcnow()
        else:
            # Create new TV show
            tvshow = TVShow(**tvshow_data)
            self.db.add(tvshow)
        
        self.db.commit()
        self.db.refresh(tvshow)
        return tvshow
    
    def create_or_update_tvshows_batch(self, tvshows_data):
        """Create or update multiple TV shows in batch"""
        for tvshow_data in tvshows_data:
            tvshow = self.get_tvshow_by_imdb_id(tvshow_data.get('imdb_id'))
            
            if tvshow:
                # Update existing TV show
                for key, value in tvshow_data.items():
                    if hasattr(tvshow, key):
                        setattr(tvshow, key, value)
                tvshow.updated_at = datetime.utcnow()
            else:
                # Create new TV show
                tvshow = TVShow(**tvshow_data)
                self.db.add(tvshow)
        
        self.db.commit()
        return len(tvshows_data)
    
    def get_latest_tvshows(self, page=1, per_page=16):
        """Get latest TV shows from database"""
        offset = (page - 1) * per_page
        tvshows = self.db.query(TVShow)\
            .order_by(TVShow.first_air_date.desc())\
            .offset(offset)\
            .limit(per_page)\
            .all()
        return [tvshow.to_dict() for tvshow in tvshows]
    
    def get_trending_tvshows(self, per_page=16):
        """Get trending TV shows from database"""
        tvshows = self.db.query(TVShow)\
            .filter(TVShow.is_trending == True, TVShow.imdb_id.isnot(None))\
            .order_by(TVShow.popularity.desc())\
            .limit(per_page)\
            .all()
        return [tvshow.to_dict() for tvshow in tvshows]
    
    def search_tvshows(self, query, page=1, per_page=15):
        """Search TV shows in database"""
        offset = (page - 1) * per_page
        search_term = f"%{query}%"
        tvshows = self.db.query(TVShow)\
            .filter(TVShow.title.ilike(search_term))\
            .order_by(TVShow.popularity.desc())\
            .offset(offset)\
            .limit(per_page)\
            .all()
        return [tvshow.to_dict() for tvshow in tvshows]
    
    def get_total_movies(self):
        """Get total number of movies"""
        return self.db.query(Movie).count()
    
    def get_total_tvshows(self):
        """Get total number of TV shows"""
        return self.db.query(TVShow).count()
    
    def movie_exists(self, imdb_id):
        """Check if a movie exists in the database"""
        return self.db.query(Movie).filter(Movie.imdb_id == imdb_id).first() is not None
    
    def tvshow_exists(self, imdb_id):
        """Check if a TV show exists in the database"""
        return self.db.query(TVShow).filter(TVShow.imdb_id == imdb_id).first() is not None
    
    def clear_trending_flags(self, media_type='all'):
        """Clear trending flags for media"""
        if media_type in ['movie', 'all']:
            self.db.query(Movie).update({Movie.is_trending: False})
        if media_type in ['tv', 'all']:
            self.db.query(TVShow).update({TVShow.is_trending: False})
        self.db.commit()
    
    # My List operations
    def get_my_list(self):
        """Get all items in My List"""
        items = self.db.query(MyList).order_by(MyList.created_at.desc()).all()
        result = []
        
        for item in items:
            # Get the actual movie or TV show data
            if item.media_type == 'movie':
                media_item = self.get_movie_by_imdb_id(item.media_id)
            else:  # 'series'
                media_item = self.get_tvshow_by_imdb_id(item.media_id)
            
            if media_item:
                # Get the full item data
                item_dict = media_item.to_dict()
                item_dict['type'] = item.media_type
                item_dict['id'] = media_item.imdb_id  # Use imdb_id as id for frontend compatibility
                result.append(item_dict)
            else:
                # Fallback if item not found in database - skip it
                pass
        
        return result
    
    def add_to_my_list(self, media_type, media_id, tmdb_id, title):
        """Add an item to My List"""
        # Check if already in list
        existing = self.db.query(MyList).filter(
            MyList.media_type == media_type,
            MyList.media_id == media_id
        ).first()
        
        if existing:
            return existing, False  # Already exists
        
        # Create new entry
        new_item = MyList(
            media_type=media_type,
            media_id=media_id,
            tmdb_id=tmdb_id,
            title=title
        )
        self.db.add(new_item)
        self.db.commit()
        self.db.refresh(new_item)
        return new_item, True  # Newly added
    
    def remove_from_my_list(self, media_type, media_id):
        """Remove an item from My List"""
        item = self.db.query(MyList).filter(
            MyList.media_type == media_type,
            MyList.media_id == media_id
        ).first()
        
        if item:
            self.db.delete(item)
            self.db.commit()
            return True
        return False
    
    def is_in_my_list(self, media_type, media_id):
        """Check if an item is in My List"""
        exists = self.db.query(MyList).filter(
            MyList.media_type == media_type,
            MyList.media_id == media_id
        ).first()
        return exists is not None
