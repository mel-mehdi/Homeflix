"""
Utility functions for common operations
Centralized helper functions for better code reuse
"""
import time
import logging
import requests
from functools import wraps
from typing import Any, Callable, Optional, Dict, Tuple
from config import api_config

logger = logging.getLogger(__name__)


class CacheManager:
    """Smart cache manager with automatic expiration"""
    
    def __init__(self):
        self._caches: Dict[str, Dict[str, Tuple[Any, float]]] = {}
    
    def get_cache(self, cache_name: str) -> dict:
        """Get or create a named cache"""
        if cache_name not in self._caches:
            self._caches[cache_name] = {}
        return self._caches[cache_name]
    
    def get(self, cache_name: str, key: str, duration: int) -> Optional[Any]:
        """Get value from cache if not expired"""
        cache = self.get_cache(cache_name)
        if key in cache:
            value, timestamp = cache[key]
            if time.time() - timestamp < duration:
                return value
            else:
                # Remove expired entry
                del cache[key]
        return None
    
    def set(self, cache_name: str, key: str, value: Any):
        """Set value in cache with current timestamp"""
        cache = self.get_cache(cache_name)
        cache[key] = (value, time.time())
    
    def clear(self, cache_name: Optional[str] = None):
        """Clear specific cache or all caches"""
        if cache_name:
            self._caches[cache_name] = {}
        else:
            self._caches = {}
    
    def size(self, cache_name: Optional[str] = None) -> int:
        """Get size of specific cache or total size"""
        if cache_name:
            return len(self._caches.get(cache_name, {}))
        return sum(len(cache) for cache in self._caches.values())
    
    def cleanup_expired(self, cache_name: str, duration: int):
        """Remove expired entries from cache"""
        cache = self.get_cache(cache_name)
        now = time.time()
        expired_keys = [
            key for key, (_, timestamp) in cache.items()
            if now - timestamp >= duration
        ]
        for key in expired_keys:
            del cache[key]


# Global cache manager instance
cache_manager = CacheManager()


def timed_cache(cache_name: str, duration: int):
    """
    Decorator for caching function results with expiration
    
    Args:
        cache_name: Name of the cache to use
        duration: Cache duration in seconds
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}_{str(args)}_{str(kwargs)}"
            
            # Try to get from cache
            cached_value = cache_manager.get(cache_name, cache_key, duration)
            if cached_value is not None:
                return cached_value
            
            # Call function and cache result
            result = func(*args, **kwargs)
            cache_manager.set(cache_name, cache_key, result)
            return result
        
        return wrapper
    return decorator


def retry_on_failure(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    Decorator to retry function on failure with exponential backoff
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay after each retry
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {e}. "
                            f"Retrying in {current_delay}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"All {max_retries} retries failed for {func.__name__}: {e}")
            
            raise last_exception
        
        return wrapper
    return decorator


@retry_on_failure(max_retries=api_config.MAX_RETRIES)
def make_api_request(url: str, headers: Optional[dict] = None, params: Optional[dict] = None) -> dict:
    """
    Make API request with retry logic and error handling
    
    Args:
        url: API endpoint URL
        headers: Optional request headers
        params: Optional query parameters
    
    Returns:
        JSON response as dictionary
    
    Raises:
        requests.RequestException: If all retries fail
    """
    try:
        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=api_config.REQUEST_TIMEOUT
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"API request failed for {url}: {e}")
        raise


def measure_time(func: Callable) -> Callable:
    """
    Decorator to measure function execution time
    Useful for performance monitoring
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        duration = end_time - start_time
        
        if duration > 1.0:  # Only log if takes more than 1 second
            logger.info(f"{func.__name__} took {duration:.2f}s to execute")
        
        return result
    return wrapper
