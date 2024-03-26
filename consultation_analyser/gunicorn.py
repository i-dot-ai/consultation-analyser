import environ

environ.Env.read_env(".env", overwrite=False)
env = environ.Env()

workers = env("GUNICORN_WORKERS", default=5)
bind = "0.0.0.0:8000"
accesslog = "-"
errorlog = "-"
reload = env("ENVIRONMENT").upper() == "LOCAL"
