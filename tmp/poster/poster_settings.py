from config.settings import *
from pathlib import Path
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': Path(__file__).with_name('poster-demo.sqlite3')}}
DEBUG = True
BACKGROUND_MODE = 'database'
DJANGO_LOCAL_WORKER = False
CSRF_TRUSTED_ORIGINS = ['http://127.0.0.1:5188']
