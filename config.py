import aiohttp

DB_URL = 'postgresql://postgres:123@localhost:5432/parser' 
BOT_TOKEN = '1631262089:AAEPH9EE4Kh8yBUgRFOVlbcMU5z99_tv4b4' 
OLX_TOKEN = 'Bearer 4e0b662ad622f7c550fcee5c9c34b5c80ac8553d' 
ADMIN_USERNAME = '@buratinosoft' 
ADMINS = (,)  # если ид один, то запятая после ид ОБЯЗАТЕЛЬНА
session = aiohttp.ClientSession()
