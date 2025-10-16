"""
Configuration module for centralized settings management
Environment variables and constants in one place
"""
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class CacheConfig:
    """Cache duration settings in seconds"""
    TMDB_DATA: int = 3600  # 1 hour
    VIDSRC_DATA: int = 600  # 10 minutes
    POSTER: int = 7200  # 2 hours
    BACKDROP: int = 7200  # 2 hours
    SEARCH_RESULTS: int = 300  # 5 minutes


@dataclass
class APIConfig:
    """API configuration"""
    TMDB_ACCESS_TOKEN: str = os.getenv(
        'TMDB_ACCESS_TOKEN',
        'eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI2YjUyNzU0MWNmODJlNjdhMmJhOGRmZTFmYjZiMDkwYyIsIm5iZiI6MTc1OTA3NDM4Mi44MDMsInN1YiI6IjY4ZDk1ODRlYWQzMTdmMmI2MWJiMDkxYSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.HnNxWDnTZIwhVWbXH8gpVfY1n6v0pse5z2A-KUSyI5I'
    )
    TMDB_BASE_URL: str = 'https://api.themoviedb.org/3'
    TMDB_IMAGE_BASE_URL: str = 'https://image.tmdb.org/t/p/w500'
    TMDB_BACKDROP_BASE_URL: str = 'https://image.tmdb.org/t/p/w1280'
    
    # Request timeout in seconds
    REQUEST_TIMEOUT: int = 10
    
    # Max retries for failed requests
    MAX_RETRIES: int = 3


@dataclass
class DatabaseConfig:
    """Database configuration"""
    URL: str = os.getenv('DATABASE_URL', 'sqlite:///homeflix.db')
    ECHO: bool = os.getenv('DB_ECHO', 'false').lower() == 'true'
    POOL_SIZE: int = int(os.getenv('DB_POOL_SIZE', '10'))
    MAX_OVERFLOW: int = int(os.getenv('DB_MAX_OVERFLOW', '20'))
    POOL_RECYCLE: int = 3600  # Recycle connections after 1 hour
    POOL_PRE_PING: bool = True  # Check connection health before using


@dataclass
class ServerConfig:
    """Flask server configuration"""
    HOST: str = os.getenv('FLASK_HOST', '0.0.0.0')
    PORT: int = int(os.getenv('FLASK_PORT', '5000'))
    DEBUG: bool = os.getenv('FLASK_ENV', 'production') == 'development'
    THREADED: bool = True
    
    # Static folder paths
    CSS_FOLDER: str = 'css'
    STATIC_FOLDER: str = 'static'
    TEMPLATE_FOLDER: str = 'templates'


@dataclass
class PaginationConfig:
    """Pagination settings"""
    DEFAULT_PER_PAGE: int = 16
    SEARCH_PER_PAGE: int = 15
    MAX_PER_PAGE: int = 50
    TRENDING_LIMIT: int = 16


# Global config instances
cache_config = CacheConfig()
api_config = APIConfig()
db_config = DatabaseConfig()
server_config = ServerConfig()
pagination_config = PaginationConfig()


def get_embed_sources(media_type: str, identifier: str, season: Optional[int] = None, episode: Optional[int] = None) -> list[str]:
    """
    Generate embed source URLs for video players
    
    Args:
        media_type: 'movie', 'tv', or 'episode'
        identifier: TMDB ID or IMDB ID
        season: Season number (for episodes)
        episode: Episode number (for episodes)
    
    Returns:
        List of embed source URLs in priority order
    """
    if media_type == 'movie':
        return [
            f"https://vidfast.pro/movie/{identifier}?autoPlay=true&sub=ar",
            f"https://vidsrc.to/embed/movie/{identifier}",
            f"https://vidsrc.xyz/embed/movie?tmdb={identifier}",
            f"https://vidsrc.pro/embed/movie/{identifier}",
            f"https://www.2embed.cc/embed/{identifier}",
            f"https://multiembed.mov/?video_id={identifier}&tmdb=1",
            f"https://autoembed.co/movie/tmdb/{identifier}",
        ]
    elif media_type == 'tv':
        return [
            f"https://vidfast.pro/tv/{identifier}?sub=ar",
            f"https://vidsrc.me/embed/tv?tmdb={identifier}",
            f"https://vidsrc.xyz/embed/tv?tmdb={identifier}",
            f"https://vidsrc.pro/embed/tv/{identifier}",
            f"https://www.2embed.cc/embedtv/{identifier}",
            f"https://vidsrc.to/embed/tv/{identifier}",
        ]
    elif media_type == 'episode' and season is not None and episode is not None:
        return [
            f"https://vidfast.pro/tv/{identifier}/{season}/{episode}?autoPlay=true&nextButton=true&autoNext=true&sub=ar",
            f"https://www.2embed.cc/embedtv/{identifier}?s={season}&e={episode}",
            f"https://vidsrc.to/embed/tv/{identifier}/{season}/{episode}",
            f"https://multiembed.mov/?video_id={identifier}&tmdb=1&s={season}&e={episode}",
            f"https://autoembed.co/tv/tmdb/{identifier}-{season}-{episode}",
        ]
    return []
