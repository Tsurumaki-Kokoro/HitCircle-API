import os
from ossapi import Ossapi

DEBUG = False

if DEBUG:
    API_KEY = "123456asdfgh"
    CLIENT_ID = 114514
    CLIENT_SECRET = "secret"
    DB_HOST = "localhost"
    DB_PORT = 3306
    DB_USER = "root"
    DB_PASSWORD = "password"
    REDIS_HOST = "localhost"
    REDIS_PORT = 6379
    REDIS_DB = 1
else:
    API_KEY = os.environ.get('API_KEY')
    CLIENT_ID = os.environ.get('OSU_CLIENT_ID')
    CLIENT_SECRET = os.environ.get('OSU_CLIENT_SECRET')
    DB_HOST = os.environ.get('DB_HOST')
    DB_PORT = os.environ.get('DB_PORT')
    DB_USER = os.environ.get('DB_USER')
    DB_PASSWORD = os.environ.get('DB_PASSWORD')
    REDIS_HOST = os.environ.get('REDIS_HOST')
    REDIS_PORT = os.environ.get('REDIS_PORT')
    REDIS_DB = os.environ.get('REDIS_DB')

osu_api = Ossapi(CLIENT_ID, CLIENT_SECRET)
