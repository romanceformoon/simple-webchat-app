import asyncio
import random
import jinja2
import aiohttp_jinja2
import aiohttp


routes = aiohttp.web.RouteTableDef()

def generateRandomName():
    return "Anonymous" + str(random.randint(0, 9999))

@routes.get('/')
async def index(request):
    r = request.app['redis']
    users = request.app['online_users']
    ws = aiohttp.web.WebSocketResponse()
    # Check if websocket can be started.
    if not ws.can_prepare(request).ok:
        return aiohttp_jinja2.render_template('index.html', request, None)
    # Start websocket.
    # After the call you can use websocket methods.
    await ws.prepare(request)
    
    nickname = generateRandomName()
    count = int(await r.zcard('name'))
    await r.zadd('name', count + 1, nickname)
    name_list = await r.zrange('name', 0, -1)
    print(name_list)

    users[nickname] = ws

    for _ws in users.values():
        await _ws.send_json({"type": "user", "nickname": nickname, "name_list": name_list})
    
    while True:
        msg = await ws.receive()

        if msg.type == aiohttp.WSMsgType.TEXT:
            msg_count = int(await r.zcard('name'))
            for _ws in users.values():
                await _ws.send_json({"type": "received", "nickname": nickname, "message": msg.data})
        elif msg.type == aiohttp.WSMsgType.CLOSE:
            for _ws in users.values():
                if ws != _ws:
                    await _ws.send_json({"type": "disconnect", "nickname": nickname, "message": "Disconnected", "name_list": name_list})
            break
        elif msg.type == aiohttp.WSMsgType.ERROR:
            for _ws in user_list.values():
                if ws != _ws:
                    await _ws.send_json({"type": "disconnect", "nickname": nickname, "message": "Disconnected", "name_list": name_list})
            break

    await r.zrem('name', nickname)
    del users[nickname]
    
    

