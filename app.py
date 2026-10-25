"""
FastAPI Server for Instagram Video Downloader
Designed for macOS / Apple Silicon (Mac mini M4)
Provides REST and WebSocket endpoints for extraction, live download tracking,
batch channel processing, macOS Finder integration, and media streaming.
"""

import asyncio
import os
import threading
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import (
    BackgroundTasks,
    FastAPI,
    HTTPException,
    Query,
    Request,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import config
import engine

app = FastAPI(
    title="Instagram Video Downloader",
    description="Full Original Quality Instagram Video & Channel Downloader for Mac mini M4",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Active tasks tracking: task_id -> DownloadTask or BatchTracker
ACTIVE_TASKS: Dict[str, engine.DownloadTask] = {}
BATCH_TASKS: Dict[str, dict] = {}

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
DOWNLOADS_DIR = config.get_download_dir()

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# Pydantic models
class ExtractRequest(BaseModel):
    url: str


class DownloadRequest(BaseModel):
    url: str


class BatchDownloadRequest(BaseModel):
    urls: List[str]
    username: Optional[str] = "instagram"


class SettingsRequest(BaseModel):
    session_id: Optional[str] = None
    download_dir: Optional[str] = None


class RevealRequest(BaseModel):
    path: str


@app.get("/", response_class=HTMLResponse)
@app.head("/")
async def serve_index():
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="Frontend template not found")
    with open(index_file, "r", encoding="utf-8") as f:
        return f.read()


@app.get("/health")
@app.head("/health")
async def health_check():
    """Health check endpoint for Render / Docker / load balancers."""
    return {"status": "ok", "service": "Instagram Video Downloader"}


@app.post("/api/extract")
async def extract_info(req: ExtractRequest):
    """Inspects an Instagram link (single video/reel or profile/channel) and returns rich info."""
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="Please enter an Instagram URL or username")

    try:
        loop = asyncio.get_running_loop()
        data = await loop.run_in_executor(None, engine.extract_media_info, url)
        return {"success": True, "data": data}
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})


@app.post("/api/download")
async def start_single_download(req: DownloadRequest, background_tasks: BackgroundTasks):
    """Starts downloading a single video in full original quality to .mp4."""
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="Missing URL")

    task_id = str(uuid.uuid4())
    task = engine.DownloadTask(url)
    ACTIVE_TASKS[task_id] = task

    def run_worker():
        task.run()

    # Run in background thread
    t = threading.Thread(target=run_worker, daemon=True)
    t.start()

    return {"success": True, "task_id": task_id, "status": "started"}


@app.get("/api/progress/{task_id}")
async def get_task_progress(task_id: str):
    """Poll progress for a single download task."""
    task = ACTIVE_TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task.to_dict()


@app.websocket("/ws/progress/{task_id}")
async def ws_task_progress(websocket: WebSocket, task_id: str):
    """WebSocket stream for real-time progress updates."""
    await websocket.accept()
    task = ACTIVE_TASKS.get(task_id)

    if not task:
        await websocket.send_json({"error": "Task not found", "status": "error"})
        await websocket.close()
        return

    try:
        while True:
            data = task.to_dict()
            await websocket.send_json(data)
            if data["status"] in ("finished", "error"):
                # Send final update and break
                await asyncio.sleep(0.5)
                await websocket.send_json(data)
                break
            await asyncio.sleep(0.3)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass


@app.post("/api/channel/batch-download")
async def start_batch_download(req: BatchDownloadRequest):
    """Starts queueing multiple videos from an Instagram channel/profile."""
    if not req.urls:
        raise HTTPException(status_code=400, detail="No video URLs provided for batch download")

    batch_id = str(uuid.uuid4())
    BATCH_TASKS[batch_id] = {
        "id": batch_id,
        "username": req.username,
        "total": len(req.urls),
        "completed": 0,
        "failed": 0,
        "status": "processing",  # processing, completed, error
        "current_item": "",
        "items": [],
    }

    def batch_worker():
        tracker = BATCH_TASKS[batch_id]
        for idx, item_url in enumerate(req.urls):
            tracker["current_item"] = item_url
            t = engine.DownloadTask(item_url)
            res = t.run()
            if res.get("success"):
                tracker["completed"] += 1
                tracker["items"].append({
                    "url": item_url,
                    "filename": res.get("filename"),
                    "status": "success",
                })
            else:
                tracker["failed"] += 1
                tracker["items"].append({
                    "url": item_url,
                    "error": res.get("error"),
                    "status": "failed",
                })
            # Sleep slightly between requests to respect Instagram rate limits
            time.sleep(1.5)

        tracker["status"] = "completed"
        tracker["current_item"] = ""

    t = threading.Thread(target=batch_worker, daemon=True)
    t.start()

    return {"success": True, "batch_id": batch_id, "total": len(req.urls)}


