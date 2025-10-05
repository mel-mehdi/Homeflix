"""
Data sync script to populate database with movies and TV shows from APIs
Fast parallel processing with batch operations
"""
import requests
import time
from database import init_db
from db_service import DatabaseService
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
import threading

# TMDB Configuration
TMDB_ACCESS_TOKEN = 'eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI2YjUyNzU0MWNmODJlNjdhMmJhOGRmZTFmYjZiMDkwYyIsIm5iZiI6MTc1OTA3NDM4Mi44MDMsInN1YiI6IjY4ZDk1ODRlYWQzMTdmMmI2MWJiMDkxYSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.HnNxWDnTZIwhVWbXH8gpVfY1n6v0pse5z2A-KUSyI5I'
TMDB_BASE_URL = 'https://api.themoviedb.org/3'

# Thread-safe counter for progress
class ProgressCounter:
    def __init__(self):
        self.lock = threading.Lock()
        self.count = 0
    
    def increment(self):
        with self.lock:
            self.count += 1
            return self.count

# Session with connection pooling for faster requests
session = requests.Session()
adapter = requests.adapters.HTTPAdapter(pool_connections=20, pool_maxsize=20)
session.mount('http://', adapter)
session.mount('https://', adapter)

def fetch_and_store_vidsrc_movies(max_pages=5):
    """Fetch movies from VidSrc and store in database (parallel API fetch, sequential DB write)"""
    print("📽️  Fetching movies from VidSrc...")
    
    # Fetch all pages in parallel (fast API calls)
    all_movies = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        page_futures = {executor.submit(fetch_vidsrc_page, page, 'movies'): page for page in range(1, max_pages + 1)}
        for future in as_completed(page_futures):
            try:
                movies = future.result()
                if movies:
                    all_movies.extend(movies)
            except Exception as e:
                print(f"   ❌ Error processing page: {e}")
    
    # Fetch TMDB details in parallel (fast API calls)
    print(f"   Processing {len(all_movies)} movies...")
    movie_data_list = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        movie_futures = {executor.submit(get_movie_details_from_tmdb, movie.get('imdb_id')): movie for movie in all_movies if movie.get('imdb_id')}
        for future in as_completed(movie_futures):
            try:
                movie_data = future.result()
                if movie_data:
                    original_movie = movie_futures[future]
                    movie_data['quality'] = original_movie.get('quality', 'HD')
                    movie_data_list.append(movie_data)
            except Exception as e:
                pass
    
    # Write to database sequentially (thread-safe)
    count = 0
    with DatabaseService() as db_service:
        for movie_data in movie_data_list:
            try:
                db_service.create_or_update_movie(movie_data)
                count += 1
                print(f"   ✅ [{count}] Saved: {movie_data['title']}")
            except Exception as e:
                print(f"   ❌ Error saving {movie_data.get('title', 'Unknown')}: {e}")
    
    print(f"✅ Movies sync completed! Total: {count}")

def fetch_vidsrc_page(page, media_type):
    """Fetch a single page from VidSrc"""
    try:
        url = f"https://vidsrc.xyz/{media_type}/latest/page-{page}.json"
        response = session.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        results = data.get('result', [])
        print(f"   Page {page}: Found {len(results)} items")
        return results
    except Exception as e:
        print(f"   ❌ Error on page {page}: {e}")
        return []

def fetch_and_store_vidsrc_tvshows(max_pages=5):
    """Fetch TV shows from VidSrc and store in database (parallel API fetch, sequential DB write)"""
    print("📺 Fetching TV shows from VidSrc...")
    
    # Fetch all pages in parallel (fast API calls)
    all_tvshows = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        page_futures = {executor.submit(fetch_vidsrc_page, page, 'tvshows'): page for page in range(1, max_pages + 1)}
        for future in as_completed(page_futures):
            try:
                tvshows = future.result()
                if tvshows:
                    all_tvshows.extend(tvshows)
            except Exception as e:
                print(f"   ❌ Error processing page: {e}")
    
    # Fetch TMDB details in parallel (fast API calls)
    print(f"   Processing {len(all_tvshows)} TV shows...")
    tvshow_data_list = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        tvshow_futures = {executor.submit(get_tvshow_details_from_tmdb, show.get('imdb_id')): show for show in all_tvshows if show.get('imdb_id')}
        for future in as_completed(tvshow_futures):
            try:
                tvshow_data = future.result()
                if tvshow_data:
                    tvshow_data_list.append(tvshow_data)
            except Exception as e:
                pass
    
    # Write to database sequentially (thread-safe)
    count = 0
    with DatabaseService() as db_service:
        for tvshow_data in tvshow_data_list:
            try:
                db_service.create_or_update_tvshow(tvshow_data)
                count += 1
                print(f"   ✅ [{count}] Saved: {tvshow_data['title']}")
            except Exception as e:
                print(f"   ❌ Error saving {tvshow_data.get('title', 'Unknown')}: {e}")
    
    print(f"✅ TV shows sync completed! Total: {count}")

