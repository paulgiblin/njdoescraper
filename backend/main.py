from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from crawler import crawler
import json
import asyncio
from typing import Dict
import os

app = FastAPI()

# Configure CORS with environment variable
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:8080')

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/start")
async def start_crawler():
    asyncio.create_task(crawler.start())
    return {"status": "started"}

@app.post("/stop")
async def stop_crawler():
    await crawler.stop()
    return {"status": "stopped"}

@app.post("/pause")
async def pause_crawler():
    await crawler.pause()
    return {"status": "paused" if crawler.is_paused else "resumed"}

@app.post("/rate-limit")
async def set_rate_limit(rate: float):
    crawler.set_rate_limit(rate)
    return {"status": "rate limit updated", "new_rate": rate}

@app.get("/stats")
async def get_stats():
    return crawler.get_stats()

# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            stats = crawler.get_stats()
            await websocket.send_json(stats)
            await asyncio.sleep(1)
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
