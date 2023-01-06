# -*- coding: utf-8 -*-

"""Sample of configuration file required for LinuFy"""

# SQL settings -  You can get this info from your web host
SQLALCHEMY_DATABASE_URI = 'mysql://USERNAME:PASSWORD@HOSTNAME/DATABASE'

# Change these to different unique phrases!
SECRET_KEY = 'YOUR-SECRET-KEY'

BABEL_DEFAULT_LOCALE = 'en'
LANGUAGES = ['en', 'fr']

# For developers: debugging mode.
DEBUG = False