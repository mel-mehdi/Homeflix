"""
Performance monitoring and health check endpoints
Track application performance and system health
"""
from flask import jsonify
import psutil
import time
from datetime import datetime
from utils import cache_manager

# Store startup time
startup_time = time.time()


def get_system_stats():
    """Get current system resource usage"""
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return {
        'cpu_percent': cpu_percent,
        'memory_percent': memory.percent,
        'memory_used_mb': memory.used / (1024 * 1024),
        'memory_total_mb': memory.total / (1024 * 1024),
        'disk_percent': disk.percent,
        'disk_used_gb': disk.used / (1024 * 1024 * 1024),
        'disk_total_gb': disk.total / (1024 * 1024 * 1024),
    }


def get_cache_stats():
    """Get cache statistics"""
    return {
        'total_items': cache_manager.size(),
        'tmdb_cache_size': cache_manager.size('tmdb'),
        'posters_cache_size': cache_manager.size('posters'),
        'backdrops_cache_size': cache_manager.size('backdrops'),
    }


def get_uptime():
    """Get server uptime"""
    uptime_seconds = time.time() - startup_time
    uptime_hours = uptime_seconds / 3600
    return {
        'seconds': int(uptime_seconds),
        'hours': round(uptime_hours, 2),
        'started_at': datetime.fromtimestamp(startup_time).isoformat(),
    }


def register_monitoring_routes(app):
    """Register monitoring and health check routes"""
    
    @app.route('/health')
    def health_check():
        """Basic health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'uptime': get_uptime(),
        })
    
    @app.route('/metrics')
    def metrics():
        """Detailed application metrics"""
        try:
            system_stats = get_system_stats()
            cache_stats = get_cache_stats()
            uptime = get_uptime()
            
            return jsonify({
                'status': 'ok',
                'timestamp': datetime.utcnow().isoformat(),
                'uptime': uptime,
                'system': system_stats,
                'cache': cache_stats,
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'error': str(e),
            }), 500
    
    @app.route('/cache/clear')
    def clear_cache():
        """Clear all caches (admin endpoint)"""
        try:
            cache_manager.clear()
            return jsonify({
                'status': 'success',
                'message': 'All caches cleared',
                'timestamp': datetime.utcnow().isoformat(),
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'error': str(e),
            }), 500
    
    return app
