# Make this unique, and don't share it with anybody.

import os,sys

try:
    exec(open("[path to django-sensitive-data file]").read())
except:
    print("Error with LOCAL_EXTRA_SETTINGS")
    sys.exit(1)

DEBUG = True