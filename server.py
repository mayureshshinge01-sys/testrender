import asyncio
import websockets
from aiohttp import web
 
client = None
 
async def tunnel(ws):
    global client
    client = ws
    print("Client connected")
 
    try:
        await ws.wait_closed()
    finally:
        client = None
        print("Client disconnected")
 
async def handle_http(request):
    global client
 
    if client is None:
        return web.Response(text="No tunnel client connected")
 
    data = {
        "method": request.method,
        "path": request.path_qs,
    }
 
    await client.send(str(data))
    response = await client.recv()
 
    return web.Response(text=response)
 
async def main():
    ws_server = await websockets.serve(tunnel, "0.0.0.0", 8765)
 
    app = web.Application()
    app.router.add_route("*", "/{tail:.*}", handle_http)
 
    runner = web.AppRunner(app)
    await runner.setup()
 
    port = int(__import__("os").environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
 
    print("Server running")
 
    await asyncio.Future()
 
asyncio.run(main())