def fetch_and_store_trending_movies(max_pages=3):
    """Fetch trending movies from TMDB and store in database (parallel API fetch, sequential DB write)"""
    print("🔥 Fetching trending movies from TMDB...")
    
    # Fetch all pages in parallel (fast API calls)
    all_movies = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        page_futures = {executor.submit(fetch_tmdb_trending_page, page, 'movie'): page for page in range(1, max_pages + 1)}
        for future in as_completed(page_futures):
            try:
                movies = future.result()
                if movies:
                    all_movies.extend(movies)
            except Exception as e:
                print(f"   ❌ Error processing page: {e}")
    
    # Fetch details in parallel (fast API calls)
    print(f"   Processing {len(all_movies)} trending movies...")
    movie_data_list = []
    
    def process_trending_movie(movie):
        """Process a single trending movie"""
        try:
            tmdb_id = movie.get('id')
            imdb_id = get_imdb_id_from_tmdb(tmdb_id, 'movie')
            if not imdb_id:
                return None
            
            poster_path, backdrop_path = get_best_images(tmdb_id, 'movie', movie.get('poster_path'), movie.get('backdrop_path'))
            
            movie_data = {
                'imdb_id': imdb_id,
                'tmdb_id': tmdb_id,
                'title': movie.get('title', 'Unknown'),
                'overview': movie.get('overview', ''),
                'release_date': movie.get('release_date', ''),
                'year': movie.get('release_date', '')[:4] if movie.get('release_date') else '',
                'poster_path': poster_path,
                'backdrop_path': backdrop_path,
                'vote_average': movie.get('vote_average'),
                'vote_count': movie.get('vote_count'),
                'popularity': movie.get('popularity'),
                'quality': 'HD',
                'is_trending': True,
            }
            
            detailed_info = get_movie_details_from_tmdb(imdb_id)
            if detailed_info:
                movie_data.update(detailed_info)
                movie_data['is_trending'] = True
            
            return movie_data
        except Exception as e:
            return None
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        movie_futures = [executor.submit(process_trending_movie, movie) for movie in all_movies]
        for future in as_completed(movie_futures):
            try:
                movie_data = future.result()
                if movie_data:
                    movie_data_list.append(movie_data)
            except Exception as e:
                pass
    
    # Write to database sequentially (thread-safe)
    count = 0
    with DatabaseService() as db_service:
        db_service.clear_trending_flags('movie')
        for movie_data in movie_data_list:
            try:
                db_service.create_or_update_movie(movie_data)
                count += 1
                print(f"   ✅ [{count}] Saved trending: {movie_data['title']}")
            except Exception as e:
                print(f"   ❌ Error saving {movie_data.get('title', 'Unknown')}: {e}")
    
    print(f"✅ Trending movies sync completed! Total: {count}")

def fetch_tmdb_trending_page(page, media_type):
    """Fetch a single trending page from TMDB"""
    try:
        url = f"{TMDB_BASE_URL}/trending/{media_type}/week"
        headers = {'Authorization': f'Bearer {TMDB_ACCESS_TOKEN}'}
        params = {'page': page}
        
        response = session.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        results = data.get('results', [])
        print(f"   Page {page}: Found {len(results)} trending items")
        return results
    except Exception as e:
        print(f"   ❌ Error on page {page}: {e}")
        return []

def get_best_images(tmdb_id, media_type, default_poster, default_backdrop):
    """Get best quality images from TMDB (fastest version)"""
    try:
        headers = {'Authorization': f'Bearer {TMDB_ACCESS_TOKEN}'}
        images_url = f"{TMDB_BASE_URL}/{media_type}/{tmdb_id}/images"
        response = session.get(images_url, headers=headers, timeout=5)
        response.raise_for_status()
        images_data = response.json()
        
        # Get best poster
        posters = images_data.get('posters', [])
        poster_path = default_poster
        if posters:
            posters.sort(key=lambda x: x.get('vote_average', 0), reverse=True)
            poster_path = posters[0].get('file_path', default_poster)
        
        # Get best backdrop
        backdrops = images_data.get('backdrops', [])
        backdrop_path = default_backdrop
        if backdrops:
            backdrops.sort(key=lambda x: x.get('vote_average', 0), reverse=True)
            backdrop_path = backdrops[0].get('file_path', default_backdrop)
        
        return poster_path, backdrop_path
    except:
        return default_poster, default_backdrop

