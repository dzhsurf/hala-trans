# gunicorn_config.py
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
bind = "0.0.0.0:8000"
loglevel = "info"
accesslog = "-"
errorlog = "-"
