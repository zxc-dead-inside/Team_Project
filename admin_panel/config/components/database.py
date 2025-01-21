import os


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB'),
        'USER': os.environ.get('POSTGRES_USER'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD'),
        'HOST': os.environ.get('SQL_HOST', '127.0.0.1'),
        'PORT': os.environ.get('SQL_PORT', 5432),
        'OPTIONS': {
            'options': os.environ.get('SQL_OPTIONS')
        }
    }
}