def fetch_and_store_trending_tvshows(max_pages=3):
    """Fetch trending TV shows from TMDB and store in database (parallel API fetch, sequential DB write)"""
    print("🔥 Fetching trending TV shows from TMDB...")
    
    # Fetch all pages in parallel (fast API calls)
    all_tvshows = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        page_futures = {executor.submit(fetch_tmdb_trending_page, page, 'tv'): page for page in range(1, max_pages + 1)}
        for future in as_completed(page_futures):
            try:
                tvshows = future.result()
                if tvshows:
                    all_tvshows.extend(tvshows)
            except Exception as e:
                print(f"   ❌ Error processing page: {e}")
    
    # Fetch details in parallel (fast API calls)
    print(f"   Processing {len(all_tvshows)} trending TV shows...")
    tvshow_data_list = []
    
    def process_trending_tvshow(show):
        """Process a single trending TV show"""
        try:
            tmdb_id = show.get('id')
            imdb_id = get_imdb_id_from_tmdb(tmdb_id, 'tv')
            if not imdb_id:
                return None
            
            poster_path, backdrop_path = get_best_images(tmdb_id, 'tv', show.get('poster_path'), show.get('backdrop_path'))
            
            tvshow_data = {
                'imdb_id': imdb_id,
                'tmdb_id': tmdb_id,
                'title': show.get('name', 'Unknown'),
                'overview': show.get('overview', ''),
                'first_air_date': show.get('first_air_date', ''),
                'year': show.get('first_air_date', '')[:4] if show.get('first_air_date') else '',
                'poster_path': poster_path,
                'backdrop_path': backdrop_path,
                'vote_average': show.get('vote_average'),
                'vote_count': show.get('vote_count'),
                'popularity': show.get('popularity'),
                'is_trending': True,
            }
            
            detailed_info = get_tvshow_details_from_tmdb(imdb_id)
            if detailed_info:
                tvshow_data.update(detailed_info)
                tvshow_data['is_trending'] = True
            
            return tvshow_data
        except Exception as e:
            return None
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        tvshow_futures = [executor.submit(process_trending_tvshow, show) for show in all_tvshows]
        for future in as_completed(tvshow_futures):
            try:
                tvshow_data = future.result()
                if tvshow_data:
                    tvshow_data_list.append(tvshow_data)
            except Exception as e:
                pass
    
    # Write to database sequentially (thread-safe)
    count = 0
    with DatabaseService() as db_service:
        db_service.clear_trending_flags('tv')
        for tvshow_data in tvshow_data_list:
            try:
                db_service.create_or_update_tvshow(tvshow_data)
                count += 1
                print(f"   ✅ [{count}] Saved trending: {tvshow_data['title']}")
            except Exception as e:
                print(f"   ❌ Error saving {tvshow_data.get('title', 'Unknown')}: {e}")
    
    print(f"✅ Trending TV shows sync completed! Total: {count}")

@lru_cache(maxsize=500)
def get_movie_details_from_tmdb(imdb_id):
    """Get detailed movie info from TMDB with images (cached for speed)"""
    try:
        headers = {'Authorization': f'Bearer {TMDB_ACCESS_TOKEN}'}
        
        # Find movie by IMDB ID
        url = f"{TMDB_BASE_URL}/find/{imdb_id}?external_source=imdb_id"
        response = session.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if not data.get('movie_results'):
            return None
        
        movie = data['movie_results'][0]
        tmdb_id = movie.get('id')
        
        # Get detailed info
        details_url = f"{TMDB_BASE_URL}/movie/{tmdb_id}"
        details_response = session.get(details_url, headers=headers, timeout=10)
        details_response.raise_for_status()
        details = details_response.json()
        
        # Get best images
        poster_path, backdrop_path = get_best_images(tmdb_id, 'movie', details.get('poster_path'), details.get('backdrop_path'))
        
        # Get certification
        cert_url = f"{TMDB_BASE_URL}/movie/{tmdb_id}/release_dates"
        cert_response = session.get(cert_url, headers=headers, timeout=10)
        cert_response.raise_for_status()
        cert_data = cert_response.json()
        
        rating = 'TV-MA'
        if cert_data.get('results'):
            for country in cert_data['results']:
                if country.get('iso_3166_1') == 'US':
                    for release in country.get('release_dates', []):
                        if release.get('certification'):
                            rating = release['certification']
                            break
                    break
        
        genres = [genre['name'] for genre in details.get('genres', [])]
        runtime = details.get('runtime', 0)
        duration = f"{runtime//60}h {runtime%60}m" if runtime else ''
        
        return {
            'imdb_id': imdb_id,
            'tmdb_id': tmdb_id,
            'title': details.get('title', 'Unknown'),
            'overview': details.get('overview', ''),
            'release_date': details.get('release_date', ''),
            'year': details.get('release_date', '')[:4] if details.get('release_date') else '',
            'rating': rating,
            'duration': duration,
            'genres': genres,
            'poster_path': poster_path,
            'backdrop_path': backdrop_path,
            'vote_average': details.get('vote_average'),
            'vote_count': details.get('vote_count'),
            'popularity': details.get('popularity'),
        }
        
    except Exception as e:
        return None

