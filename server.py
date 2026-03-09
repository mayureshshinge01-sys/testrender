import os
from aiohttp import web
import asyncio
 
client_ws = None
ws_lock = asyncio.Lock()
 
async def websocket_handler(request):
    global client_ws
 
    # ❗ Reject new client if one is already connected
    if client_ws is not None:
        return web.Response(text="A tunnel client is already connected", status=403)
 
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
