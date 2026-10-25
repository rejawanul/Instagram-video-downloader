"""
Configuration and settings management for Instagram Video Downloader
Optimized for macOS / Apple Silicon (Mac mini M4)
"""

import json
import os
import subprocess
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DOWNLOAD_DIR = BASE_DIR / "downloads"
SETTINGS_FILE = BASE_DIR / "settings.json"
COOKIES_FILE = BASE_DIR / "cookies.txt"

DEFAULT_SETTINGS = {
    "download_dir": str(DEFAULT_DOWNLOAD_DIR),
    "quality": "best",  # Always download full original uploaded resolution
    "format": "mp4",     # Strictly .mp4 output
    "session_id": "",
    "cookies_loaded": False,
    "last_username": "",
    "hardware_acceleration": True, # Apple Silicon VideoToolbox
}


def load_settings() -> dict:
    if not SETTINGS_FILE.exists():
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS.copy()
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            merged = {**DEFAULT_SETTINGS, **data}
            # Check if environment variable INSTAGRAM_SESSION_ID is provided (e.g. Hugging Face Secrets)
            env_sid = os.environ.get("INSTAGRAM_SESSION_ID", "").strip()
            if env_sid and not merged.get("session_id"):
                save_session_cookie(env_sid)
                merged["session_id"] = env_sid

            # Verify if cookies file exists and is not empty
            merged["cookies_loaded"] = COOKIES_FILE.exists() and COOKIES_FILE.stat().st_size > 10
            return merged
    except Exception:
        return DEFAULT_SETTINGS.copy()


def save_settings(settings: dict):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)


def get_download_dir() -> Path:
    settings = load_settings()
    d = Path(settings.get("download_dir", str(DEFAULT_DOWNLOAD_DIR)))
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_session_cookie(session_id: str, ds_user_id: str = "", csrf_token: str = "") -> bool:
    """Save an Instagram session cookie in Netscape cookies.txt format for yt-dlp/instaloader."""
    session_id = session_id.strip()
    if not session_id:
        if COOKIES_FILE.exists():
            COOKIES_FILE.unlink()
        settings = load_settings()
        settings["session_id"] = ""
        settings["cookies_loaded"] = False
        save_settings(settings)
        return True

    # If user provided user_id:session_id or just session_id
    if "%3A" in session_id and not ds_user_id:
        try:
            parts = session_id.split("%3A")
            ds_user_id = parts[0]
        except Exception:
            pass

    expiry = int(time.time()) + (365 * 24 * 60 * 60)
    lines = [
        "# Netscape HTTP Cookie File",
        "# Created by Instagram Video Downloader",
        f".instagram.com\tTRUE\t/\tTRUE\t{expiry}\tsessionid\t{session_id}",
    ]
    if ds_user_id:
        lines.append(f".instagram.com\tTRUE\t/\tFALSE\t{expiry}\tds_user_id\t{ds_user_id}")
    if csrf_token:
        lines.append(f".instagram.com\tTRUE\t/\tTRUE\t{expiry}\tcsrftoken\t{csrf_token}")

    with open(COOKIES_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    settings = load_settings()
    settings["session_id"] = session_id
    settings["cookies_loaded"] = True
    save_settings(settings)
    return True


def save_raw_cookies_txt(content: str) -> bool:
    """Save user-uploaded cookies.txt content directly."""
    content = content.strip()
    if not content:
        return False
    with open(COOKIES_FILE, "w", encoding="utf-8") as f:
        f.write(content + "\n")

    settings = load_settings()
    settings["cookies_loaded"] = True
    save_settings(settings)
    return True


def reveal_in_finder(file_or_dir_path: str) -> bool:
    """Use macOS native 'open -R' to reveal file in Finder, or 'open' for folder."""
    try:
        p = Path(file_or_dir_path).resolve()
        if p.is_file():
            subprocess.run(["open", "-R", str(p)], check=True)
            return True
        elif p.is_dir():
            subprocess.run(["open", str(p)], check=True)
            return True
        return False
    except Exception as e:
        print(f"Error revealing in Finder: {e}")
        return False


def get_cookie_file_path() -> str | None:
    if COOKIES_FILE.exists() and COOKIES_FILE.stat().st_size > 10:
        return str(COOKIES_FILE)
    return None
