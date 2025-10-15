from database import Movie, TVShow, get_db, close_db, MyList, WatchHistory
from sqlalchemy import text, desc
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from typing import List, Optional, Dict, Any
from utils import measure_time
import logging

logger = logging.getLogger(__name__)


class DatabaseService:
    """
    Optimized service for database operations with better error handling
    Context manager for automatic resource cleanup
    """
    
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
    
    def create_or_update_movie(self, movie_data: Dict[str, Any]) -> Movie:
        """
        Create or update a movie with upsert logic
        
        Args:
            movie_data: Dictionary containing movie data
            
        Returns:
            Movie object
        """
        try:
            movie = self.get_movie_by_imdb_id(movie_data.get('imdb_id'))
            
            if movie:
                # Update existing movie - only update if data has changed
                for key, value in movie_data.items():
                    if hasattr(movie, key) and getattr(movie, key) != value:
                        setattr(movie, key, value)
                movie.updated_at = datetime.utcnow()
            else:
                # Create new movie
                movie = Movie(**movie_data)
                self.db.add(movie)
            
            self.db.commit()
            self.db.refresh(movie)
            return movie
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"IntegrityError creating/updating movie: {e}")
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating/updating movie: {e}")
            raise
    
    def create_or_update_movies_batch(self, movies_data: List[Dict[str, Any]]) -> int:
        """
        Create or update multiple movies in batch with bulk operations
        Much faster than individual inserts
        
        Args:
            movies_data: List of movie data dictionaries
            
        Returns:
            Number of movies processed
        """
        try:
            processed_count = 0
            # Use bulk operations for better performance
            for movie_data in movies_data:
                try:
                    movie = self.get_movie_by_imdb_id(movie_data.get('imdb_id'))
                    
                    if movie:
                        # Update existing movie
                        for key, value in movie_data.items():
                            if hasattr(movie, key) and getattr(movie, key) != value:
                                setattr(movie, key, value)
                        movie.updated_at = datetime.utcnow()
                    else:
                        # Create new movie
                        movie = Movie(**movie_data)
                        self.db.add(movie)
                    processed_count += 1
                except Exception as e:
                    logger.error(f"Error processing movie {movie_data.get('imdb_id')}: {e}")
                    continue
            
            self.db.commit()
            return processed_count
        except Exception as e:
            self.db.rollback()
            logger.error(f"Batch movie operation failed: {e}")
            raise
    
    @measure_time
    def get_latest_movies(self, page: int = 1, per_page: int = 16) -> List[Dict[str, Any]]:
        """
        Get latest movies from database with pagination
        Optimized with proper indexing
        
        Args:
            page: Page number (1-indexed)
            per_page: Number of items per page
            
        Returns:
            List of movie dictionaries
        """
        offset = (page - 1) * per_page
        movies = self.db.query(Movie)\
            .filter(Movie.imdb_id.isnot(None))\
            .order_by(desc(Movie.release_date))\
            .offset(offset)\
            .limit(per_page)\
            .all()
        return [movie.to_dict() for movie in movies]
    
    def get_trending_movies(self, per_page: int = 16) -> List[Dict[str, Any]]:
        """
        Get trending movies using composite index for fast retrieval
        
        Args:
            per_page: Number of items to return
            
        Returns:
            List of trending movie dictionaries
        """
        movies = self.db.query(Movie)\
            .filter(Movie.is_trending == True, Movie.imdb_id.isnot(None))\
            .order_by(desc(Movie.popularity))\
            .limit(per_page)\
            .all()
        return [movie.to_dict() for movie in movies]
    
    @measure_time
    def search_movies(self, query: str, page: int = 1, per_page: int = 15) -> List[Dict[str, Any]]:
        """
        Search movies using FTS5 for ultra-fast full-text search
        Falls back to LIKE if FTS is not available
        
        Args:
            query: Search query string
            page: Page number (1-indexed)
            per_page: Number of results per page
            
        Returns:
            List of matching movie dictionaries
        """
        offset = (page - 1) * per_page
        
        # Use FTS5 for lightning-fast full-text search
        try:
            # Escape special FTS characters and add prefix matching
            fts_query = query.replace('"', '""').replace('*', '')
            if len(fts_query) >= 2:
                fts_query = f'"{fts_query}"*'  # Quoted prefix search
            
            # FTS5 search with prefix matching for autocomplete
            sql = text("""
                SELECT m.* FROM movies m
                INNER JOIN movies_fts fts ON m.id = fts.rowid
                WHERE movies_fts MATCH :query
                ORDER BY 
                    CASE WHEN LOWER(m.title) LIKE :starts_with THEN 0 ELSE 1 END,
                    m.popularity DESC
                LIMIT :limit OFFSET :offset
            """)
            result = self.db.execute(sql, {
                'query': fts_query,
                'starts_with': f"{query.lower()}%",
                'limit': per_page,
                'offset': offset
            })
            
            movies = []
            for row in result:
                row_dict = dict(row._mapping)
                movie = Movie(**row_dict)
                movies.append(movie.to_dict())
            return movies
        except Exception as e:
            logger.warning(f"FTS search failed, falling back to LIKE: {e}")
            # Fallback to LIKE search if FTS fails
            search_term = f"%{query}%"
            movies = self.db.query(Movie)\
                .filter(Movie.title.ilike(search_term))\
                .order_by(desc(Movie.popularity))\
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
        """Search TV shows in database using FTS for ultra-fast results"""
        offset = (page - 1) * per_page
        
        # Use FTS5 for lightning-fast full-text search
        try:
            # Escape special FTS characters and add prefix matching
            # Use * for prefix matching (e.g., "breaking*" matches "breaking bad")
            fts_query = query.replace('"', '""').replace('*', '')
            if len(fts_query) >= 2:
                fts_query = f'"{fts_query}"*'  # Quoted prefix search
            
            # FTS5 search with prefix matching for autocomplete
            sql = text("""
                SELECT t.* FROM tvshows t
                INNER JOIN tvshows_fts fts ON t.id = fts.rowid
                WHERE tvshows_fts MATCH :query
                ORDER BY 
                    CASE WHEN LOWER(t.title) LIKE :starts_with THEN 0 ELSE 1 END,
                    t.popularity DESC
                LIMIT :limit OFFSET :offset
            """)
            result = self.db.execute(sql, {
                'query': fts_query,
                'starts_with': f"{query.lower()}%",
                'limit': per_page,
                'offset': offset
            })
            
            tvshows = []
            for row in result:
                row_dict = dict(row._mapping)
                tvshow = TVShow(**row_dict)
                tvshows.append(tvshow.to_dict())
            return tvshows
        except Exception as e:
            # Fallback to LIKE search if FTS fails
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
    
    def is_in_my_list(self, media_type: str, media_id: str) -> bool:
        """Check if an item is in My List"""
        exists = self.db.query(MyList).filter(
            MyList.media_type == media_type,
            MyList.media_id == media_id
        ).first()
        return exists is not None
    
    # Watch History operations
    def get_watch_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get user's watch history sorted by last watched
        Only returns items with progress > 5% and < 95% (continue watching)
        
        Args:
            limit: Maximum number of items to return
            
        Returns:
            List of watch history dictionaries
        """
        from database import WatchHistory
        
        history = self.db.query(WatchHistory)\
            .filter(
                WatchHistory.progress_percent > 5,
                WatchHistory.progress_percent < 95
            )\
            .order_by(desc(WatchHistory.last_watched))\
            .limit(limit)\
            .all()
        
        result = []
        for item in history:
            history_dict = item.to_dict()
            
            # Enrich with media details
            if item.media_type == 'movie':
                media = self.get_movie_by_imdb_id(item.media_id)
                if media:
                    history_dict.update({
                        'poster_url': media.to_dict().get('poster_url'),
                        'backdrop_url': media.to_dict().get('backdrop_url'),
                    })
            else:  # series
                media = self.get_tvshow_by_imdb_id(item.media_id)
                if media:
                    history_dict.update({
                        'poster_url': media.to_dict().get('poster_url'),
                        'backdrop_url': media.to_dict().get('backdrop_url'),
                    })
            
            result.append(history_dict)
        
        return result
    
    def get_watch_progress(self, media_type: str, media_id: str, 
                          season: Optional[int] = None, 
                          episode: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Get watch progress for a specific item
        
        Args:
            media_type: 'movie' or 'series'
            media_id: IMDB ID
            season: Season number (for series)
            episode: Episode number (for series)
            
        Returns:
            Watch progress dictionary or None
        """
        from database import WatchHistory
        
        query = self.db.query(WatchHistory).filter(
            WatchHistory.media_type == media_type,
            WatchHistory.media_id == media_id
        )
        
        # Add episode filters for series
        if media_type == 'series' and season and episode:
            query = query.filter(
                WatchHistory.season_number == season,
                WatchHistory.episode_number == episode
            )
        
        progress = query.first()
        return progress.to_dict() if progress else None
    
    def update_watch_progress(self, media_type: str, media_id: str, 
                             progress_seconds: int, duration_seconds: int,
                             title: str, tmdb_id: Optional[int] = None,
                             season: Optional[int] = None, 
                             episode: Optional[int] = None) -> Dict[str, Any]:
        """
        Update or create watch progress
        
        Args:
            media_type: 'movie' or 'series'
            media_id: IMDB ID
            progress_seconds: Current playback position in seconds
            duration_seconds: Total duration in seconds
            title: Title of the media
            tmdb_id: TMDB ID (optional)
            season: Season number (for series)
            episode: Episode number (for series)
            
        Returns:
            Updated watch history dictionary
        """
        from database import WatchHistory
        
        # Calculate progress percentage
        progress_percent = (progress_seconds / duration_seconds * 100) if duration_seconds > 0 else 0
        is_completed = progress_percent > 90
        
        # Find existing record
        query = self.db.query(WatchHistory).filter(
            WatchHistory.media_type == media_type,
            WatchHistory.media_id == media_id
        )
        
        # Add episode filters for series
        if media_type == 'series' and season and episode:
            query = query.filter(
                WatchHistory.season_number == season,
                WatchHistory.episode_number == episode
            )
        
        watch_record = query.first()
        
        if watch_record:
            # Update existing record
            watch_record.progress_seconds = progress_seconds
            watch_record.duration_seconds = duration_seconds
            watch_record.progress_percent = progress_percent
            watch_record.is_completed = is_completed
            watch_record.last_watched = datetime.utcnow()
            watch_record.updated_at = datetime.utcnow()
        else:
            # Create new record
            watch_record = WatchHistory(
                media_type=media_type,
                media_id=media_id,
                tmdb_id=tmdb_id,
                title=title,
                progress_seconds=progress_seconds,
                duration_seconds=duration_seconds,
                progress_percent=progress_percent,
                season_number=season,
                episode_number=episode,
                is_completed=is_completed
            )
            self.db.add(watch_record)
        
        self.db.commit()
        self.db.refresh(watch_record)
        return watch_record.to_dict()
    
    def clear_watch_progress(self, media_type: str, media_id: str,
                           season: Optional[int] = None, 
                           episode: Optional[int] = None) -> bool:
        """
        Clear watch progress for an item
        
        Args:
            media_type: 'movie' or 'series'
            media_id: IMDB ID
            season: Season number (for series)
            episode: Episode number (for series)
            
        Returns:
            True if deleted, False if not found
        """
        from database import WatchHistory
        
        query = self.db.query(WatchHistory).filter(
            WatchHistory.media_type == media_type,
            WatchHistory.media_id == media_id
        )
        
        if media_type == 'series' and season and episode:
            query = query.filter(
                WatchHistory.season_number == season,
                WatchHistory.episode_number == episode
            )
        
        watch_record = query.first()
        if watch_record:
            self.db.delete(watch_record)
            self.db.commit()
            return True
        return False
    
    def get_completed_items(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get completed watch history (>90% watched)
        
        Args:
            limit: Maximum number of items to return
            
        Returns:
            List of completed watch history items
        """
        from database import WatchHistory
        
        completed = self.db.query(WatchHistory)\
            .filter(WatchHistory.is_completed == True)\
            .order_by(desc(WatchHistory.last_watched))\
            .limit(limit)\
            .all()
        
        return [item.to_dict() for item in completed]
    
    # Watch Mark operations (manually mark as watched)
    def mark_as_watched(self, media_type: str, media_id: str, tmdb_id: Optional[int] = None,
                       title: str = "Unknown", season: Optional[int] = None, 
                       episode: Optional[int] = None) -> bool:
        """
        Mark an item as watched manually
        
        Args:
            media_type: 'movie' or 'series'
            media_id: IMDB ID
            tmdb_id: TMDB ID (optional)
            title: Title of the media
            season: Season number (for series)
            episode: Episode number (for series)
            
        Returns:
            True if marked successfully
        """
        from database import WatchedItems
        
        try:
            # Check if already marked
            query = self.db.query(WatchedItems).filter(
                WatchedItems.media_type == media_type,
                WatchedItems.media_id == media_id
            )
            
            if media_type == 'series' and season and episode:
                query = query.filter(
                    WatchedItems.season_number == season,
                    WatchedItems.episode_number == episode
                )
            
            existing = query.first()
            
            if existing:
                # Update timestamp
                existing.marked_at = datetime.utcnow()
                self.db.commit()
                return True
            
            # Create new watched mark
            watched_item = WatchedItems(
                media_type=media_type,
                media_id=media_id,
                tmdb_id=tmdb_id,
                title=title,
                season_number=season,
                episode_number=episode
            )
            self.db.add(watched_item)
            self.db.commit()
            return True
        except IntegrityError:
            self.db.rollback()
            # Already exists, just update it
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error marking as watched: {e}")
            return False
    
    def unmark_as_watched(self, media_type: str, media_id: str,
                         season: Optional[int] = None, 
                         episode: Optional[int] = None) -> bool:
        """
        Remove watched mark from an item
        
        Args:
            media_type: 'movie' or 'series'
            media_id: IMDB ID
            season: Season number (for series)
            episode: Episode number (for series)
            
        Returns:
            True if unmarked successfully
        """
        from database import WatchedItems
        
        try:
            query = self.db.query(WatchedItems).filter(
                WatchedItems.media_type == media_type,
                WatchedItems.media_id == media_id
            )
            
            if media_type == 'series' and season and episode:
                query = query.filter(
                    WatchedItems.season_number == season,
                    WatchedItems.episode_number == episode
                )
            
            watched_item = query.first()
            
            if watched_item:
                self.db.delete(watched_item)
                self.db.commit()
                return True
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error unmarking as watched: {e}")
            return False
    
    def is_marked_watched(self, media_type: str, media_id: str,
                         season: Optional[int] = None, 
                         episode: Optional[int] = None) -> bool:
        """
        Check if an item is marked as watched
        
        Args:
            media_type: 'movie' or 'series'
            media_id: IMDB ID
            season: Season number (for series)
            episode: Episode number (for series)
            
        Returns:
            True if marked as watched
        """
        from database import WatchedItems
        
        query = self.db.query(WatchedItems).filter(
            WatchedItems.media_type == media_type,
            WatchedItems.media_id == media_id
        )
        
        if media_type == 'series' and season and episode:
            query = query.filter(
                WatchedItems.season_number == season,
                WatchedItems.episode_number == episode
            )
        
        return query.first() is not None
    
    def get_watched_items(self, media_type: Optional[str] = None, 
                         limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all items marked as watched
        
        Args:
            media_type: Filter by 'movie' or 'series' (optional)
            limit: Maximum number of items to return
            
        Returns:
            List of watched items
        """
        from database import WatchedItems
        
        query = self.db.query(WatchedItems)
        
        if media_type:
            query = query.filter(WatchedItems.media_type == media_type)
        
        watched = query.order_by(desc(WatchedItems.marked_at)).limit(limit).all()
        
        result = []
        for item in watched:
            watched_dict = item.to_dict()
            
            # Enrich with media details
            if item.media_type == 'movie':
                media = self.get_movie_by_imdb_id(item.media_id)
                if media:
                    watched_dict.update({
                        'poster_url': media.to_dict().get('poster_url'),
                        'backdrop_url': media.to_dict().get('backdrop_url'),
                    })
            else:  # series
                media = self.get_tvshow_by_imdb_id(item.media_id)
                if media:
                    watched_dict.update({
                        'poster_url': media.to_dict().get('poster_url'),
                        'backdrop_url': media.to_dict().get('backdrop_url'),
                    })
            
            result.append(watched_dict)
        
        return result
    
    def save_watch_progress(self, media_type: str, media_id: str, 
                           progress_seconds: int, duration_seconds: int,
                           title: str, tmdb_id: Optional[int] = None,
                           season_number: Optional[int] = None, 
                           episode_number: Optional[int] = None,
                           poster_path: Optional[str] = None) -> 'WatchHistory':
        """
        Save or update watch progress for continue watching feature
        
        Args:
            media_type: 'movie' or 'series'
            media_id: IMDB ID
            progress_seconds: Current playback position in seconds
            duration_seconds: Total duration in seconds
            title: Title of the media
            tmdb_id: TMDB ID (optional)
            season_number: Season number (for series)
            episode_number: Episode number (for series)
            poster_path: Poster path (optional)
            
        Returns:
            WatchHistory object
        """
        from database import WatchHistory
        
        try:
            # Calculate progress percentage
            progress_percent = (progress_seconds / duration_seconds * 100) if duration_seconds > 0 else 0
            is_completed = progress_percent >= 90
            
            # Find existing record
            query = self.db.query(WatchHistory).filter(
                WatchHistory.media_type == media_type,
                WatchHistory.media_id == media_id
            )
            
            # Add episode filters for series
            if media_type == 'series' and season_number and episode_number:
                query = query.filter(
                    WatchHistory.season_number == season_number,
                    WatchHistory.episode_number == episode_number
                )
            
            watch_record = query.first()
            
            if watch_record:
                # Update existing record
                watch_record.progress_seconds = progress_seconds
                watch_record.duration_seconds = duration_seconds
                watch_record.progress_percent = progress_percent
                watch_record.is_completed = is_completed
                watch_record.last_watched = datetime.utcnow()
                watch_record.updated_at = datetime.utcnow()
                if poster_path:
                    watch_record.poster_path = poster_path
            else:
                # Create new record
                watch_record = WatchHistory(
                    media_type=media_type,
                    media_id=media_id,
                    tmdb_id=tmdb_id,
                    title=title,
                    progress_seconds=progress_seconds,
                    duration_seconds=duration_seconds,
                    progress_percent=progress_percent,
                    season_number=season_number,
                    episode_number=episode_number,
                    poster_path=poster_path,
                    is_completed=is_completed
                )
                self.db.add(watch_record)
            
            self.db.commit()
            self.db.refresh(watch_record)
            
            # If completed and progress > 90%, also mark as watched
            if is_completed:
                self.mark_as_watched(
                    media_type=media_type,
                    media_id=media_id,
                    tmdb_id=tmdb_id,
                    title=title,
                    season=season_number,
                    episode=episode_number
                )
            
            return watch_record
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error saving watch progress: {e}")
            raise
    
    def get_continue_watching(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get continue watching items (5% - 90% progress)
        
        Args:
            limit: Maximum number of items to return
            
        Returns:
            List of continue watching items with enriched data
        """
        from database import WatchHistory
        
        continue_watching = self.db.query(WatchHistory)\
            .filter(
                WatchHistory.progress_percent >= 5,
                WatchHistory.progress_percent < 90,
                WatchHistory.is_completed == False
            )\
            .order_by(desc(WatchHistory.last_watched))\
            .limit(limit)\
            .all()
        
        result = []
        for item in continue_watching:
            history_dict = item.to_dict()
            
            # Enrich with media details
            if item.media_type == 'movie':
                media = self.get_movie_by_imdb_id(item.media_id)
                if media:
                    media_dict = media.to_dict()
                    history_dict.update({
                        'poster_url': media_dict.get('poster_url'),
                        'backdrop_url': media_dict.get('backdrop_url'),
                        'overview': media_dict.get('overview'),
                    })
            else:  # series
                media = self.get_tvshow_by_imdb_id(item.media_id)
                if media:
                    media_dict = media.to_dict()
                    history_dict.update({
                        'poster_url': media_dict.get('poster_url'),
                        'backdrop_url': media_dict.get('backdrop_url'),
                        'overview': media_dict.get('overview'),
                    })
            
            result.append(history_dict)
        
        return result
    
    def remove_from_watch_history(self, media_type: str, media_id: str,
                                 season_number: Optional[int] = None, 
                                 episode_number: Optional[int] = None) -> bool:
        """
        Remove item from watch history
        
        Args:
            media_type: 'movie' or 'series'
            media_id: IMDB ID
            season_number: Season number (for series)
            episode_number: Episode number (for series)
            
        Returns:
            True if removed successfully
        """
        return self.clear_watch_progress(media_type, media_id, season_number, episode_number)
