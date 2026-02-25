from .base import *

DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'postgres',
        'USER': 'postgres',
        'PASSWORD': 'rXdkrsZWydr8Vma',
        'HOST': 'database-django-mumbai.crww4ymk2svi.ap-south-1.rds.amazonaws.com',
        'PORT': '5432',
        'CONN_MAX_AGE': 60,
    }
}


