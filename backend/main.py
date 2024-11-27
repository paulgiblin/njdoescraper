from fastapi import FastAPI, WebSocket
import asyncio
import json
import os
from crawler import ElectionCrawler
import aiohttp
import logging
from logging import LogRecord
from datetime import datetime
import pytz

app = FastAPI()

# Create crawler instance
crawler = ElectionCrawler()

# WebSocket connections store
active_connections = []

# Custom WebSocket logging handler
class LogHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.eastern = pytz.timezone('America/New_York')
        self.formatter = logging.Formatter('%(message)s')

    def format(self, record):
        # Convert timestamp to Eastern Time
        created = datetime.fromtimestamp(record.created)
        eastern_time = created.astimezone(self.eastern)
        record.asctime = eastern_time.strftime('%Y-%m-%d %H:%M:%S %Z')
        return f"{record.asctime} [{record.levelname}] {record.getMessage()}"

    def emit(self, record: LogRecord):
        try:
            msg = self.format(record)
            asyncio.create_task(broadcast_log(msg))
        except Exception:
            self.handleError(record)

async def broadcast_log(message):
    if len(active_connections) > 0:
        for connection in active_connections:
            await connection.send_json({
                "type": "log",
                "message": message
            })

async def broadcast_stats():
    while True:
        if active_connections:  # Only broadcast if there are active connections
            stats = crawler.get_stats()
            for connection in active_connections:
                try:
                    await connection.send_json({
                        "type": "stats",
                        "stats": {
                            "status": stats["status"],
                            "pages_crawled": stats["pages_crawled"],
                            "pdfs_found": stats["pdfs_found"],
                            "pdfs_downloaded": stats["pdfs_downloaded"],
                            "current_url": stats["current_url"],
                            "link_tree": stats["link_tree"]
                        }
                    })
                except Exception as e:
                    print(f"Error broadcasting stats: {e}")
                    if connection in active_connections:
                        active_connections.remove(connection)
        await asyncio.sleep(1)

# Create WebSocket logging handler
ws_handler = LogHandler()
logging.getLogger("crawler").addHandler(ws_handler)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        if websocket in active_connections:
            active_connections.remove(websocket)

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
        return {"status": "resumed"}
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
