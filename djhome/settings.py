"""
Django settings for djhome project.

Generated by 'django-admin startproject' using Django 1.9.7.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.9/ref/settings/
"""

import os
import datetime
import logging.config

# SECURITY WARNING: don't run with debug turned on in production!
#set via: sudo nano /etc/environment
DEBUG = os.environ.get('DEBUG', 'true') != 'false'

# ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼
# ▼▼▼▼▼▼   SECURITY DEFINITIONS - OVERRIDE THE BELOW SETTINGS FOR YOUR SPECIFIC DEPLOYMENT; DO NOT SHARE WITH ANYONE   ▼▼▼▼▼▼
# ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'replace_with_actual_secret')
if DEBUG:
    ALLOWED_HOSTS = ['*']
else:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'yourdomain.com', ]
CORS_ORIGIN_WHITELIST = (
    'http://localhost', 'http://localhost:8000', 'http://localhost:8100', 'http://localhost:8101', 'https://yourdomain.com')      # This value should not contain a trailing dash, but calling url does require a trailing dash
ADMINS = [('Admin', 'admin@yourdomain.com'), ]
MANAGERS = ADMINS

# Be sure to setup your email backend with all relevant configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

ASTRAL_LOCATION_INFO = """Raanana_wiki,Israel,32°11'N,34°52'E,Asia/Jerusalem,48
    Raanana_google,Israel,32°18'N,34°87'E,Asia/Jerusalem,44"""
LOCATION = 'Raanana_wiki'

try:
    # A good practice is to keep all the secret data in a separate file
    from .settings_secret import *
except:
    pass
# ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲
# ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲     End of Security definitions     ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲
# ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Application definition
INSTALLED_APPS = [
    'channels',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_admin_listfilter_dropdown',
    'corsheaders',
    'django_rq',
    'taggit',
    'guardian',
    'rest_framework',
    'rest_framework.authtoken',
    'ios',
    'schedules',
]

MIDDLEWARE = [
    'log_request_id.middleware.RequestIDMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.common.BrokenLinkEmailsMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',  # this is default
    'guardian.backends.ObjectPermissionBackend',
)

SESSION_COOKIE_SAMESITE = None

CORS_ORIGIN_ALLOW_ALL = False  # not DEBUG
CORS_ALLOW_CREDENTIALS = True



#LOGIN_REDIRECT_URL = '/api/login/'
LOGIN_REDIRECT_URL = ('..')
ROOT_URLCONF = 'djhome.urls'
#APPEND_SLASH=False

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['djhome/templates'],
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

WSGI_APPLICATION = 'djhome.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'djhome.sqlite3'),
    },
}

# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

FIXTURE_DIRS = ('fixtures/',)

# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Jerusalem'

USE_I18N = True

USE_L10N = True

USE_TZ = True

TAGGIT_CASE_INSENSITIVE = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'run/static')
STATICFILES_DIRS = [
    #'djhome/static',
    #"ios/static",
    os.path.join(BASE_DIR, "djhome/static"),
    #'/var/www/static/',
]

REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly',      # removing this screwed up the channels
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': (
        #'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework_jwt.authentication.JSONWebTokenAuthentication',
    ),
    #'DEFAULT_RENDERER_CLASSES': (
    #    'rest_framework.renderers.JSONRenderer',                                # Disables the browsable API
    #),
    #'DEFAULT_METADATA_CLASS': 'rest_framework.metadata.SimpleMetadata'
}

JWT_AUTH = {
    'JWT_ALLOW_REFRESH': True,
    'JWT_VERIFY_EXPIRATION': False,     #This doesn't seem to work
    #'JWT_EXPIRATION_DELTA': datetime.timedelta(seconds=3),              #TODO: Make longer for production
    'JWT_EXPIRATION_DELTA': datetime.timedelta(days=14),
    'JWT_REFRESH_EXPIRATION_DELTA': datetime.timedelta(days=36500),     #100 years!
    'JWT_AUTH_HEADER_PREFIX': 'Bearer',
    'JWT_AUTH_COOKIE': 'JWT',
}


