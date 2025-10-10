from flask import Flask, render_template, request, Response, send_file, send_from_directory, abort, redirect, jsonify
import os
import requests
import io
import time
import logging
from database import init_db
from db_service import DatabaseService

# Configure logging
logging.basicConfig(
    level=logging.WARNING,  # Only show warnings and errors
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
# Disable Flask's default request logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# TMDB API configuration
TMDB_ACCESS_TOKEN = 'eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI2YjUyNzU0MWNmODJlNjdhMmJhOGRmZTFmYjZiMDkwYyIsIm5iZiI6MTc1OTA3NDM4Mi44MDMsInN1YiI6IjY4ZDk1ODRlYWQzMTdmMmI2MWJiMDkxYSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.HnNxWDnTZIwhVWbXH8gpVfY1n6v0pse5z2A-KUSyI5I'
TMDB_BASE_URL = 'https://api.themoviedb.org/3'
TMDB_IMAGE_BASE_URL = 'https://image.tmdb.org/t/p/w500'
TMDB_BACKDROP_BASE_URL = 'https://image.tmdb.org/t/p/w1280'

CSS_FOLDER = "css"  # Add this line

# Initialize database on startup
init_db()

# Caches
tmdb_cache = {}
vidsrc_cache = {}
poster_cache = {}
backdrop_cache = {}
CACHE_DURATION_TMDB = 3600  # 1 hour
CACHE_DURATION_VIDSRC = 600  # 10 minutes

def get_cached_data(url, cache, duration, headers=None):
    now = time.time()
    if url in cache:
        data, timestamp = cache[url]
        if now - timestamp < duration:
            return data
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    cache[url] = (data, now)
    return data

def get_cached_tmdb_data(url, headers, params=None):
    """Get data from cache or fetch from TMDB"""
    cache_key = url + str(params) if params else url
    now = time.time()
    if cache_key in tmdb_cache:
        data, timestamp = tmdb_cache[cache_key]
        if now - timestamp < CACHE_DURATION_TMDB:
            return data
        else:
            del tmdb_cache[cache_key]
    
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    data = response.json()
    tmdb_cache[cache_key] = (data, now)
    return data

def _populate_image_cache(items, media_type):
    """Populate poster and backdrop cache from database results"""
    with DatabaseService() as db_service:
        for item in items:
            tmdb_id = item.get('tmdb_id')
            if not tmdb_id:
                continue
            
            # For mixed types (My List), determine type from item
            current_type = media_type
            if media_type == 'mixed':
                current_type = 'movie' if item.get('type') == 'movie' else 'tv'
            
            # Get the database object to access poster_path and backdrop_path
            if current_type == 'movie':
                db_item = db_service.get_movie_by_tmdb_id(tmdb_id)
            else:
                db_item = db_service.get_tvshow_by_tmdb_id(tmdb_id)
            
            if db_item:
                # Populate poster cache
                if db_item.poster_path:
                    poster_cache[f"{current_type}_{tmdb_id}_poster"] = db_item.poster_path
                
                # Populate backdrop cache
                if db_item.backdrop_path:
                    backdrop_cache[f"{current_type}_{tmdb_id}_backdrop"] = db_item.backdrop_path

@app.route('/favicon.ico')
def favicon():
    """Handle favicon requests"""
    return '', 204

@app.route('/')
def index():
    """Display all movies and series"""
    movie_page = int(request.args.get('movie_page', 1))
    series_page = int(request.args.get('series_page', 1))
    try:
        # Use database instead of API calls
        with DatabaseService() as db_service:
            movies = db_service.get_latest_movies(movie_page)
            series = db_service.get_latest_tvshows(series_page)
            trending_movies = db_service.get_trending_movies()
            trending_series = db_service.get_trending_tvshows()
            my_list = db_service.get_my_list()  # Get My List items
        
        # Populate image caches from database results
        _populate_image_cache(movies, 'movie')
        _populate_image_cache(series, 'tv')
        _populate_image_cache(trending_movies, 'movie')
        _populate_image_cache(trending_series, 'tv')
        if my_list:
            _populate_image_cache(my_list, 'mixed')  # My List can have both movies and series
        
        # Get backdrop URLs for hero section from trending movies
        backdrop_urls = []
        for movie in trending_movies:
            backdrop_url = movie.get('backdrop_url')
            if backdrop_url:
                backdrop_urls.append(backdrop_url)
        
        # If not enough backdrops, add from movies
        if len(backdrop_urls) < 5:
            for movie in movies:
                if len(backdrop_urls) >= 10:
                    break
                backdrop_url = movie.get('backdrop_url')
                if backdrop_url:
                    backdrop_urls.append(backdrop_url)
        
        return render_template('index.html', movies=movies, series=series, 
                             trending_movies=trending_movies, trending_series=trending_series, 
                             movie_page=movie_page, series_page=series_page, 
                             backdrop_urls=backdrop_urls, my_list=my_list)
    except Exception as e:
        logger.error(f" in index: {e}")
        return f"Error accessing data: {e}", 500

@app.route('/load_more_movies/<int:page>')
def load_more_movies(page):
    """Load more movies for AJAX"""
    try:
        with DatabaseService() as db_service:
            movies = db_service.get_latest_movies(page)
        _populate_image_cache(movies, 'movie')
        return {'movies': movies}
    except Exception as e:
        return {'error': str(e)}, 500

@app.route('/load_more_series/<int:page>')
def load_more_series(page):
    """Load more series for AJAX"""
    try:
        with DatabaseService() as db_service:
            series = db_service.get_latest_tvshows(page)
        _populate_image_cache(series, 'tv')
        return {'series': series}
    except Exception as e:
        return {'error': str(e)}, 500

@app.route('/watch/movie/<imdb_id>')
def watch_movie(imdb_id):
    """Watch movie using embed URL with multiple fallback sources"""
    try:
        # Fetch movie details from TMDB for accurate info
        details = get_movie_details(imdb_id)
        tmdb_id = None
        title = 'Unknown Movie'
        
        if details:
            title = details['title']
            tmdb_id = details.get('tmdb_id')
        
        # Generate multiple embed sources as fallback options
        embed_sources = []
        if tmdb_id:
            embed_sources = [
                f"https://vidsrc.xyz/embed/movie?tmdb={tmdb_id}",
                f"https://vidsrc.pro/embed/movie/{tmdb_id}",
                f"https://vidsrc.me/embed/movie?tmdb={tmdb_id}",
                f"https://www.2embed.cc/embed/{imdb_id}",
                f"https://vidsrc.to/embed/movie/{imdb_id}",
            ]
        else:
            embed_sources = [
                f"https://vidsrc.me/embed/movie/{imdb_id}",
                f"https://www.2embed.cc/embed/{imdb_id}",
                f"https://vidsrc.to/embed/movie/{imdb_id}",
            ]
        
        embed_url = embed_sources[0]  # Use first source as default
        
        return render_template('player.html', 
                             embed_url=embed_url, 
                             embed_sources=embed_sources,
                             title=title, 
                             type='movie',
                             imdb_id=imdb_id,
                             tmdb_id=tmdb_id)
    except Exception as e:
        logger.error(f" in watch_movie: {e}")
        return f"Error: {e}", 500

@app.route('/watch/series/<imdb_id>')
def watch_series(imdb_id):
    """Watch series using embed URL with multiple fallback sources"""
    try:
        # Fetch series details from TMDB for accurate info
        details = get_series_details(imdb_id)
        tmdb_id = None
        title = 'Unknown Series'
        
        if details:
            title = details['title']
            tmdb_id = details.get('tmdb_id')
        
        # Generate multiple embed sources as fallback options
        embed_sources = []
        if tmdb_id:
            embed_sources = [
                f"https://vidsrc.xyz/embed/tv?tmdb={tmdb_id}",
                f"https://vidsrc.pro/embed/tv/{tmdb_id}",
                f"https://vidsrc.me/embed/tv?tmdb={tmdb_id}",
                f"https://www.2embed.cc/embedtv/{imdb_id}",
                f"https://vidsrc.to/embed/tv/{imdb_id}",
            ]
        else:
            embed_sources = [
                f"https://vidsrc.me/embed/tv/{imdb_id}",
                f"https://www.2embed.cc/embedtv/{imdb_id}",
                f"https://vidsrc.to/embed/tv/{imdb_id}",
            ]
        
        embed_url = embed_sources[0]  # Use first source as default
        
        return render_template('player.html', 
                             embed_url=embed_url, 
                             embed_sources=embed_sources,
                             title=title, 
                             type='series',
                             imdb_id=imdb_id,
                             tmdb_id=tmdb_id)
    except Exception as e:
        logger.error(f" in watch_series: {e}")
        return f"Error: {e}", 500

@app.route('/series/<imdb_id>')
def series_details(imdb_id):
    """Display series details with seasons and episodes"""
    try:
        # Fetch series details from database first
        with DatabaseService() as db_service:
            series = db_service.get_tvshow_by_imdb_id(imdb_id)
            my_list = db_service.get_my_list()  # Get My List items
        
        if not series:
            return "Series not found", 404
        
        series_dict = series.to_dict()
        tmdb_id = series.tmdb_id
        
        # Fetch detailed information from TMDB
        if tmdb_id:
            # Get full series details
            url = f"{TMDB_BASE_URL}/tv/{tmdb_id}"
            headers = {'Authorization': f'Bearer {TMDB_ACCESS_TOKEN}'}
            series_data = get_cached_tmdb_data(url, headers)
            
            # Get seasons information
            seasons = []
            for season_data in series_data.get('seasons', []):
                if season_data.get('season_number', 0) > 0:  # Skip specials (season 0)
                    seasons.append({
                        'season_number': season_data.get('season_number'),
                        'name': season_data.get('name'),
                        'episode_count': season_data.get('episode_count'),
                        'overview': season_data.get('overview'),
                        'air_date': season_data.get('air_date'),
                        'poster_path': season_data.get('poster_path')
                    })
            
            # Get cast information
            credits_url = f"{TMDB_BASE_URL}/tv/{tmdb_id}/credits"
            credits_data = get_cached_tmdb_data(credits_url, headers)
            cast = credits_data.get('cast', [])[:10]  # Top 10 cast members
            
            # Get content rating
            content_ratings_url = f"{TMDB_BASE_URL}/tv/{tmdb_id}/content_ratings"
            ratings_data = get_cached_tmdb_data(content_ratings_url, headers)
            rating = 'TV-MA'  # default
            for item in ratings_data.get('results', []):
                if item.get('iso_3166_1') == 'US':
                    rating = item.get('rating', 'TV-MA')
                    break
            
            # Update series dict with additional info
            series_dict['rating'] = rating
            series_dict['cast'] = cast
            series_dict['seasons'] = seasons
            series_dict['genres'] = series_data.get('genres', [])
            series_dict['created_by'] = series_data.get('created_by', [])
            series_dict['networks'] = series_data.get('networks', [])
            series_dict['status'] = series_data.get('status', '')
            series_dict['tagline'] = series_data.get('tagline', '')
        
        return render_template('series_details.html', series=series_dict, imdb_id=imdb_id, my_list=my_list)
    except Exception as e:
        logger.error(f" in series_details: {e}")
        return f"Error: {e}", 500

@app.route('/movie/<imdb_id>')
def movie_details(imdb_id):
    """Display movie details page"""
    try:
        # Fetch movie details from database first
        with DatabaseService() as db_service:
            movie = db_service.get_movie_by_imdb_id(imdb_id)
            my_list = db_service.get_my_list()  # Get My List items
        
        if not movie:
            return "Movie not found", 404
        
        movie_dict = movie.to_dict()
        tmdb_id = movie.tmdb_id
        
        # Fetch detailed information from TMDB
        if tmdb_id:
            # Get full movie details
            url = f"{TMDB_BASE_URL}/movie/{tmdb_id}"
            headers = {'Authorization': f'Bearer {TMDB_ACCESS_TOKEN}'}
            movie_data = get_cached_tmdb_data(url, headers)
            
            # Get cast information
            credits_url = f"{TMDB_BASE_URL}/movie/{tmdb_id}/credits"
            credits_data = get_cached_tmdb_data(credits_url, headers)
            cast = credits_data.get('cast', [])[:10]  # Top 10 cast members
            crew = credits_data.get('crew', [])
            
            # Get director
            director = next((person for person in crew if person.get('job') == 'Director'), None)
            
            # Get content rating
            releases_url = f"{TMDB_BASE_URL}/movie/{tmdb_id}/release_dates"
            releases_data = get_cached_tmdb_data(releases_url, headers)
            rating = 'NR'  # default
            for country in releases_data.get('results', []):
                if country.get('iso_3166_1') == 'US':
                    release_dates = country.get('release_dates', [])
                    if release_dates:
                        rating = release_dates[0].get('certification', 'NR')
                    break
            
            # Update movie dict with additional info
            movie_dict['rating'] = rating
            movie_dict['cast'] = cast
            movie_dict['director'] = director
            movie_dict['genres'] = movie_data.get('genres', [])
            movie_dict['runtime'] = movie_data.get('runtime', 0)
            movie_dict['tagline'] = movie_data.get('tagline', '')
            movie_dict['budget'] = movie_data.get('budget', 0)
            movie_dict['revenue'] = movie_data.get('revenue', 0)
        
        return render_template('movie_details.html', movie=movie_dict, imdb_id=imdb_id, my_list=my_list)
    except Exception as e:
        logger.error(f"Error in movie_details: {e}")
        return f"Error: {e}", 500

@app.route('/series/<imdb_id>/season/<int:season_number>')
def season_episodes(imdb_id, season_number):
    """Display episodes for a specific season"""
    try:
        # Fetch series details from database
        with DatabaseService() as db_service:
            series = db_service.get_tvshow_by_imdb_id(imdb_id)
        
        if not series:
            return "Series not found", 404
        
        tmdb_id = series.tmdb_id
        
        # Fetch season details from TMDB
        if tmdb_id:
            url = f"{TMDB_BASE_URL}/tv/{tmdb_id}/season/{season_number}"
            headers = {'Authorization': f'Bearer {TMDB_ACCESS_TOKEN}'}
            season_data = get_cached_tmdb_data(url, headers)
            
            episodes = []
            for ep_data in season_data.get('episodes', []):
                episodes.append({
                    'episode_number': ep_data.get('episode_number'),
                    'name': ep_data.get('name'),
                    'overview': ep_data.get('overview'),
                    'air_date': ep_data.get('air_date'),
                    'runtime': ep_data.get('runtime'),
                    'still_path': ep_data.get('still_path'),
                    'vote_average': ep_data.get('vote_average')
                })
            
            season_info = {
                'season_number': season_number,
                'name': season_data.get('name'),
                'overview': season_data.get('overview'),
                'air_date': season_data.get('air_date'),
                'episodes': episodes
            }
            
            return render_template('season_details.html', 
                                 series=series.to_dict(), 
                                 season=season_info,
                                 imdb_id=imdb_id,
                                 tmdb_id=tmdb_id)
    except Exception as e:
        logger.error(f" in season_episodes: {e}")
        return f"Error: {e}", 500

@app.route('/watch/series/<imdb_id>/<int:season_number>/<int:episode_number>')
def watch_episode(imdb_id, season_number, episode_number):
    """Watch a specific episode"""
    try:
        # Fetch series details from database
        with DatabaseService() as db_service:
            series = db_service.get_tvshow_by_imdb_id(imdb_id)
        
        if not series:
            return "Series not found", 404
        
        tmdb_id = series.tmdb_id
        title = series.title
        
        # Generate multiple embed sources
        embed_sources = []
        if tmdb_id:
            embed_sources = [
                f"https://vidsrc.xyz/embed/tv?tmdb={tmdb_id}&season={season_number}&episode={episode_number}",
                f"https://vidsrc.pro/embed/tv/{tmdb_id}/{season_number}/{episode_number}",
                f"https://vidsrc.me/embed/tv?tmdb={tmdb_id}&season={season_number}&episode={episode_number}",
                f"https://www.2embed.cc/embedtv/{imdb_id}&s={season_number}&e={episode_number}",
                f"https://vidsrc.to/embed/tv/{imdb_id}/{season_number}/{episode_number}",
            ]
        else:
            embed_sources = [
                f"https://vidsrc.me/embed/tv/{imdb_id}?season={season_number}&episode={episode_number}",
                f"https://www.2embed.cc/embedtv/{imdb_id}&s={season_number}&e={episode_number}",
                f"https://vidsrc.to/embed/tv/{imdb_id}/{season_number}/{episode_number}",
            ]
        
        embed_url = embed_sources[0]
        
        return render_template('player.html',
                             embed_url=embed_url,
                             embed_sources=embed_sources,
                             title=f"{title} - S{season_number}E{episode_number}",
                             series_title=title,
                             type='episode',
                             imdb_id=imdb_id,
                             tmdb_id=tmdb_id,
                             season=season_number,
                             episode=episode_number)
    except Exception as e:
        logger.error(f" in watch_episode: {e}")
        return f"Error: {e}", 500

def search_tmdb_movies(query, page=1):
    """Search movies using TMDB API"""
    try:
        url = f"{TMDB_BASE_URL}/search/movie"
        headers = {'Authorization': f'Bearer {TMDB_ACCESS_TOKEN}'}
        params = {'query': query, 'page': page}
        data = get_cached_tmdb_data(url, headers, params=params)
        movies = data.get('results', [])[:15]  # Limit to 15
        filtered_movies = []
        for movie in movies:
            movie['tmdb_id'] = movie['id']
            # Get IMDB ID
            imdb_id = get_imdb_id(movie['tmdb_id'], 'movie')
            if imdb_id:  # Only include movies with IMDB IDs
                movie['imdb_id'] = imdb_id
                # Build poster URL directly
                movie['poster_url'] = f"/poster/movie/{movie['tmdb_id']}"
                movie['backdrop_url'] = f"/backdrop/movie/{movie['tmdb_id']}" if movie.get('backdrop_path') else None
                movie['quality'] = 'HD'  # Default
                # Cache the poster path if available
                if movie.get('poster_path'):
                    poster_cache[f"movie_{movie['tmdb_id']}_poster"] = movie['poster_path']
                if movie.get('backdrop_path'):
                    backdrop_cache[f"movie_{movie['tmdb_id']}_backdrop"] = movie['backdrop_path']
                filtered_movies.append(movie)
        return filtered_movies
    except Exception as e:
        logger.error(f" searching TMDB movies: {e}")
        return []

def search_tmdb_series(query, page=1):
    """Search TV series using TMDB API"""
    try:
        url = f"{TMDB_BASE_URL}/search/tv"
        headers = {'Authorization': f'Bearer {TMDB_ACCESS_TOKEN}'}
        params = {'query': query, 'page': page}
        data = get_cached_tmdb_data(url, headers, params=params)
        series = data.get('results', [])[:15]  # Limit to 15
        filtered_series = []
        for show in series:
            show['tmdb_id'] = show['id']
            # Get IMDB ID
            imdb_id = get_imdb_id(show['tmdb_id'], 'tv')
            if imdb_id:  # Only include series with IMDB IDs
                show['imdb_id'] = imdb_id
                # Build poster URL directly
                show['poster_url'] = f"/poster/tv/{show['tmdb_id']}"
                show['backdrop_url'] = f"/backdrop/tv/{show['tmdb_id']}" if show.get('backdrop_path') else None
                # Cache the poster path if available
                if show.get('poster_path'):
                    poster_cache[f"tv_{show['tmdb_id']}_poster"] = show['poster_path']
                if show.get('backdrop_path'):
                    backdrop_cache[f"tv_{show['tmdb_id']}_backdrop"] = show['backdrop_path']
                filtered_series.append(show)
        return filtered_series
    except Exception as e:
        logger.error(f" searching TMDB series: {e}")
        return []

def get_imdb_id(tmdb_id, media_type):
    """Get IMDB ID from TMDB ID"""
    try:
        url = f"{TMDB_BASE_URL}/{media_type}/{tmdb_id}/external_ids"
        headers = {'Authorization': f'Bearer {TMDB_ACCESS_TOKEN}'}
        data = get_cached_tmdb_data(url, headers)
        return data.get('imdb_id')
    except Exception as e:
        logger.error(f" getting IMDB ID for {tmdb_id}: {e}")
        return None

def get_poster_url(tmdb_id, media_type='movie'):
    """Get poster URL - checks database first, then fetches from API if needed"""
    if not tmdb_id:
        return None
    
    key = f"{media_type}_{tmdb_id}_poster"
    
    # Check if already in cache
    if key in poster_cache:
        return f"/poster/{media_type}/{tmdb_id}"
    
    # Try to get from database
    try:
        with DatabaseService() as db_service:
            if media_type == 'movie':
                item = db_service.get_movie_by_tmdb_id(tmdb_id)
            else:
                item = db_service.get_tvshow_by_tmdb_id(tmdb_id)
            
            if item and item.poster_path:
                poster_cache[key] = item.poster_path
                return f"/poster/{media_type}/{tmdb_id}"
    except Exception as e:
        logger.error(f" getting poster from DB for {tmdb_id}: {e}")
    
    # Fallback to API if not in database
    if not TMDB_ACCESS_TOKEN:
        return f"/poster/{media_type}/{tmdb_id}"
    
    try:
        url = f"{TMDB_BASE_URL}/{media_type}/{tmdb_id}/images"
        headers = {'Authorization': f'Bearer {TMDB_ACCESS_TOKEN}'}
        data = get_cached_data(url, tmdb_cache, CACHE_DURATION_TMDB, headers)
        posters = data.get('posters', [])
        if posters:
            posters.sort(key=lambda x: x.get('vote_average', 0), reverse=True)
            poster_cache[key] = posters[0]['file_path']
            return f"/poster/{media_type}/{tmdb_id}"
    except Exception as e:
        logger.error(f" getting poster from API for {tmdb_id}: {e}")
    
    return None

@app.route('/poster/<media_type>/<int:tmdb_id>')
def get_poster(media_type, tmdb_id):
    if not TMDB_ACCESS_TOKEN:
        svg = '''<svg width="300" height="450" xmlns="http://www.w3.org/2000/svg">
        <rect width="300" height="450" fill="#333"/>
        <text x="150" y="225" text-anchor="middle" fill="white" font-size="20">No Poster</text>
        </svg>'''
        return Response(svg, mimetype='image/svg+xml')
    
    key = f"{media_type}_{tmdb_id}_poster"
    if key not in poster_cache:
        abort(404)
    poster_path = poster_cache[key]
    
    try:
        image_url = f"{TMDB_IMAGE_BASE_URL}{poster_path}"
        image_response = requests.get(image_url)
        image_response.raise_for_status()
        
        return send_file(io.BytesIO(image_response.content), mimetype=image_response.headers.get('content-type', 'image/jpeg'))
    except Exception as e:
        logger.error(f" proxying poster: {e}")
        abort(404)

def get_backdrop_url(tmdb_id, media_type='movie'):
    """Get backdrop URL - checks database first, then fetches from API if needed"""
    if not tmdb_id:
        return None
    
    key = f"{media_type}_{tmdb_id}_backdrop"
    
    # Check if already in cache
    if key in backdrop_cache:
        return f"/backdrop/{media_type}/{tmdb_id}"
    
    # Try to get from database
    try:
        with DatabaseService() as db_service:
            if media_type == 'movie':
                item = db_service.get_movie_by_tmdb_id(tmdb_id)
            else:
                item = db_service.get_tvshow_by_tmdb_id(tmdb_id)
            
            if item and item.backdrop_path:
                backdrop_cache[key] = item.backdrop_path
                return f"/backdrop/{media_type}/{tmdb_id}"
    except Exception as e:
        logger.error(f" getting backdrop from DB for {tmdb_id}: {e}")
    
    # Fallback to API if not in database
    if not TMDB_ACCESS_TOKEN:
        return None
    
    try:
        url = f"{TMDB_BASE_URL}/{media_type}/{tmdb_id}/images"
        headers = {'Authorization': f'Bearer {TMDB_ACCESS_TOKEN}'}
        data = get_cached_data(url, tmdb_cache, CACHE_DURATION_TMDB, headers)
        backdrops = data.get('backdrops', [])
        if backdrops:
            backdrops.sort(key=lambda x: x.get('vote_average', 0), reverse=True)
            backdrop_cache[key] = backdrops[0]['file_path']
            return f"/backdrop/{media_type}/{tmdb_id}"
    except Exception as e:
        logger.error(f" getting backdrop from API for {tmdb_id}: {e}")
    
    return None

@app.route('/backdrop/<media_type>/<int:tmdb_id>')
def get_backdrop(media_type, tmdb_id):
    if not TMDB_ACCESS_TOKEN:
        svg = '''<svg width="500" height="281" xmlns="http://www.w3.org/2000/svg">
        <rect width="500" height="281" fill="#333"/>
        <text x="250" y="140" text-anchor="middle" fill="white" font-size="20">No Backdrop</text>
        </svg>'''
        return Response(svg, mimetype='image/svg+xml')
    
    key = f"{media_type}_{tmdb_id}_backdrop"
    if key not in backdrop_cache:
        abort(404)
    backdrop_path = backdrop_cache[key]
    
    try:
        image_url = f"{TMDB_BACKDROP_BASE_URL}{backdrop_path}"
        image_response = requests.get(image_url)
        image_response.raise_for_status()
        
        return send_file(io.BytesIO(image_response.content), mimetype=image_response.headers.get('content-type', 'image/jpeg'))
    except Exception as e:
        logger.error(f" proxying backdrop: {e}")
        abort(404)

@app.route('/css/<filename>')
def serve_css(filename):
    """Serve CSS files"""
    try:
        return send_from_directory(CSS_FOLDER, filename)
    except Exception as e:
        logger.error(f" serving CSS {filename}: {e}")
        abort(404)

@app.route('/search')
def search():
    """Search for movies and series"""
    query = request.args.get('q', '').strip()
    if not query:
        return redirect('/')
    
    try:
        # Try database first for fast search
        with DatabaseService() as db_service:
            movies = db_service.search_movies(query)
            series = db_service.search_tvshows(query)
        
        # If no results in database, fallback to API search
        if not movies:
            movies = search_tmdb_movies(query)
        else:
            _populate_image_cache(movies, 'movie')
        
        if not series:
            series = search_tmdb_series(query)
        else:
            _populate_image_cache(series, 'tv')
        
        # Get backdrop URLs from search results (already in database results)
        backdrop_urls = []
        for movie in movies[:5]:  # Limit to first 5 for backdrops
            backdrop_url = movie.get('backdrop_url')
            if backdrop_url:
                backdrop_urls.append(backdrop_url)
        for show in series[:5]:
            backdrop_url = show.get('backdrop_url')
            if backdrop_url:
                backdrop_urls.append(backdrop_url)
        
        return render_template('index.html', 
                             movies=movies, 
                             series=series, 
                             movie_page=1, 
                             series_page=1, 
                             backdrop_urls=backdrop_urls, 
                             search_query=query,
                             trending_movies=[],
                             trending_series=[],
                             continue_watching=[],
                             my_list=[])
    except Exception as e:
        logger.error(f" in search: {e}")
        return f"Error searching: {e}", 500

@app.route('/search_more_movies/<query>/<int:page>')
def search_more_movies(query, page):
    """Load more search results for movies"""
    try:
        movies = search_tmdb_movies(query, page)
        return {'movies': movies}
    except Exception as e:
        return {'error': str(e)}, 500

@app.route('/search_more_series/<query>/<int:page>')
def search_more_series(query, page):
    """Load more search results for series"""
    try:
        series = search_tmdb_series(query, page)
        return {'series': series}
    except Exception as e:
        return {'error': str(e)}, 500

@app.route('/api/my-list', methods=['POST'])
def add_to_my_list():
    """Add or remove item from My List"""
    try:
        data = request.get_json()
        action = data.get('action', 'add')  # 'add' or 'remove'
        imdb_id = data.get('imdb_id') or data.get('id')  # support both
        media_type = data.get('type')  # 'movie' or 'tv'
        tmdb_id = data.get('tmdb_id')
        title = data.get('title')
        
        if not imdb_id or not media_type:
            return jsonify({'error': 'Missing id or type'}), 400
        
        with DatabaseService() as db_service:
            if media_type == 'movie':
                movie = db_service.get_movie_by_imdb_id(imdb_id)
                if movie:
                    if action == 'add':
                        db_service.add_to_my_list('movie', movie.imdb_id, movie.tmdb_id, movie.title)
                        logger.info(f"Added movie {imdb_id} to My List")
                    else:
                        db_service.remove_from_my_list('movie', movie.imdb_id)
                        logger.info(f"Removed movie {imdb_id} from My List")
                    return jsonify({'success': True})
            else:
                series = db_service.get_tvshow_by_imdb_id(imdb_id)
                if series:
                    if action == 'add':
                        db_service.add_to_my_list('series', series.imdb_id, series.tmdb_id, series.title)
                        logger.info(f"Added series {imdb_id} to My List")
                    else:
                        db_service.remove_from_my_list('series', series.imdb_id)
                        logger.info(f"Removed series {imdb_id} from My List")
                    return jsonify({'success': True})
        
        return jsonify({'error': 'Item not found'}), 404
    except Exception as e:
        logger.error(f"Error in api_my_list: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/my-list', methods=['GET'])
def get_my_list_api():
    """API endpoint to get My List items"""
    try:
        with DatabaseService() as db_service:
            my_list = db_service.get_my_list()
            logger.info(f"Fetching My List: {len(my_list)} items")
            return jsonify({'success': True, 'items': my_list})
    except Exception as e:
        logger.error(f"Error in get_my_list_api: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/continue_watching', methods=['POST'])
def save_continue_watching():
    """Save continue watching progress"""
    try:
        data = request.get_json()
        media_type = data.get('type')
        media_id = data.get('id')
        title = data.get('title')
        progress = data.get('progress', 0)
        duration = data.get('duration', 0)
        poster_url = data.get('poster_url', '')
        
        # For now, just log the progress - you can extend this to save to database
        logger.info(f"Continue watching: {title} ({media_type}) - Progress: {progress}/{duration}s")
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error saving continue watching: {e}")
        return jsonify({'error': str(e)}), 500

def get_movie_details(imdb_id):
    """Get movie details from TMDB by IMDB ID"""
    try:
        url = f"{TMDB_BASE_URL}/find/{imdb_id}"
        headers = {'Authorization': f'Bearer {TMDB_ACCESS_TOKEN}'}
        params = {'external_source': 'imdb_id'}
        data = get_cached_tmdb_data(url, headers, params=params)
        
        if data.get('movie_results'):
            movie = data['movie_results'][0]
            movie['tmdb_id'] = movie['id']
            return movie
        return None
    except Exception as e:
        logger.error(f" getting movie details for {imdb_id}: {e}")
        return None

def get_series_details(imdb_id):
    """Get series details from TMDB by IMDB ID"""
    try:
        url = f"{TMDB_BASE_URL}/find/{imdb_id}"
        headers = {'Authorization': f'Bearer {TMDB_ACCESS_TOKEN}'}
        params = {'external_source': 'imdb_id'}
        data = get_cached_tmdb_data(url, headers, params=params)
        
        if data.get('tv_results'):
            series = data['tv_results'][0]
            series['tmdb_id'] = series['id']
            return series
        return None
    except Exception as e:
        logger.error(f" getting series details for {imdb_id}: {e}")
        return None

def get_network_ip():
    """Get the network IP address of the machine"""
    try:
        # Try to get IP from external service
        response = requests.get('https://api.ipify.org', timeout=5)
        if response.status_code == 200:
            return response.text.strip()
    except:
        pass
    
    try:
        # Fallback: get local IP
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"  # Fallback

@app.route('/api/next_episode/<imdb_id>/<int:season>/<int:episode>')
def get_next_episode(imdb_id, season, episode):
    """Get next episode information for series"""
    try:
        # Get series details to check total episodes
        series_details = get_series_details(imdb_id)
        if not series_details:
            return jsonify({'has_next': False})
        
        tmdb_id = series_details.get('tmdb_id')
        if not tmdb_id:
            return jsonify({'has_next': False})
        
        # Get season details to check episode count
        url = f"{TMDB_BASE_URL}/tv/{tmdb_id}/season/{season}"
        headers = {'Authorization': f'Bearer {TMDB_ACCESS_TOKEN}'}
        season_data = get_cached_tmdb_data(url, headers)
        
        total_episodes = len(season_data.get('episodes', []))
        next_episode = episode + 1
        next_season = season
        
        # Check if there's a next episode in current season
        if next_episode <= total_episodes:
            # Next episode exists in current season
            episode_data = season_data['episodes'][next_episode - 1]  # 0-indexed
            
            return jsonify({
                'has_next': True,
                'next_season': next_season,
                'next_episode': next_episode,
                'next_title': episode_data.get('name', f'Episode {next_episode}'),
                'next_overview': episode_data.get('overview', ''),
                'next_still_path': f"{TMDB_IMAGE_BASE_URL}{episode_data['still_path']}" if episode_data.get('still_path') else None
            })
        else:
            # Check if there's a next season
            next_season = season + 1
            try:
                url = f"{TMDB_BASE_URL}/tv/{tmdb_id}/season/{next_season}"
                next_season_data = get_cached_tmdb_data(url, headers)
                
                if next_season_data.get('episodes'):
                    first_episode = next_season_data['episodes'][0]
                    return jsonify({
                        'has_next': True,
                        'next_season': next_season,
                        'next_episode': 1,
                        'next_title': first_episode.get('name', 'Episode 1'),
                        'next_overview': first_episode.get('overview', ''),
                        'next_still_path': f"{TMDB_IMAGE_BASE_URL}{first_episode['still_path']}" if first_episode.get('still_path') else None
                    })
            except:
                pass
        
        return jsonify({'has_next': False})
        
    except Exception as e:
        logger.error(f"Error getting next episode for {imdb_id} S{season}E{episode}: {e}")
        return jsonify({'has_next': False})

if __name__ == '__main__':
    network_ip = get_network_ip()
    # Server starting silently - access at http://localhost:5000 or http://<your-ip>:5000
    
    app.run(host='0.0.0.0', port=5000, debug=os.getenv('FLASK_ENV') == 'development')