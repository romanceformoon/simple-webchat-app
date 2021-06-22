import asyncio
import aioredis
import jinja2
import aiohttp_jinja2
import aiohttp
from views import *


async def make_app():
    app = aiohttp.web.Application()
    app.add_routes(routes)
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('./templates/'))

    # Create a redis
    app['redis'] = await aioredis.create_redis(('localhost', 6379), db=1, encoding='utf-8')

    # Initialize redis at first
    await app['redis'].delete('name') 
    app['online_users'] = {}

    return app

aiohttp.web.run_app(make_app())
