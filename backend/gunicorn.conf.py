import os


bind = os.getenv("GUNICORN_BIND", "unix:/run/juno-kim/gunicorn.sock")
workers = int(os.getenv("GUNICORN_WORKERS", "2"))
worker_class = "gthread"
threads = int(os.getenv("GUNICORN_THREADS", "2"))
timeout = 60
graceful_timeout = 30
keepalive = 5

# The socket is writable by the service group (www-data) and inaccessible to others.
umask = 0o007

accesslog = "-"
errorlog = "-"
capture_output = True
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "info")

# Periodic worker recycling limits the impact of slow memory growth.
max_requests = 1000
max_requests_jitter = 100
