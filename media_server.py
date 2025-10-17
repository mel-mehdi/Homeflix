from flask import Flask, render_template, request, Response, send_file, send_from_directory, abort, redirect, jsonify
import requests
import io
import logging
from database import init_db
from db_service import DatabaseService
from config import api_config, cache_config, server_config, pagination_config, get_embed_sources
from utils import cache_manager, make_api_request, measure_time
from functools import lru_cache
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.WARNING,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
# Disable Flask's default request logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# Initialize database on startup
init_db()

# Register monitoring routes
try:
    from monitoring import register_monitoring_routes
    register_monitoring_routes(app)
    logger.info("Monitoring endpoints registered: /health, /metrics, /cache/clear")
except ImportError:
    logger.warning("Monitoring module not available - health check endpoints disabled")

@lru_cache(maxsize=1000)
def get_cached_tmdb_data(url: str, params_str: str = "") -> Dict[str, Any]:
    """
    Get data from cache or fetch from TMDB with LRU cache decorator
    
    Args:
        url: TMDB API endpoint URL
        params_str: Stringified params for cache key
        
    Returns:
        JSON response as dictionary
    """
    cache_key = f"{url}_{params_str}"
    
    # Try to get from timed cache first
    cached_data = cache_manager.get('tmdb', cache_key, cache_config.TMDB_DATA)
    if cached_data is not None:
        return cached_data
    
    # Fetch from API
    headers = {'Authorization': f'Bearer {api_config.TMDB_ACCESS_TOKEN}'}
    # Parse params_str safely (it's always from str(dict) in this codebase)
    import json
    try:
        params = json.loads(params_str.replace("'", '"')) if params_str else None
    except (json.JSONDecodeError, ValueError):
        params = None
    
    try:
        data = make_api_request(url, headers=headers, params=params)
        cache_manager.set('tmdb', cache_key, data)
        return data
    except Exception as e:
        logger.error(f"Error fetching TMDB data from {url}: {e}")
        return {}

def _populate_image_cache(items: List[Dict[str, Any]], media_type: str):
    """
    Populate poster and backdrop cache from database results
    Optimized to reduce database queries
    
    Args:
        items: List of movie/TV show dictionaries
        media_type: 'movie', 'tv', or 'mixed'
    """
    if not items:
        return

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
            try:
                if current_type == 'movie':
                    db_item = db_service.get_movie_by_tmdb_id(tmdb_id)
                else:
                    db_item = db_service.get_tvshow_by_tmdb_id(tmdb_id)

                if not db_item:
                    continue

                # Populate caches
                if getattr(db_item, 'poster_path', None):
                    cache_manager.set('posters', f"{current_type}_{tmdb_id}", db_item.poster_path)

                if getattr(db_item, 'backdrop_path', None):
                    cache_manager.set('backdrops', f"{current_type}_{tmdb_id}", db_item.backdrop_path)
            except Exception as e:
                logger.error(f"Error populating cache for {current_type} {tmdb_id}: {e}")


def _allows_framing(headers: Dict[str, str]) -> bool:
    """Return True if the response headers indicate the resource can be framed.

    Checks X-Frame-Options and Content-Security-Policy frame-ancestors.
    """
    xfo = headers.get('x-frame-options') or headers.get('X-Frame-Options')
    if xfo:
        xfo_val = xfo.lower()
        if 'deny' in xfo_val or 'sameorigin' in xfo_val:
            return False
    csp = headers.get('content-security-policy') or headers.get('Content-Security-Policy')
    if csp and 'frame-ancestors' in csp:
        try:
            # Parse frame-ancestors directive
            parts = [p.strip() for p in csp.split(';')]
            fa = [p for p in parts if p.startswith('frame-ancestors')]
            if fa:
                fa_vals = fa[0].split()[1:]
                # If frame-ancestors contains * or 'self', allow; otherwise block
                if any(v == '*' or "'self'" in v or 'self' in v for v in fa_vals):
                    return True
                return False
        except Exception:
            # If parsing fails, be conservative and disallow
            return False
    return True


