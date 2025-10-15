"""
Gunicorn configuration for production deployment
Optimized for performance and reliability
"""
import multiprocessing
import os

# Server Socket
bind = f"0.0.0.0:{os.getenv('PORT', '5000')}"
backlog = 2048

# Worker Processes
workers = int(os.getenv('WEB_CONCURRENCY', multiprocessing.cpu_count() * 2 + 1))
worker_class = 'sync'
worker_connections = 1000
max_requests = 1000  # Restart workers after this many requests (prevents memory leaks)
max_requests_jitter = 100
timeout = 30
keepalive = 5

# Logging
accesslog = '-'  # Log to stdout
errorlog = '-'   # Log to stderr
loglevel = os.getenv('LOG_LEVEL', 'info')
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process Naming
proc_name = 'homeflix'

# Server Mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (uncomment and configure if using HTTPS)
# keyfile = '/path/to/key.pem'
# certfile = '/path/to/cert.pem'

# Server Hooks
def on_starting(server):
    """Called just before the master process is initialized."""
    server.log.info("Homeflix server is starting...")

def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    server.log.info("Homeflix server is reloading...")

def when_ready(server):
    """Called just after the server is started."""
    server.log.info("Homeflix server is ready. Accepting connections.")

def on_exit(server):
    """Called just before exiting Gunicorn."""
    server.log.info("Homeflix server is shutting down...")

# Preload application for better performance
preload_app = True

# Performance tuning
worker_tmp_dir = '/dev/shm'  # Use shared memory for better performance