@lru_cache(maxsize=500)
def get_tvshow_details_from_tmdb(imdb_id):
    """Get detailed TV show info from TMDB with images (cached for speed)"""
    try:
        headers = {'Authorization': f'Bearer {TMDB_ACCESS_TOKEN}'}
        
        # Find TV show by IMDB ID
        url = f"{TMDB_BASE_URL}/find/{imdb_id}?external_source=imdb_id"
        response = session.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if not data.get('tv_results'):
            return None
        
        show = data['tv_results'][0]
        tmdb_id = show.get('id')
        
        # Get detailed info
        details_url = f"{TMDB_BASE_URL}/tv/{tmdb_id}"
        details_response = session.get(details_url, headers=headers, timeout=10)
        details_response.raise_for_status()
        details = details_response.json()
        
        # Get best images
        poster_path, backdrop_path = get_best_images(tmdb_id, 'tv', details.get('poster_path'), details.get('backdrop_path'))
        
        genres = [genre['name'] for genre in details.get('genres', [])]
        
        return {
            'imdb_id': imdb_id,
            'tmdb_id': tmdb_id,
            'title': details.get('name', 'Unknown'),
            'overview': details.get('overview', ''),
            'first_air_date': details.get('first_air_date', ''),
            'year': details.get('first_air_date', '')[:4] if details.get('first_air_date') else '',
            'genres': genres,
            'poster_path': poster_path,
            'backdrop_path': backdrop_path,
            'vote_average': details.get('vote_average'),
            'vote_count': details.get('vote_count'),
            'popularity': details.get('popularity'),
        }
        
    except Exception as e:
        return None

@lru_cache(maxsize=1000)
def get_imdb_id_from_tmdb(tmdb_id, media_type):
    """Get IMDB ID from TMDB ID (cached for speed)"""
    try:
        headers = {'Authorization': f'Bearer {TMDB_ACCESS_TOKEN}'}
        url = f"{TMDB_BASE_URL}/{media_type}/{tmdb_id}/external_ids"
        response = session.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get('imdb_id')
    except Exception as e:
        return None

def sync_all_data(movie_pages=5, tv_pages=5, trending_pages=3):
    """Sync all data from APIs to database"""
    print("🚀 Starting data synchronization...")
    print("=" * 60)
    
    start_time = time.time()
    
    # Initialize database
    init_db()
    
    # Fetch and store data
    fetch_and_store_trending_movies(trending_pages)
    print()
    fetch_and_store_trending_tvshows(trending_pages)
    print()
    fetch_and_store_vidsrc_movies(movie_pages)
    print()
    fetch_and_store_vidsrc_tvshows(tv_pages)
    
    # Print statistics
    with DatabaseService() as db_service:
        total_movies = db_service.get_total_movies()
        total_tvshows = db_service.get_total_tvshows()
    
    elapsed_time = time.time() - start_time
    
    print()
    print("=" * 60)
    print("✅ Data synchronization completed!")
    print(f"📊 Statistics:")
    print(f"   - Total Movies: {total_movies}")
    print(f"   - Total TV Shows: {total_tvshows}")
    print(f"   - Time elapsed: {elapsed_time:.2f} seconds")
    print("=" * 60)

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Sync media data to database')
    parser.add_argument('--movie-pages', type=int, default=50, help='Number of movie pages to fetch (50 items per page)')
    parser.add_argument('--tv-pages', type=int, default=50, help='Number of TV show pages to fetch (50 items per page)')
    parser.add_argument('--trending-pages', type=int, default=50, help='Number of trending pages to fetch (20 items per page)')
    
    args = parser.parse_args()
    
    sync_all_data(
        movie_pages=args.movie_pages,
        tv_pages=args.tv_pages,
        trending_pages=args.trending_pages
    )
