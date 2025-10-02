"""
Data sync script to populate database with movies and TV shows from APIs
"""
import requests
import time
from database import init_db
from db_service import DatabaseService

# TMDB Configuration
TMDB_ACCESS_TOKEN = 'eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI2YjUyNzU0MWNmODJlNjdhMmJhOGRmZTFmYjZiMDkwYyIsIm5iZiI6MTc1OTA3NDM4Mi44MDMsInN1YiI6IjY4ZDk1ODRlYWQzMTdmMmI2MWJiMDkxYSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.HnNxWDnTZIwhVWbXH8gpVfY1n6v0pse5z2A-KUSyI5I'
TMDB_BASE_URL = 'https://api.themoviedb.org/3'

def fetch_and_store_vidsrc_movies(max_pages=5):
    """Fetch movies from VidSrc and store in database"""
    print("📽️  Fetching movies from VidSrc...")
    
    with DatabaseService() as db_service:
        for page in range(1, max_pages + 1):
            try:
                url = f"https://vidsrc.xyz/movies/latest/page-{page}.json"
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                movies = data.get('result', [])
                print(f"   Page {page}: Found {len(movies)} movies")
                
                for movie in movies:
                    imdb_id = movie.get('imdb_id')
                    if not imdb_id:
                        continue
                    
                    # Get detailed info from TMDB
                    movie_data = get_movie_details_from_tmdb(imdb_id)
                    if movie_data:
                        movie_data['quality'] = movie.get('quality', 'HD')
                        db_service.create_or_update_movie(movie_data)
                        print(f"   ✅ Saved: {movie_data['title']}")
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                print(f"   ❌ Error on page {page}: {e}")
                continue
    
    print("✅ Movies sync completed!")

def fetch_and_store_vidsrc_tvshows(max_pages=5):
    """Fetch TV shows from VidSrc and store in database"""
    print("📺 Fetching TV shows from VidSrc...")
    
    with DatabaseService() as db_service:
        for page in range(1, max_pages + 1):
            try:
                url = f"https://vidsrc.xyz/tvshows/latest/page-{page}.json"
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                tvshows = data.get('result', [])
                print(f"   Page {page}: Found {len(tvshows)} TV shows")
                
                for show in tvshows:
                    imdb_id = show.get('imdb_id')
                    if not imdb_id:
                        continue
                    
                    # Get detailed info from TMDB
                    tvshow_data = get_tvshow_details_from_tmdb(imdb_id)
                    if tvshow_data:
                        db_service.create_or_update_tvshow(tvshow_data)
                        print(f"   ✅ Saved: {tvshow_data['title']}")
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                print(f"   ❌ Error on page {page}: {e}")
                continue
    
    print("✅ TV shows sync completed!")

