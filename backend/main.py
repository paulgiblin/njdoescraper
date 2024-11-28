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
        disconnected = []
        for connection in active_connections:
            try:
                await connection.send_json({
                    "type": "log",
                    "message": message
                })
            except Exception as e:
                print(f"Error sending log to connection {id(connection)}: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected connections
        for conn in disconnected:
            if conn in active_connections:
                active_connections.remove(conn)

async def broadcast_stats():
    while True:
        if active_connections:  # Only broadcast if there are active connections
            try:
                stats = crawler.get_stats()
                # Ensure link_tree exists and has the required structure
                if "link_tree" not in stats:
                    stats["link_tree"] = {"nodes": [], "links": []}
                elif stats["link_tree"] is None:
                    stats["link_tree"] = {"nodes": [], "links": []}
                
                message = {
                    "type": "stats",
                    "stats": {
                        "status": stats.get("status", "unknown"),
                        "pages_crawled": stats.get("pages_crawled", 0),
                        "pdfs_found": stats.get("pdfs_found", 0),
                        "pdfs_downloaded": stats.get("pdfs_downloaded", 0),
                        "current_url": stats.get("current_url", ""),
                        "link_tree": stats.get("link_tree", {"nodes": [], "links": []})
                    }
                }
                
                json_str = json.dumps(message)
                print(f"Broadcasting stats (raw): {repr(json_str)}")  # Debug log with repr
                print(f"First character: {repr(json_str[0])}")  # Debug first char
                
                disconnected = []
                for connection in active_connections:
                    try:
                        await connection.send_json(message)
                        print(f"Stats sent successfully to connection {id(connection)}")
                    except Exception as e:
                        print(f"Error broadcasting stats: {e}")
                        disconnected.append(connection)
                
                # Clean up disconnected connections
                for conn in disconnected:
                    if conn in active_connections:
                        active_connections.remove(conn)
                        print(f"Removed disconnected connection. Total active: {len(active_connections)}")
            except Exception as e:
                print(f"Error preparing stats for broadcast: {e}")
        await asyncio.sleep(1)

# Create WebSocket logging handler
ws_handler = LogHandler()
logging.getLogger("crawler").addHandler(ws_handler)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    print(f"New WebSocket connection request from {websocket.client}")  # Debug log
    try:
        await websocket.accept()
        print(f"WebSocket connection accepted for {websocket.client}")  # Debug log
        active_connections.append(websocket)
        print(f"Total active connections: {len(active_connections)}")  # Debug log
        
        # Send initial stats
        stats = crawler.get_stats()
        message = {
            "type": "stats",
            "stats": {
                "status": stats.get("status", "unknown"),
                "pages_crawled": stats.get("pages_crawled", 0),
                "pdfs_found": stats.get("pdfs_found", 0),
                "pdfs_downloaded": stats.get("pdfs_downloaded", 0),
                "current_url": stats.get("current_url", ""),
                "link_tree": stats.get("link_tree", {"nodes": [], "links": []})
            }
        }
        json_str = json.dumps(message)
        print(f"Sending initial stats (raw): {repr(json_str)}")  # Debug log
        await websocket.send_json(message)  # Use send_json instead of send_text
        
        while True:
            try:
                data = await websocket.receive_json()  # Use receive_json for consistency
                print(f"Received message: {data}")  # Debug log
            except Exception as e:
                print(f"Error receiving WebSocket message: {e}")
                break
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        if websocket in active_connections:
            active_connections.remove(websocket)
            print(f"WebSocket connection removed. Total active connections: {len(active_connections)}")

@app.post("/start")
async def start_crawler():
    try:
        print("Start crawler endpoint called")  # Debug log
        if not crawler.running:
            print("Starting crawler task")  # Debug log
            await crawler.start()  # Wait for start to complete
            return {"status": "started", "message": "Crawler started successfully"}
        else:
            print("Crawler already running")  # Debug log
            return {"status": "error", "message": "Crawler is already running"}
    except Exception as e:
        print(f"Error starting crawler: {e}")  # Debug log
        return {"status": "error", "message": str(e)}

@app.post("/stop")
async def stop_crawler():
    crawler.stop()
    return {"status": "stopped"}

@app.post("/rate-limit")
async def set_rate_limit(rate_limit: dict):
    crawler.set_rate_limit(rate_limit["delay"])
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
