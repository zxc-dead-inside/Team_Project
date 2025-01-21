import os
from pathlib import Path

from dotenv import load_dotenv

from split_settings.tools import include


load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY')

DEBUG = os.environ.get('DEBUG', False) == 'True'
IS_DOCKERED = os.environ.get('IS_DOCKERED', False) == 'True'


ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]',]

ROOT_URLCONF = 'config.urls'

WSGI_APPLICATION = 'config.wsgi.application'

include(
    'components/applications.py',
    'components/middlewares.py',
    'components/database.py',
    'components/templates.py',
    'components/validators.py'
)

LANGUAGE_CODE = 'ru-RU'
LOCALE_PATHS = ['movies/locale']

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

if IS_DOCKERED:
    STATIC_URL = '/static/'
    STATIC_ROOT = os.path.join(BASE_DIR, 'static')
else:
    STATIC_URL = 'static/'


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CORS_ORIGIN_ALLOW_ALL = True
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',
    "http://127.0.0.1:8000"
]

CORS_ALLOWED_ORIGINS = [
    "http://127.0.0.1:8000",
    "http://localhost:8000",
]
CORS_URLS_REGEX = r'^/api/.*$'
