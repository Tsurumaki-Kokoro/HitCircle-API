import os
from ossapi import Ossapi

DEBUG = False
if DEBUG:
    API_KEY = "123456asdfgh"
else:
    API_KEY = os.environ.get('API_KEY')

if DEBUG:
    CLIENT_ID = 114514
    CLIENT_SECRET = "secret"
else:
    CLIENT_ID = os.environ.get('OSU_CLIENT_ID')
    CLIENT_SECRET = os.environ.get('OSU_CLIENT_SECRET')

osu_api = Ossapi(CLIENT_ID, CLIENT_SECRET)