@app.route('/embed_check', methods=['POST'])
def embed_check():
    """Simple endpoint to test whether an embed url allows framing.

    Expects JSON: { "url": "https://..." }
    Returns JSON: { "url": "...", "allows": true/false, "status_code": int }
    """
    try:
        data = request.get_json(force=True)
        url = data.get('url')
        if not url:
            return jsonify({'error': 'missing url'}), 400

        # Use HEAD first to be lighter; follow redirects but capture final headers
        try:
            resp = requests.head(url, allow_redirects=True, timeout=5)
        except Exception:
            # Fallback to GET if HEAD fails (some hosts don't support HEAD)
            resp = requests.get(url, allow_redirects=True, timeout=5)

        allows = _allows_framing({k.lower(): v for k, v in resp.headers.items()})
        return jsonify({'url': url, 'allows': allows, 'status_code': resp.status_code})
    except Exception as e:
        logger.error(f"Error in embed_check: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/favicon.ico')
def favicon():
    """Handle favicon requests"""
    return '', 204

@app.route('/')
@measure_time
def index():
    """Display all movies and series - optimized with caching"""
    movie_page = int(request.args.get('movie_page', 1))
    series_page = int(request.args.get('series_page', 1))
    try:
        # Use database instead of API calls
        with DatabaseService() as db_service:
            movies = db_service.get_latest_movies(movie_page, pagination_config.DEFAULT_PER_PAGE)
            series = db_service.get_latest_tvshows(series_page, pagination_config.DEFAULT_PER_PAGE)
            trending_movies = db_service.get_trending_movies(pagination_config.TRENDING_LIMIT)
            trending_series = db_service.get_trending_tvshows(pagination_config.TRENDING_LIMIT)
            my_list = db_service.get_my_list()
            continue_watching = db_service.get_continue_watching(limit=10)  # Get continue watching
        
        # Populate image caches from database results
        _populate_image_cache(movies, 'movie')
        _populate_image_cache(series, 'tv')
        _populate_image_cache(trending_movies, 'movie')
        _populate_image_cache(trending_series, 'tv')
        if my_list:
            _populate_image_cache(my_list, 'mixed')
        if continue_watching:
            _populate_image_cache(continue_watching, 'mixed')
        
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
                             backdrop_urls=backdrop_urls, my_list=my_list, 
                             continue_watching=continue_watching)
    except Exception as e:
        logger.error(f"Error in index: {e}")
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
@measure_time
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
        
        # Generate multiple embed sources using config
        embed_sources = get_embed_sources('movie', tmdb_id or imdb_id)
        embed_url = embed_sources[0] if embed_sources else ""
        
        return render_template('player.html', 
                             embed_url=embed_url, 
                             embed_sources=embed_sources,
                             title=title, 
                             type='movie',
                             imdb_id=imdb_id,
                             tmdb_id=tmdb_id)
    except Exception as e:
        logger.error(f"Error in watch_movie: {e}")
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
        
        # Generate multiple embed sources using config
        embed_sources = get_embed_sources('tv', tmdb_id or imdb_id)
        embed_url = embed_sources[0] if embed_sources else ""
        
        return render_template('player.html', 
                             embed_url=embed_url, 
                             embed_sources=embed_sources,
                             title=title, 
                             type='series',
                             imdb_id=imdb_id,
                             tmdb_id=tmdb_id)
    except Exception as e:
        logger.error(f"Error in watch_series: {e}")
        return f"Error: {e}", 500
        
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
@measure_time
def series_details(imdb_id):
    """Display series details with seasons and episodes"""
    try:
        # Fetch series details from database first
        with DatabaseService() as db_service:
            series = db_service.get_tvshow_by_imdb_id(imdb_id)
            my_list = db_service.get_my_list()
        
        if not series:
            # If not in database, try to fetch from TMDB using IMDB ID
            find_url = f"{api_config.TMDB_BASE_URL}/find/{imdb_id}"
            params = {'external_source': 'imdb_id'}
            params_str = str(params)
            find_data = get_cached_tmdb_data(find_url, params_str)
            
            tv_results = find_data.get('tv_results', [])
            if not tv_results:
                return "Series not found", 404
            
            # Get the TMDB ID from the results
            tmdb_id = tv_results[0].get('id')
            
            # Fetch full TV show details
            tv_url = f"{api_config.TMDB_BASE_URL}/tv/{tmdb_id}"
            tv_data = get_cached_tmdb_data(tv_url, "")
            
            # Create series_dict from TMDB data
            series_dict = {
                'title': tv_data.get('name'),
                'overview': tv_data.get('overview'),
                'poster_path': tv_data.get('poster_path'),
                'backdrop_path': tv_data.get('backdrop_path'),
                'first_air_date': tv_data.get('first_air_date'),
                'vote_average': tv_data.get('vote_average'),
                'vote_count': tv_data.get('vote_count'),
                'popularity': tv_data.get('popularity'),
                'tmdb_id': tmdb_id,
                'imdb_id': imdb_id
            }
        else:
            series_dict = series.to_dict()
        
        tmdb_id = series_dict.get('tmdb_id')
        
        # Fetch detailed information from TMDB
        if tmdb_id:
            # Get full series details
            url = f"{api_config.TMDB_BASE_URL}/tv/{tmdb_id}"
            series_data = get_cached_tmdb_data(url, "")
            
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
            credits_url = f"{api_config.TMDB_BASE_URL}/tv/{tmdb_id}/credits"
            credits_data = get_cached_tmdb_data(credits_url, "")
            cast = credits_data.get('cast', [])[:10]  # Top 10 cast members
            
            # Get content rating
            content_ratings_url = f"{api_config.TMDB_BASE_URL}/tv/{tmdb_id}/content_ratings"
            ratings_data = get_cached_tmdb_data(content_ratings_url, "")
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
        logger.error(f"Error in series_details: {e}")
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
            url = f"{api_config.TMDB_BASE_URL}/movie/{tmdb_id}"
            headers = {'Authorization': f'Bearer {api_config.TMDB_ACCESS_TOKEN}'}
            movie_data = get_cached_tmdb_data(url, "")
            
            # Get cast information
            credits_url = f"{api_config.TMDB_BASE_URL}/movie/{tmdb_id}/credits"
            credits_data = get_cached_tmdb_data(credits_url, "")
            cast = credits_data.get('cast', [])[:10]  # Top 10 cast members
            crew = credits_data.get('crew', [])
            
            # Get director
            director = next((person for person in crew if person.get('job') == 'Director'), None)
            
            # Get content rating
            releases_url = f"{api_config.TMDB_BASE_URL}/movie/{tmdb_id}/release_dates"
            releases_data = get_cached_tmdb_data(releases_url, "")
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
            # If not in database, try to fetch from TMDB using IMDB ID
            find_url = f"{api_config.TMDB_BASE_URL}/find/{imdb_id}"
            params = {'external_source': 'imdb_id'}
            params_str = str(params)
            find_data = get_cached_tmdb_data(find_url, params_str)
            
            tv_results = find_data.get('tv_results', [])
            if not tv_results:
                return "Series not found", 404
            
            tmdb_id = tv_results[0].get('id')
            series_title = tv_results[0].get('name')
        else:
            tmdb_id = series.tmdb_id
            series_title = series.title
        
        # Fetch season details from TMDB
        if tmdb_id:
            url = f"{api_config.TMDB_BASE_URL}/tv/{tmdb_id}/season/{season_number}"
            season_data = get_cached_tmdb_data(url, "")
            
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
            
            # Create series dict for template
            if series:
                series_dict = series.to_dict()
            else:
                series_dict = {
                    'title': series_title,
                    'tmdb_id': tmdb_id,
                    'imdb_id': imdb_id
                }
            
            return render_template('season_details.html', 
                                 series=series_dict, 
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
            # If not in database, try to fetch from TMDB using IMDB ID
            find_url = f"{api_config.TMDB_BASE_URL}/find/{imdb_id}"
            params = {'external_source': 'imdb_id'}
            params_str = str(params)
            find_data = get_cached_tmdb_data(find_url, params_str)
            
            tv_results = find_data.get('tv_results', [])
            if not tv_results:
                return "Series not found", 404
            
            tmdb_id = tv_results[0].get('id')
            title = tv_results[0].get('name')
        else:
            tmdb_id = series.tmdb_id
            title = series.title
        
        # Generate multiple embed sources using config
        embed_sources = get_embed_sources('episode', tmdb_id or imdb_id, season_number, episode_number)
        embed_url = embed_sources[0] if embed_sources else ""
        
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
        logger.error(f"Error in watch_episode: {e}")
        return f"Error: {e}", 500

@app.route('/css/<filename>')
def serve_css(filename):
    """Serve CSS files with caching headers"""
    try:
        response = send_from_directory(server_config.CSS_FOLDER, filename)
        # Add caching headers for better performance
        response.headers['Cache-Control'] = 'public, max-age=3600'
        return response
    except Exception as e:
        logger.error(f"Error serving CSS {filename}: {e}")
        abort(404)

@app.route('/poster/<media_type>/<int:tmdb_id>')
def get_poster(media_type, tmdb_id):
    """Serve poster image with caching"""
    if not api_config.TMDB_ACCESS_TOKEN:
        svg = '''<svg width="300" height="450" xmlns="http://www.w3.org/2000/svg">
        <rect width="300" height="450" fill="#333"/>
        <text x="150" y="225" text-anchor="middle" fill="white" font-size="20">No Poster</text>
        </svg>'''
        return Response(svg, mimetype='image/svg+xml')
    
    key = f"{media_type}_{tmdb_id}"
    poster_path = cache_manager.get('posters', key, cache_config.POSTER)
    
    # If not in cache, try to get from database
    if not poster_path:
        try:
            with DatabaseService() as db_service:
                if media_type == 'movie':
                    db_item = db_service.get_movie_by_tmdb_id(tmdb_id)
                else:
                    db_item = db_service.get_tvshow_by_tmdb_id(tmdb_id)
                
                if db_item and hasattr(db_item, 'poster_path') and db_item.poster_path:
                    poster_path = db_item.poster_path
                    cache_manager.set('posters', key, poster_path)
        except Exception as e:
            logger.error(f"Error fetching poster from database: {e}")
    
    if not poster_path:
        abort(404)
    
    try:
        image_url = f"{api_config.TMDB_IMAGE_BASE_URL}{poster_path}"
        image_response = requests.get(image_url, timeout=api_config.REQUEST_TIMEOUT)
        image_response.raise_for_status()
        
        return send_file(
            io.BytesIO(image_response.content),
            mimetype=image_response.headers.get('content-type', 'image/jpeg')
        )
    except Exception as e:
        logger.error(f"Error proxying poster: {e}")
        abort(404)

@app.route('/backdrop/<media_type>/<int:tmdb_id>')
def get_backdrop(media_type, tmdb_id):
    """Serve backdrop image with caching"""
    if not api_config.TMDB_ACCESS_TOKEN:
        svg = '''<svg width="500" height="281" xmlns="http://www.w3.org/2000/svg">
        <rect width="500" height="281" fill="#333"/>
        <text x="250" y="140" text-anchor="middle" fill="white" font-size="20">No Backdrop</text>
        </svg>'''
        return Response(svg, mimetype='image/svg+xml')
    
    key = f"{media_type}_{tmdb_id}"
    backdrop_path = cache_manager.get('backdrops', key, cache_config.BACKDROP)
    
    # If not in cache, try to get from database first
    if not backdrop_path:
        try:
            with DatabaseService() as db_service:
                if media_type == 'movie':
                    db_item = db_service.get_movie_by_tmdb_id(tmdb_id)
                else:
                    db_item = db_service.get_tvshow_by_tmdb_id(tmdb_id)
                
                if db_item and hasattr(db_item, 'backdrop_path') and db_item.backdrop_path:
                    backdrop_path = db_item.backdrop_path
                    cache_manager.set('backdrops', key, backdrop_path)
        except Exception as e:
            logger.error(f"Error fetching backdrop from database: {e}")
    
    # If still not found, try to fetch from TMDB API
    if not backdrop_path:
        try:
            headers = {
                "Authorization": f"Bearer {api_config.TMDB_ACCESS_TOKEN}",
                "accept": "application/json"
            }
            tmdb_url = f"https://api.themoviedb.org/3/{media_type}/{tmdb_id}"
            response = requests.get(tmdb_url, headers=headers, timeout=api_config.REQUEST_TIMEOUT)
            
            if response.ok:
                data = response.json()
                backdrop_path = data.get('backdrop_path')
                
                if backdrop_path:
                    # Cache the backdrop path
                    cache_manager.set('backdrops', key, backdrop_path)
                else:
                    # No backdrop available, return placeholder
                    logger.warning(f"No backdrop available for {media_type}/{tmdb_id}")
                    svg = '''<svg width="500" height="281" xmlns="http://www.w3.org/2000/svg">
                    <rect width="500" height="281" fill="#333"/>
                    <text x="250" y="140" text-anchor="middle" fill="white" font-size="16">No Backdrop Available</text>
                    </svg>'''
                    return Response(svg, mimetype='image/svg+xml')
            else:
                # TMDB API error, return placeholder
                logger.warning(f"TMDB API error for {media_type}/{tmdb_id}: {response.status_code}")
                svg = '''<svg width="500" height="281" xmlns="http://www.w3.org/2000/svg">
                <rect width="500" height="281" fill="#333"/>
                <text x="250" y="140" text-anchor="middle" fill="white" font-size="16">Backdrop Unavailable</text>
                </svg>'''
                return Response(svg, mimetype='image/svg+xml')
        except Exception as e:
            logger.error(f"Error fetching backdrop metadata from TMDB: {e}")
            # Return placeholder instead of aborting
            svg = '''<svg width="500" height="281" xmlns="http://www.w3.org/2000/svg">
            <rect width="500" height="281" fill="#333"/>
            <text x="250" y="140" text-anchor="middle" fill="white" font-size="16">Backdrop Error</text>
            </svg>'''
            return Response(svg, mimetype='image/svg+xml')
    
    # Now fetch the actual image
    try:
        image_url = f"{api_config.TMDB_BACKDROP_BASE_URL}{backdrop_path}"
        image_response = requests.get(image_url, timeout=api_config.REQUEST_TIMEOUT)
        image_response.raise_for_status()
        
        return send_file(
            io.BytesIO(image_response.content),
            mimetype=image_response.headers.get('content-type', 'image/jpeg')
        )
    except Exception as e:
        logger.error(f"Error proxying backdrop image for {media_type}/{tmdb_id}: {e}")
        # Return placeholder instead of aborting
        svg = '''<svg width="500" height="281" xmlns="http://www.w3.org/2000/svg">
        <rect width="500" height="281" fill="#333"/>
        <text x="250" y="140" text-anchor="middle" fill="white" font-size="16">Image Unavailable</text>
        </svg>'''
        return Response(svg, mimetype='image/svg+xml')

def search_tmdb_movies(query, page=1):
    """Search movies using TMDB API"""
    try:
        url = f"{api_config.TMDB_BASE_URL}/search/movie"
        params = {'query': query, 'page': page}
        data = get_cached_tmdb_data(url, str(params))
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
                    cache_manager.set('posters', f"movie_{movie['tmdb_id']}", movie['poster_path'])
                if movie.get('backdrop_path'):
                    cache_manager.set('backdrops', f"movie_{movie['tmdb_id']}", movie['backdrop_path'])
                filtered_movies.append(movie)
        return filtered_movies
    except Exception as e:
        logger.error(f" searching TMDB movies: {e}")
        return []

def search_tmdb_series(query, page=1):
    """Search TV series using TMDB API"""
    try:
        url = f"{api_config.TMDB_BASE_URL}/search/tv"
        params = {'query': query, 'page': page}
        data = get_cached_tmdb_data(url, str(params))
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
                    cache_manager.set('posters', f"tv_{show['tmdb_id']}", show['poster_path'])
                if show.get('backdrop_path'):
                    cache_manager.set('backdrops', f"tv_{show['tmdb_id']}", show['backdrop_path'])
                filtered_series.append(show)
        return filtered_series
    except Exception as e:
        logger.error(f" searching TMDB series: {e}")
        return []

@lru_cache(maxsize=500)
def get_imdb_id(tmdb_id: int, media_type: str) -> Optional[str]:
    """
    Get IMDB ID from TMDB ID with caching
    
    Args:
        tmdb_id: TMDB ID
        media_type: 'movie' or 'tv'
        
    Returns:
        IMDB ID or None if not found
    """
    try:
        url = f"{api_config.TMDB_BASE_URL}/{media_type}/{tmdb_id}/external_ids"
        data = get_cached_tmdb_data(url, "")
        return data.get('imdb_id')
    except Exception as e:
        logger.error(f"Error getting IMDB ID for {tmdb_id}: {e}")
        return None

@lru_cache(maxsize=500)
def get_imdb_id(tmdb_id: int, media_type: str) -> Optional[str]:
    """
    Get IMDB ID from TMDB ID with caching
    
    Args:
        tmdb_id: TMDB ID
        media_type: 'movie' or 'tv'
        
    Returns:
        IMDB ID or None if not found
    """
    try:
        url = f"{api_config.TMDB_BASE_URL}/{media_type}/{tmdb_id}/external_ids"
        data = get_cached_tmdb_data(url, "")
        return data.get('imdb_id')
    except Exception as e:
        logger.error(f"Error getting IMDB ID for {tmdb_id}: {e}")
        return None

@lru_cache(maxsize=200)
def get_movie_details(imdb_id: str) -> Optional[Dict[str, Any]]:
    """
    Get movie details from TMDB by IMDB ID with caching
    
    Args:
        imdb_id: IMDB ID
        
    Returns:
        Movie details dictionary or None
    """
    try:
        url = f"{api_config.TMDB_BASE_URL}/find/{imdb_id}"
        params_str = str({'external_source': 'imdb_id'})
        data = get_cached_tmdb_data(url, params_str)
        
        if data.get('movie_results'):
            movie = data['movie_results'][0]
            movie['tmdb_id'] = movie['id']
            return movie
        return None
    except Exception as e:
        logger.error(f"Error getting movie details for {imdb_id}: {e}")
        return None


@lru_cache(maxsize=200)
def get_series_details(imdb_id: str) -> Optional[Dict[str, Any]]:
    """
    Get series details from TMDB by IMDB ID with caching
    
    Args:
        imdb_id: IMDB ID
        
    Returns:
        Series details dictionary or None
    """
    try:
        url = f"{api_config.TMDB_BASE_URL}/find/{imdb_id}"
        params_str = str({'external_source': 'imdb_id'})
        data = get_cached_tmdb_data(url, params_str)
        
        if data.get('tv_results'):
            series = data['tv_results'][0]
            series['tmdb_id'] = series['id']
            return series
        return None
    except Exception as e:
        logger.error(f"Error getting series details for {imdb_id}: {e}")
        return None

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
        url = f"{api_config.TMDB_BASE_URL}/tv/{tmdb_id}/season/{season}"
        season_data = get_cached_tmdb_data(url, "")
        
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
                'next_still_path': f"{api_config.TMDB_IMAGE_BASE_URL}{episode_data['still_path']}" if episode_data.get('still_path') else None
            })
        else:
            # Check if there's a next season
            next_season = season + 1
            try:
                url = f"{api_config.TMDB_BASE_URL}/tv/{tmdb_id}/season/{next_season}"
                next_season_data = get_cached_tmdb_data(url, "")
                
                if next_season_data.get('episodes'):
                    first_episode = next_season_data['episodes'][0]
                    return jsonify({
                        'has_next': True,
                        'next_season': next_season,
                        'next_episode': 1,
                        'next_title': first_episode.get('name', 'Episode 1'),
                        'next_overview': first_episode.get('overview', ''),
                        'next_still_path': f"{api_config.TMDB_IMAGE_BASE_URL}{first_episode['still_path']}" if first_episode.get('still_path') else None
                    })
            except:
                pass
        
        return jsonify({'has_next': False})
        
    except Exception as e:
        logger.error(f"Error getting next episode for {imdb_id} S{season}E{episode}: {e}")
        return jsonify({'has_next': False})

