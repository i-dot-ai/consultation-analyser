#!/bin/sh

venv/bin/django-admin migrate
venv/bin/django-admin compress --force --engine jinja2
exec venv/bin/gunicorn -c ./consultation_analyser/gunicorn.py consultation_analyser.wsgi
