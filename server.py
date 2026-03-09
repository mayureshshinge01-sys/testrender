import asyncio
from aiohttp import web
 
client_ws = None
 
async def websocket_handler(request):
    global client_ws
    ws = web.WebSocketResponse()
    await ws.prepare(request)
 
    client_ws = ws
    print("Tunnel client connected")
 
    async for msg in ws:
        pass
 
    client_ws = None
    print("Client disconnected")
    return ws
 
async def handle_http(request):
    global client_ws
 
    if client_ws is None:
        return web.Response(text="No tunnel client connected")
 
    await client_ws.send_str(request.path)
 
    msg = await client_ws.receive()
 
    return web.Response(text=msg.data)
 
app = web.Application()
app.router.add_get("/ws", websocket_handler)
app.router.add_route("*", "/{tail:.*}", handle_http)
 
port = int(__import__("os").environ.get("PORT", 10000))
 
web.run_app(app, host="0.0.0.0", port=port)
