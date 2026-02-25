from .base import *

DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'localhost']



DATABASES = {
    'default': {
       'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'postgres',
        'USER': 'postgres.tqwopngrndmxjdwalrjk',
        'PASSWORD': 'm3Su5?eP+SgKtU9',  # Your decoded password
        'HOST': 'aws-1-ap-northeast-1.pooler.supabase.com',  # Connection pooler
        'PORT': '5432',  # Or 6543 for connection pooler
       'OPTIONS': {
           'sslmode': 'require',
       },
    }
}

