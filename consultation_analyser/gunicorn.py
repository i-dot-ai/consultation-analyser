import os

workers = os.getenv("GUNICORN_WORKERS", default=5)
bind = "0.0.0.0:8000"
accesslog = "-"
errorlog = "-"
reload = os.getenv("GUNICORN_RELOAD", default=True)
