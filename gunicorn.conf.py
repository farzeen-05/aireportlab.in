# gunicorn.conf.py — optimized for Render free tier (512MB RAM)
workers          = 1          # single worker saves ~120MB vs 2 workers
threads          = 2          # handle concurrency with threads instead
timeout          = 120        # 2 min — covers large file processing
keepalive        = 5
worker_class     = "sync"
bind             = "0.0.0.0:10000"
max_requests     = 50         # restart worker every 50 requests — prevents memory leaks
max_requests_jitter = 10      # randomize restart to avoid all workers restarting at once
preload_app      = False      # don't preload — saves startup RAM
