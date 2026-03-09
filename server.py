import os
from aiohttp import web
import asyncio
 
client_ws = None
ws_lock = asyncio.Lock()
 
async def websocket_handler(request):
    global client_ws
 
    # ❗ Reject new client if one is already connected
    if client_ws is not None:
        return web.Response(text="A tunnel client is already connected", status=403)import os

import asyncio

import uuid

from aiohttp import web
 
workers = []

pending = {}
 
# -------------------------

# WebSocket worker handler

# -------------------------

async def websocket_handler(request):
 
    ws = web.WebSocketResponse()

    await ws.prepare(request)
 
    workers.append(ws)

    print("Worker connected:", len(workers))
 
    try:

        async for msg in ws:
 
            if msg.type == web.WSMsgType.TEXT:

                data = msg.json()
 
                req_id = data["id"]
 
                if req_id in pending:

                    pending[req_id].set_result(data["body"])
 
    finally:

        workers.remove(ws)

        print("Worker disconnected")
 
    return ws
 
 
# -------------------------

# HTTP handler

# -------------------------

async def handle_http(request):
 
    # Block browser noise

    if request.path == "/favicon.ico":

        return web.Response(status=204)
 
    blocked_extensions = [".ico", ".png", ".svg", ".map"]
 
    if any(request.path.endswith(ext) for ext in blocked_extensions):

        return web.Response(status=204)
 
    if not workers:

        return web.Response(text="No tunnel workers connected")
 
    req_id = str(uuid.uuid4())
 
    future = asyncio.get_event_loop().create_future()

    pending[req_id] = future
 
    payload = {

        "id": req_id,

        "path": request.path_qs,

        "method": request.method

    }
 
    # Round robin worker selection

    worker = workers[0]

    workers.append(workers.pop(0))
 
    await worker.send_json(payload)
 
    try:

        body = await asyncio.wait_for(future, timeout=30)

        return web.Response(text=body)

    except asyncio.TimeoutError:

        return web.Response(text="Tunnel timeout", status=504)

    finally:

        pending.pop(req_id, None)
 
 
# -------------------------

# App setup

# -------------------------

app = web.Application()
 
app.router.add_get("/ws", websocket_handler)

app.router.add_route("*", "/{tail:.*}", handle_http)
 
port = int(os.environ.get("PORT", 10000))
 
web.run_app(app, host="0.0.0.0", port=port)
 
 
    ws = web.WebSocketResponse()
    await ws.prepare(request)
 
    client_ws = ws
    print("Tunnel client connected")
 
    try:
        async for msg in ws:
            pass
    finally:
        client_ws = None
        print("Tunnel client disconnected")
 
    return ws
 
 
async def handle_http(request):
    global client_ws
 
    if client_ws is None:
        return web.Response(text="Tunnel client not connected")
 
    try:
        async with ws_lock:
            await client_ws.send_str(request.path)
 
            msg = await client_ws.receive()
 
        return web.Response(text=msg.data)
 
    except Exception as e:
        return web.Response(text=f"Tunnel error: {str(e)}")
 
 
app = web.Application()
 
app.router.add_get("/ws", websocket_handler)
app.router.add_route("*", "/{tail:.*}", handle_http)
 
port = int(os.environ.get("PORT", 10000))
 
web.run_app(app, host="0.0.0.0", port=port)