@app.get("/api/channel/batch-progress/{batch_id}")
async def get_batch_progress(batch_id: str):
    """Poll status of batch channel download."""
    tracker = BATCH_TASKS.get(batch_id)
    if not tracker:
        raise HTTPException(status_code=404, detail="Batch task not found")
    return tracker


@app.get("/api/history")
async def get_history():
    """Returns list of downloaded MP4 videos in the downloads directory."""
    history = engine.get_download_history()
    return {"success": True, "count": len(history), "videos": history}


@app.post("/api/reveal")
async def reveal_file_or_dir(req: RevealRequest):
    """macOS Integration: Reveals the file or folder in macOS Finder."""
    target_path = req.path.strip()
    if not target_path:
        target_path = str(config.get_download_dir())
    success = config.reveal_in_finder(target_path)
    return {"success": success, "path": target_path}


@app.post("/api/open-downloads")
async def open_downloads_folder():
    """macOS Integration: Opens the downloads folder in Finder."""
    d = config.get_download_dir()
    success = config.reveal_in_finder(str(d))
    return {"success": success, "path": str(d)}


@app.get("/api/media/{filename}")
async def stream_media(filename: str, request: Request):
    """Streams a downloaded MP4 video file with HTTP range request support for video player scrubbing."""
    d = config.get_download_dir()
    filepath = (d / filename).resolve()

    # Prevent directory traversal
    if not str(filepath).startswith(str(d.resolve())):
        raise HTTPException(status_code=403, detail="Forbidden")

    if not filepath.exists() or not filepath.is_file():
        raise HTTPException(status_code=404, detail="Video file not found")

    file_size = filepath.stat().st_size
    range_header = request.headers.get("range")

    if range_header:
        # Parse range header
        byte_range = range_header.replace("bytes=", "").split("-")
        start = int(byte_range[0])
        end = int(byte_range[1]) if byte_range[1] else file_size - 1
        length = (end - start) + 1

        def iterfile():
            with open(filepath, "rb") as f:
                f.seek(start)
                remaining = length
                chunk_size = 1024 * 1024  # 1MB chunks
                while remaining > 0:
                    read_bytes = min(chunk_size, remaining)
                    chunk = f.read(read_bytes)
                    if not chunk:
                        break
                    remaining -= len(chunk)
                    yield chunk

        headers = {
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(length),
            "Content-Type": "video/mp4",
        }
        return StreamingResponse(iterfile(), status_code=206, headers=headers)

    return FileResponse(
        path=str(filepath),
        media_type="video/mp4",
        filename=filename,
        headers={"Accept-Ranges": "bytes"},
    )


@app.get("/api/download-file/{filename}")
async def download_file_to_client(filename: str):
    """Directly triggers file download in client browser/mobile device."""
    d = config.get_download_dir()
    filepath = (d / filename).resolve()

    if not str(filepath).startswith(str(d.resolve())):
        raise HTTPException(status_code=403, detail="Forbidden")

    if not filepath.exists() or not filepath.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=str(filepath),
        media_type="video/mp4",
        filename=filename,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )



@app.get("/api/settings")
async def get_settings():
    """Get current configuration."""
    settings = config.load_settings()
    # Mask session id for security
    raw_sid = settings.get("session_id", "")
    masked_sid = ""
    if raw_sid:
        masked_sid = raw_sid[:4] + "••••••••" + raw_sid[-4:] if len(raw_sid) > 8 else "••••••••"
    
    return {
        "success": True,
        "download_dir": settings.get("download_dir"),
        "quality": settings.get("quality", "best"),
        "format": settings.get("format", "mp4"),
        "has_session": bool(raw_sid) or settings.get("cookies_loaded", False),
        "session_masked": masked_sid,
        "cookies_loaded": settings.get("cookies_loaded", False),
    }


@app.post("/api/settings")
async def update_settings(req: SettingsRequest):
    """Updates settings including Instagram session ID and download path."""
    current = config.load_settings()
    if req.download_dir:
        new_dir = Path(req.download_dir).expanduser().resolve()
        new_dir.mkdir(parents=True, exist_ok=True)
        current["download_dir"] = str(new_dir)
        config.save_settings(current)

    if req.session_id is not None:
        config.save_session_cookie(req.session_id)

    return {"success": True, "message": "Settings updated successfully"}


@app.post("/api/settings/upload-cookies")
async def upload_cookies_file(file: UploadFile):
    """Uploads a Netscape cookies.txt file exported from browser."""
    content = await file.read()
    try:
        text = content.decode("utf-8")
        success = config.save_raw_cookies_txt(text)
        if success:
            return {"success": True, "message": "Cookies imported successfully"}
        else:
            raise HTTPException(status_code=400, detail="Invalid or empty cookies file")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Cookie file must be plain text")