@app.route('/api/search_suggestions')
def search_suggestions():
    """Get search suggestions as user types - ULTRA FAST FTS search"""
    query = request.args.get('q', '').strip()
    if not query or len(query) < 2:
        return jsonify({'results': []})
    
    # For very short queries (2 chars), require exact start match for speed
    if len(query) == 2:
        per_page = 2  # Reduce results for very short queries
    else:
        per_page = 3
    
    try:
        suggestions = []
        
        # Search local database using FTS for instant results
        with DatabaseService() as db_service:
            movies = db_service.search_movies(query, page=1, per_page=per_page)
            series = db_service.search_tvshows(query, page=1, per_page=per_page)
        
        # Add movies to suggestions
        for movie in movies:
            suggestions.append({
                'id': movie.get('imdb_id'),
                'title': movie.get('title'),
                'type': 'movie',
                'year': movie.get('release_date', '')[:4] if movie.get('release_date') else '',
                'poster_url': movie.get('poster_url'),
                'url': f"/movie/{movie.get('imdb_id')}"
            })
        
        # Add series to suggestions
        for show in series:
            suggestions.append({
                'id': show.get('imdb_id'),
                'title': show.get('title'),
                'type': 'series',
                'year': show.get('first_air_date', '')[:4] if show.get('first_air_date') else '',
                'poster_url': show.get('poster_url'),
                'url': f"/series/{show.get('imdb_id')}"
            })
        
        # Sort by relevance (title starts with query) and limit to 6 results
        suggestions.sort(key=lambda x: (
            not x['title'].lower().startswith(query.lower()),  # Prioritize starts-with matches
            x['title'].lower()  # Then alphabetically
        ))
        
        return jsonify({'results': suggestions[:6]})
        
    except Exception as e:
        logger.error(f"Error in search_suggestions: {e}")
        return jsonify({'results': []})



if __name__ == "__main__":
    app.run(
        host=server_config.HOST,
        port=server_config.PORT,
        debug=server_config.DEBUG,
        threaded=server_config.THREADED
    )
