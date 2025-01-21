DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PRT_APPS = [
    'corsheaders',
]

LOCAL_APPS = [
    'movies.apps.MoviesConfig',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PRT_APPS + LOCAL_APPS