def fetch_and_store_trending_movies(max_pages=3):
    """Fetch trending movies from TMDB and store in database"""
    print("🔥 Fetching trending movies from TMDB...")
    
    with DatabaseService() as db_service:
        # Clear existing trending flags
        db_service.clear_trending_flags('movie')
        
        for page in range(1, max_pages + 1):
            try:
                url = f"{TMDB_BASE_URL}/trending/movie/week"
                headers = {'Authorization': f'Bearer {TMDB_ACCESS_TOKEN}'}
                params = {'page': page}
                
                response = requests.get(url, headers=headers, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                movies = data.get('results', [])
                print(f"   Page {page}: Found {len(movies)} trending movies")
                
                for movie in movies:
                    tmdb_id = movie.get('id')
                    
                    # Get IMDB ID
                    imdb_id = get_imdb_id_from_tmdb(tmdb_id, 'movie')
                    if not imdb_id:
                        continue
                    
                    # Get high-quality images from /images endpoint
                    poster_path = movie.get('poster_path')
                    backdrop_path = movie.get('backdrop_path')
                    try:
                        images_url = f"{TMDB_BASE_URL}/movie/{tmdb_id}/images"
                        images_response = requests.get(images_url, headers=headers, timeout=10)
                        images_response.raise_for_status()
                        images_data = images_response.json()
                        
                        # Get best poster
                        posters = images_data.get('posters', [])
                        if posters:
                            posters.sort(key=lambda x: x.get('vote_average', 0), reverse=True)
                            poster_path = posters[0].get('file_path', poster_path)
                        
                        # Get best backdrop
                        backdrops = images_data.get('backdrops', [])
                        if backdrops:
                            backdrops.sort(key=lambda x: x.get('vote_average', 0), reverse=True)
                            backdrop_path = backdrops[0].get('file_path', backdrop_path)
                    except:
                        pass  # Use default paths if images fetch fails
                    
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
                    
                    # Get additional details
                    detailed_info = get_movie_details_from_tmdb(imdb_id)
                    if detailed_info:
                        movie_data.update(detailed_info)
                        movie_data['is_trending'] = True
                    
                    db_service.create_or_update_movie(movie_data)
                    print(f"   ✅ Saved trending: {movie_data['title']}")
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                print(f"   ❌ Error on page {page}: {e}")
                continue
    
    print("✅ Trending movies sync completed!")

def fetch_and_store_trending_tvshows(max_pages=3):
    """Fetch trending TV shows from TMDB and store in database"""
    print("🔥 Fetching trending TV shows from TMDB...")
    
    with DatabaseService() as db_service:
        # Clear existing trending flags
        db_service.clear_trending_flags('tv')
        
        for page in range(1, max_pages + 1):
            try:
                url = f"{TMDB_BASE_URL}/trending/tv/week"
                headers = {'Authorization': f'Bearer {TMDB_ACCESS_TOKEN}'}
                params = {'page': page}
                
                response = requests.get(url, headers=headers, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                tvshows = data.get('results', [])
                print(f"   Page {page}: Found {len(tvshows)} trending TV shows")
                
                for show in tvshows:
                    tmdb_id = show.get('id')
                    
                    # Get IMDB ID
                    imdb_id = get_imdb_id_from_tmdb(tmdb_id, 'tv')
                    if not imdb_id:
                        continue
                    
                    # Get high-quality images from /images endpoint
                    poster_path = show.get('poster_path')
                    backdrop_path = show.get('backdrop_path')
                    try:
                        images_url = f"{TMDB_BASE_URL}/tv/{tmdb_id}/images"
                        images_response = requests.get(images_url, headers=headers, timeout=10)
                        images_response.raise_for_status()
                        images_data = images_response.json()
                        
                        # Get best poster
                        posters = images_data.get('posters', [])
                        if posters:
                            posters.sort(key=lambda x: x.get('vote_average', 0), reverse=True)
                            poster_path = posters[0].get('file_path', poster_path)
                        
                        # Get best backdrop
                        backdrops = images_data.get('backdrops', [])
                        if backdrops:
                            backdrops.sort(key=lambda x: x.get('vote_average', 0), reverse=True)
                            backdrop_path = backdrops[0].get('file_path', backdrop_path)
                    except:
                        pass  # Use default paths if images fetch fails
                    
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
                    
                    # Get additional details
                    detailed_info = get_tvshow_details_from_tmdb(imdb_id)
                    if detailed_info:
                        tvshow_data.update(detailed_info)
                        tvshow_data['is_trending'] = True
                    
                    db_service.create_or_update_tvshow(tvshow_data)
                    print(f"   ✅ Saved trending: {tvshow_data['title']}")
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                print(f"   ❌ Error on page {page}: {e}")
                continue
    
    print("✅ Trending TV shows sync completed!")

def get_movie_details_from_tmdb(imdb_id):
    """Get detailed movie info from TMDB with images"""
    try:
        headers = {'Authorization': f'Bearer {TMDB_ACCESS_TOKEN}'}
        
        # Find movie by IMDB ID
        url = f"{TMDB_BASE_URL}/find/{imdb_id}?external_source=imdb_id"
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if not data.get('movie_results'):
            return None
        
        movie = data['movie_results'][0]
        tmdb_id = movie.get('id')
        
        # Get detailed info
        details_url = f"{TMDB_BASE_URL}/movie/{tmdb_id}"
        details_response = requests.get(details_url, headers=headers, timeout=10)
        details_response.raise_for_status()
        details = details_response.json()
        
        # Get high-quality images from /images endpoint
        images_url = f"{TMDB_BASE_URL}/movie/{tmdb_id}/images"
        try:
            images_response = requests.get(images_url, headers=headers, timeout=10)
            images_response.raise_for_status()
            images_data = images_response.json()
            
            # Get best poster (highest rated)
            posters = images_data.get('posters', [])
            poster_path = details.get('poster_path')
            if posters:
                posters.sort(key=lambda x: x.get('vote_average', 0), reverse=True)
                poster_path = posters[0].get('file_path', poster_path)
            
            # Get best backdrop (highest rated)
            backdrops = images_data.get('backdrops', [])
            backdrop_path = details.get('backdrop_path')
            if backdrops:
                backdrops.sort(key=lambda x: x.get('vote_average', 0), reverse=True)
                backdrop_path = backdrops[0].get('file_path', backdrop_path)
        except Exception as img_error:
            print(f"   ⚠️  Could not fetch images for movie {tmdb_id}: {img_error}")
            poster_path = details.get('poster_path')
            backdrop_path = details.get('backdrop_path')
        
        # Get certification
        cert_url = f"{TMDB_BASE_URL}/movie/{tmdb_id}/release_dates"
        cert_response = requests.get(cert_url, headers=headers, timeout=10)
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
        print(f"   ⚠️  Error getting movie details for {imdb_id}: {e}")
        return None

def get_tvshow_details_from_tmdb(imdb_id):
    """Get detailed TV show info from TMDB with images"""
    try:
        headers = {'Authorization': f'Bearer {TMDB_ACCESS_TOKEN}'}
        
        # Find TV show by IMDB ID
        url = f"{TMDB_BASE_URL}/find/{imdb_id}?external_source=imdb_id"
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if not data.get('tv_results'):
            return None
        
        show = data['tv_results'][0]
        tmdb_id = show.get('id')
        
        # Get detailed info
        details_url = f"{TMDB_BASE_URL}/tv/{tmdb_id}"
        details_response = requests.get(details_url, headers=headers, timeout=10)
        details_response.raise_for_status()
        details = details_response.json()
        
        # Get high-quality images from /images endpoint
        images_url = f"{TMDB_BASE_URL}/tv/{tmdb_id}/images"
        try:
            images_response = requests.get(images_url, headers=headers, timeout=10)
            images_response.raise_for_status()
            images_data = images_response.json()
            
            # Get best poster (highest rated)
            posters = images_data.get('posters', [])
            poster_path = details.get('poster_path')
            if posters:
                posters.sort(key=lambda x: x.get('vote_average', 0), reverse=True)
                poster_path = posters[0].get('file_path', poster_path)
            
            # Get best backdrop (highest rated)
            backdrops = images_data.get('backdrops', [])
            backdrop_path = details.get('backdrop_path')
            if backdrops:
                backdrops.sort(key=lambda x: x.get('vote_average', 0), reverse=True)
                backdrop_path = backdrops[0].get('file_path', backdrop_path)
        except Exception as img_error:
            print(f"   ⚠️  Could not fetch images for TV show {tmdb_id}: {img_error}")
            poster_path = details.get('poster_path')
            backdrop_path = details.get('backdrop_path')
        
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
        print(f"   ⚠️  Error getting TV show details for {imdb_id}: {e}")
        return None

def get_imdb_id_from_tmdb(tmdb_id, media_type):
    """Get IMDB ID from TMDB ID"""
    try:
        headers = {'Authorization': f'Bearer {TMDB_ACCESS_TOKEN}'}
        url = f"{TMDB_BASE_URL}/{media_type}/{tmdb_id}/external_ids"
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get('imdb_id')
    except Exception as e:
        print(f"   ⚠️  Error getting IMDB ID for TMDB {tmdb_id}: {e}")
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
    parser.add_argument('--movie-pages', type=int, default=5, help='Number of movie pages to fetch')
    parser.add_argument('--tv-pages', type=int, default=5, help='Number of TV show pages to fetch')
    parser.add_argument('--trending-pages', type=int, default=3, help='Number of trending pages to fetch')
    
    args = parser.parse_args()
    
    sync_all_data(
        movie_pages=args.movie_pages,
        tv_pages=args.tv_pages,
        trending_pages=args.trending_pages
    )
