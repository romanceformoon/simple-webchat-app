import aioredis
import jinja2
import aiohttp_jinja2
import aiohttp
import base64
from views import routes
from cryptography import fernet
from aiohttp_session import setup
from aiohttp_session.cookie_storage import EncryptedCookieStorage
import os
import pickle


async def make_app():
    app = aiohttp.web.Application()
    if os.path.exists(".secret"):
        with open(".secret", "rb") as f:
            fernet_key = pickle.load(f)
    else:
        fernet_key = fernet.Fernet.generate_key()
        with open(".secret", "wb") as f:
            pickle.dump(fernet_key, f)
    secret_key = base64.urlsafe_b64decode(fernet_key)
    setup(app, EncryptedCookieStorage(secret_key))
    app.add_routes(routes)
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('./templates/'))

    # Create a redis
    app['redis'] = await aioredis.create_redis(
        ('localhost', 6379), db=1, encoding='utf-8')

    # Initialize redis at first
    await app['redis'].delete('name')
    app['online_users'] = {}

    return app

aiohttp.web.run_app(make_app())
