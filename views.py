import random
import string
import aiohttp_jinja2
import aiohttp
from aiohttp_session import get_session


routes = aiohttp.web.RouteTableDef()


def generateRandomName():
    string_pool = string.ascii_letters + string.digits
    result = ""
    for i in range(4):
        result += random.choice(string_pool)
    return "Anonymous_" + result


async def broadcast(users, **kwargs):
    for _ws in users.values():
        try:
            await _ws.send_json(kwargs)
        except OSError:
            # If users have disconnected websocket.
            continue


@routes.get('/')
async def index(request):
    # Get session
    session = await get_session(request)
    # If have no session, make new.
    if session.new:
        nickname = generateRandomName()
        session['nickname'] = nickname
    else:
        nickname = session['nickname']

    r = request.app['redis']
    users = request.app['online_users']

    ws = aiohttp.web.WebSocketResponse()
    # Check if websocket can be started.
    if not ws.can_prepare(request).ok:
        return aiohttp_jinja2.render_template('index.html', request, None)
    # Start websocket.
    # After the call you can use websocket methods.
    await ws.prepare(request)

    # Make clone against to connect request from same browser.
    num = 1
    for k in users.keys():
        if nickname in k:
            num += 1
    if num > 1:
        nickname += " (" + str(num) + ")"
    users[nickname] = ws

    # Online users list
    await r.zadd('name', 1, nickname)
    name_list = await r.zrange('name', 0, -1)
    print(name_list)

    # Broadcast new user enter the room.
    await broadcast(users, type="user", nickname=nickname, name_list=name_list)

    while True:
        # Receive message.
        msg = await ws.receive()

        # Broadcast what received.
        if msg.type == aiohttp.WSMsgType.TEXT:
            # print(f'{nickname} sent message')
            await broadcast(
                users,
                type="received",
                nickname=nickname,
                message=msg.data
            )
        # Remove user from list and close socket.
        else:
            print(f'{nickname} ws connection closed')
            await r.zrem('name', nickname)
            name_list = await r.zrange('name', 0, -1)
            await broadcast(
                users,
                type="disconnect",
                nickname=nickname,
                name_list=name_list
            )
            # print(name_list)
            del users[nickname]
            await ws.close()
            break
