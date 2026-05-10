# gunicorn.conf.py
workers    = 2
timeout    = 120        # give workers 2 minutes
keepalive  = 5
worker_class = "sync"
bind       = "0.0.0.0:10000"
