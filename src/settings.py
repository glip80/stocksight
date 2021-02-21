import os
# settings.py

PRODUCTION_MODE=os.getenv('APP_ENV', 'development') == 'production'
if PRODUCTION_MODE:
    import django_heroku
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.config()
    }
    # , conn_max_age=600, ssl_require=True
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'sqlite.db',
        }
    }
    

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

INSTALLED_APPS = (
    'data',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    )

MIDDLEWARE = [
    # 'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    # 'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# TEMPLATES = [
#     'django.template.backends.django.DjangoTemplates'
# ]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

ALLOWED_HOSTS = [
    '*'
]

ROOT_URLCONF = 'urls'

DEBUG = True

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(PROJECT_ROOT, 'static')

SECRET_KEY = 'REPLACE_ME'

if PRODUCTION_MODE:
    django_heroku.settings(locals())