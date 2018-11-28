import os
from core.settings.base import BASE_DIR

LOG_ROOT = BASE_DIR +'/logs'
LOG_SIZE = 1000000000
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,

    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'null': {
            'level':'DEBUG',
            'class':'logging.NullHandler',
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'logfile-django': {
            'level':'DEBUG',
            'class':'logging.handlers.RotatingFileHandler',
            'filename': LOG_ROOT + "/application_main.log",
            'maxBytes': LOG_SIZE,
            'backupCount': 2,
            'formatter': 'verbose',
        },
        'logfile-error': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_ROOT + "/application_error.log",
            'maxBytes': LOG_SIZE,
            'backupCount': 2,
            'formatter': 'verbose',
        },
        'logfile-template': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_ROOT + "/template.log",
            'maxBytes': LOG_SIZE,
            'backupCount': 2,
            'formatter': 'verbose',
        }
    },
    'loggers': {
        'django.template': {
            'handlers': ['logfile-template'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['logfile-error', 'console'],
            'level': 'ERROR',
        },
        'django': {
            'handlers': ['null', ],
        },
        'py.warnings': {
            'handlers': ['null', ],
        },
        '': {
            'handlers': ['logfile-django', 'logfile-error'],
            'level': "DEBUG",
        },
    },
    'formatters': {
        'verbose': {
            'format': '%(asctime)s %(module)s %(name)-1s:%(lineno)d %(levelname)-5s %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(name)-1s:%(lineno)d %(message)s'
        },
    },

    'logfile': {
        'level':'DEBUG',
        'class':'logging.handlers.RotatingFileHandler',
        'filename': LOG_ROOT + "/logfile",
        'maxBytes': 10000000,
        'backupCount': 5,
        'formatter': 'verbose',
    },
}