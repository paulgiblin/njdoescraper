from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import os
from crawler import ElectionCrawler
import aiohttp
import logging

app = FastAPI()

# CORS configuration
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:8080")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create crawler instance
crawler = ElectionCrawler()

# WebSocket connections store
active_connections = []

# Custom WebSocket logging handler
class WebSocketLoggingHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.connections = []
        self.formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')

    def emit(self, record: LogRecord):
        try:
            log_entry = self.formatter.format(record)
            asyncio.create_task(self.broadcast_log(log_entry))
        except Exception as e:
            print(f"Error in WebSocket logging handler: {e}")

    async def broadcast_log(self, log_entry: str):
        for connection in self.connections:
            try:
                await connection.send_json({
                    "type": "log",
                    "data": log_entry
                })
            except:
                if connection in self.connections:
                    self.connections.remove(connection)

# Create WebSocket logging handler
ws_handler = WebSocketLoggingHandler()
logging.getLogger().addHandler(ws_handler)
logging.getLogger("crawler").addHandler(ws_handler)

async def broadcast_stats():
    while True:
        if active_connections:
            stats = crawler.get_stats()
            for connection in active_connections:
                try:
                    await connection.send_json(stats)
                except:
                    active_connections.remove(connection)
        await asyncio.sleep(1)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    ws_handler.connections.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except:
        active_connections.remove(websocket)
        if websocket in ws_handler.connections:
            ws_handler.connections.remove(websocket)

@app.post("/start")
async def start_crawler():
    if not crawler.running:
        asyncio.create_task(crawler.start())
    return {"status": "started"}

@app.post("/stop")
async def stop_crawler():
    crawler.stop()
    return {"status": "stopped"}

@app.post("/pause")
async def pause_crawler():
    if crawler.paused:
        crawler.resume()
        return {"status": "running"}
    else:
        crawler.pause()
        return {"status": "paused"}

@app.post("/rate-limit")
async def set_rate_limit(rate_limit: dict):
    crawler.set_rate_limit(rate_limit["rate_limit"])
    return {"status": "updated"}

@app.get("/stats")
async def get_stats():
    return crawler.get_stats()

# Start broadcasting stats when the app starts
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(broadcast_stats())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
