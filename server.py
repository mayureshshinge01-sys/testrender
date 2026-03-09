import os
import asyncio
import uuid
from aiohttp import web
 
workers = []
pending = {}
 
# -----------------------------
# WebSocket Worker Handler
# -----------------------------
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
 
 
# -----------------------------
# HTTP Handler
# -----------------------------
async def handle_http(request):
 
    # Block browser noise
    if request.path == "/favicon.ico":
        return web.Response(status=204)
 
    blocked_ext = [".ico", ".png", ".svg", ".map"]
 
    if any(request.path.endswith(ext) for ext in blocked_ext):
        return web.Response(status=204)
 
    if not workers:
        return web.Response(text="No tunnel workers connected")
 
    req_id = str(uuid.uuid4())
 
    loop = asyncio.get_event_loop()
    future = loop.create_future()
 
    pending[req_id] = future
 
    payload = {
        "id": req_id,
        "path": request.path_qs,
        "method": request.method
    }
 
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
 
 
# -----------------------------
# App Setup
# -----------------------------
app = web.Application()
 
app.router.add_get("/ws", websocket_handler)
app.router.add_route("*", "/{tail:.*}", handle_http)
 
port = int(os.environ.get("PORT", 10000))
 
web.run_app(app, host="0.0.0.0", port=port)