#redis_host = os.environ.get('REDIS_HOST', 'localhost')          #for Channels
ASGI_APPLICATION = "djhome.routing.application"
# Channel layer definitions
# http://channels.readthedocs.org/en/latest/deploying.html#setting-up-a-channel-backend
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}

# Q_CLUSTER = {
#     'name': 'djHome',
#     'workers': 1,
#     'timeout': 90,
#     'retry': 120,
#     'save_limit': 250,
#     'queue_limit': 50,
#     'catch_up': True,
#     'bulk': 1,
#     'poll': 0.2,
#     'cached': 120,
#     'orm': 'default'
# }

'''
# Celery settings
CELERY_BROKER_URL = 'amqp://guest:guest@localhost//'
#: Only add pickle to this list if your broker is secured
#: from unwanted access (see userguide/security.html)
CELERY_ACCEPT_CONTENT = ['json']
#CELERY_RESULT_BACKEND = 'db+sqlite:///results.sqlite'
CELERY_TASK_SERIALIZER = 'json'
CELERY_TASK_IGNORE_RESULT = True
CELERY_IGNORE_RESULT = True
CELERY_TIMEZONE = 'Asia/Jerusalem'
CELERYD_TIMER_PRECISION = 0.5       #not tested
CELERYD_LOG_LEVEL = "DEBUG"
CELERY_WORKER_HIJACK_ROOT_LOGGER = False
'''


PHIDGET_SERVER_FQDN = 'localhost'
PHIDGET_SERVER_PORT = '8081'
PHIDGET_SERVER_URL = 'http://' + PHIDGET_SERVER_FQDN + ':' + PHIDGET_SERVER_PORT + '/'


RQ_QUEUES = {
    'default': {
        'HOST': 'localhost',
        'PORT': 6379,
        'DB': 0,
        #'PASSWORD': 'some-password',
        'DEFAULT_TIMEOUT': 360,
    }
}
# may interfere with other apps that modifies the default admin template.
RQ_SHOW_ADMIN_LINK = True
#RQ_EXCEPTION_HANDLERS = ['path.to.my.handler'] # If you need custom exception handlers


LOGGING_CONFIG = None
#DJANGO_LOG_LEVEL = DEBUG
LOG_REQUEST_ID_HEADER = "HTTP_X_REQUEST_ID"
#LOG_REQUEST_ID_HEADER = "X-Request-ID"
GENERATE_REQUEST_ID_IF_NOT_IN_HEADER = True
REQUEST_ID_RESPONSE_HEADER = "RESPONSE_HEADER_NAME"
LOG_REQUESTS = True
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'request_id': {
            '()': 'log_request_id.filters.RequestIDFilter'
        }
    },
    'formatters': {
        'standard': {
            'format': '%(levelname)-8s [%(asctime)s] [%(request_id)s] %(name)s: %(message)s'
        },
        'simple': {
            'format': '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
        },
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
            # 'class': 'logging.handlers.RotatingFileHandler',
            # 'filename': 'log/djhome.log',
            # 'maxBytes': 1024 * 1024 * 5,  # 5 MB
            # 'backupCount': 5,
            # 'filters': ['request_id'],
            # 'formatter': 'standard',
        },
        'console': {
            'class': 'logging.StreamHandler',
            'filters': ['request_id'],
            'formatter': 'standard',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'DEBUG',
   },
   'loggers': {
       'root': {
           'handlers': ['console', 'file'],
           'level': 'DEBUG',
       },
       'django.db.backends': {
           'handlers': ['null'],  # Quiet by default!
           'propagate': False,
           'level': 'DEBUG',
       },
       'django.*': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True
        },
        'watchdog.*': {
            'level': 'ERROR',
            'handlers': ['console', 'file'],
            'propagate': True,
        },
        'watchdog': {
            'level': 'ERROR',
            'handlers': ['console', 'file'],
            'propagate': True,
        },
        'djhome.*': {
            'level': 'DEBUG',
            'handlers': ['console', 'file'],
            'propagate': True,
        },
    },
}

logging.config.dictConfig(LOGGING)
