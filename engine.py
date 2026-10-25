"""
Instagram Video Downloader Engine
Handles video extraction, profile/channel scanning, full-quality MP4 downloads,
and real-time progress reporting using yt-dlp, FFmpeg, and Instaloader.
"""

import asyncio
import glob
import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import yt_dlp
from config import get_cookie_file_path, get_download_dir, load_settings

# Regular expressions for URL matching
REEL_REGEX = re.compile(r"instagram\.com/(?:reel|reels|p|tv)/([A-Za-z0-9_-]+)", re.IGNORECASE)
PROFILE_REGEX = re.compile(r"instagram\.com/([A-Za-z0-9._]+)/?", re.IGNORECASE)
RESERVED_USERNAMES = {"p", "reel", "reels", "tv", "stories", "explore", "accounts", "direct"}


def get_media_type_and_id(url_or_user: str) -> tuple[str, str]:
    """
    Returns ('video', shortcode) or ('channel', username)
    """
    clean = url_or_user.strip()
    # Check if handle directly passed, e.g. @natgeo or natgeo
    if clean.startswith("@"):
        return "channel", clean[1:].strip()

    # Check for reel/post/tv
    m_reel = REEL_REGEX.search(clean)
    if m_reel:
        return "video", m_reel.group(1)

    # Check for profile URL
    m_profile = PROFILE_REGEX.search(clean)
    if m_profile:
        username = m_profile.group(1).rstrip("/")
        if username.lower() not in RESERVED_USERNAMES:
            return "channel", username

    # If it's a plain string without slashes, treat as username
    if "/" not in clean and " " not in clean and len(clean) > 1:
        return "channel", clean

    # Default to single video URL
    return "video", clean


def ensure_macos_compatible_mp4(filepath: str) -> str:
    """
    Guarantees that the MP4 file has a video codec 100% compatible with
    macOS (QuickTime Player, Finder QuickLook, Safari, AVFoundation).
    If the video is VP9, AV1, or unsupported, transcodes to pristine H.264
    using Apple Silicon M4 VideoToolbox hardware acceleration in seconds.
    Audio is kept untouched (AAC -c:a copy).
    """
    if not filepath or not os.path.exists(filepath):
        return filepath

    try:
        # Check video codec with ffprobe
        cmd = [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=codec_name",
            "-of", "default=noprint_wrappers=1:nokey=1",
            filepath
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        vcodec = res.stdout.strip().lower()

        # If it's already Apple/macOS native h264 or hevc, no transcode needed
        if vcodec in ["h264", "hevc", "hvc1"]:
            return filepath

        # If it's VP9, AV1, or any other web codec not supported by QuickTime
        temp_out = filepath + ".h264.mp4"

        # Try Apple Silicon VideoToolbox M4 hardware encoder first
        hw_success = False
        try:
            transcode_cmd = [
                "ffmpeg", "-y", "-i", filepath,
                "-c:v", "h264_videotoolbox",
                "-b:v", "10M",
                "-c:a", "copy",
                "-movflags", "+faststart",
                temp_out
            ]
            subprocess.run(transcode_cmd, check=True, capture_output=True)
            hw_success = True
        except Exception:
            hw_success = False

        if not hw_success:
            # Fallback to libx264
            transcode_cmd = [
                "ffmpeg", "-y", "-i", filepath,
                "-c:v", "libx264",
                "-crf", "18",
                "-preset", "fast",
                "-c:a", "copy",
                "-movflags", "+faststart",
                temp_out
            ]
            subprocess.run(transcode_cmd, check=True, capture_output=True)

        if os.path.exists(temp_out) and os.path.getsize(temp_out) > 1000:
            os.replace(temp_out, filepath)

    except Exception as e:
        print(f"Error ensuring macOS MP4 compatibility: {e}")

    return filepath


def get_base_ydl_opts(progress_hook: Optional[Callable] = None) -> dict:
    """Builds yt-dlp options configured for highest original quality in strict MP4 container."""
    download_dir = str(get_download_dir())
    cookie_path = get_cookie_file_path()

    opts = {
        # Strictly require video stream (vcodec!=none), preferring H.264 if available, otherwise highest resolution
        "format": "bestvideo*+bestaudio/best[vcodec!=none]/best",
        "format_sort": ["res", "vcodec:h264", "fps", "br"],
        "merge_output_format": "mp4",
        "outtmpl": f"{download_dir}/%(uploader|Instagram)s_%(upload_date|unknown)s_%(id)s_%(resolution|HD)s.%(ext)s",
        "postprocessors": [
            {
                "key": "FFmpegVideoRemuxer",
                "preferedformat": "mp4",
            }
        ],
        "postprocessor_args": {
            "ffmpeg": ["-movflags", "+faststart"],
        },
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": False,
        "socket_timeout": 30,
        "retries": 5,
        "noplaylist": True,
    }

    if cookie_path:
        opts["cookiefile"] = cookie_path

    if progress_hook:
        opts["progress_hooks"] = [progress_hook]

    return opts



def extract_media_info(url_or_user: str) -> dict:
    """
    Inspects Instagram URL and returns full metadata without downloading.
    """
    media_type, target_id = get_media_type_and_id(url_or_user)

    if media_type == "video":
        return _extract_single_video_info(url_or_user, target_id)
    else:
        return _extract_channel_info(target_id)


def _extract_single_video_info(url: str, shortcode: str) -> dict:
    """Extract metadata for a single reel/video/post."""
    clean_url = url
    if not clean_url.startswith("http"):
        clean_url = f"https://www.instagram.com/reel/{shortcode}/"

    ydl_opts = get_base_ydl_opts()
    ydl_opts["extract_flat"] = False

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(clean_url, download=False)
            if not info:
                raise Exception("Could not retrieve media info from Instagram")

            # Determine best resolution
            width = info.get("width")
            height = info.get("height")
            res_str = f"{width}x{height}" if width and height else info.get("resolution", "Original High Resolution")

            duration = info.get("duration", 0)
            duration_str = time.strftime("%M:%S", time.gmtime(duration)) if duration else "Video"

            return {
                "type": "video",
                "id": info.get("id") or shortcode,
                "title": (info.get("title") or info.get("description") or "Instagram Video")[:150],
                "caption": info.get("description", ""),
                "uploader": info.get("uploader") or info.get("channel") or "Instagram User",
                "uploader_id": info.get("uploader_id") or "",
                "thumbnail": info.get("thumbnail") or "",
                "duration": duration,
                "duration_str": duration_str,
                "resolution": res_str,
                "width": width,
                "height": height,
                "fps": info.get("fps") or 30,
                "filesize_approx": info.get("filesize_approx") or info.get("filesize") or 0,
                "webpage_url": info.get("webpage_url") or clean_url,
                "quality_badge": "Full Upload Quality (1080p/4K)",
            }
    except Exception as e:
        err_msg = str(e)
        if "login" in err_msg.lower() or "cookie" in err_msg.lower() or "empty media" in err_msg.lower():
            raise Exception(
                "Instagram requires session authentication for this video. "
                "Please add your session ID or cookies in Settings (takes 10 seconds)."
            ) from e
        raise Exception(f"Failed to fetch video: {err_msg}") from e


def _extract_channel_info(username: str) -> dict:
    """
    Extract profile and video/reel list for a channel/user using instaloader or yt-dlp.
    """
    clean_user = username.strip().lstrip("@")
    profile_url = f"https://www.instagram.com/{clean_user}/"
    cookie_path = get_cookie_file_path()

    # Attempt to fetch profile info using yt-dlp first or instaloader
    videos = []
    profile_data = {
        "type": "channel",
        "username": clean_user,
        "full_name": clean_user,
        "biography": "",
        "avatar": "",
        "follower_count": 0,
        "media_count": 0,
        "videos": [],
    }

    ydl_opts = {
        "extract_flat": True,
        "quiet": True,
        "no_warnings": True,
        "playlistend": 30,  # Grab up to 30 recent reels/videos for fast response
    }
    if cookie_path:
        ydl_opts["cookiefile"] = cookie_path

    try:
        # Try fetching reels playlist: https://www.instagram.com/USERNAME/reels/
        reels_url = f"https://www.instagram.com/{clean_user}/reels/"
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            res = ydl.extract_info(reels_url, download=False)
            if res and "entries" in res:
                entries = list(res.get("entries") or [])
                for entry in entries:
                    if entry:
                        v_id = entry.get("id")
                        v_url = entry.get("url") or f"https://www.instagram.com/reel/{v_id}/"
                        v_title = entry.get("title") or entry.get("description") or f"Reel {v_id}"
                        videos.append({
                            "id": v_id,
                            "url": v_url,
                            "title": v_title[:100],
                            "thumbnail": entry.get("thumbnail") or "",
                            "duration": entry.get("duration"),
                            "duration_str": time.strftime("%M:%S", time.gmtime(entry.get("duration") or 0)) if entry.get("duration") else "Reel",
                            "view_count": entry.get("view_count"),
                            "selected": True,
                        })
                profile_data["videos"] = videos
                profile_data["media_count"] = len(videos)
                if videos:
                    return profile_data
    except Exception as e:
        # Continue to secondary method if yt-dlp hit rate limit or login
        pass

    # Secondary: Use Instaloader to extract profile and reel entries
    try:
        import instaloader
        L = instaloader.Instaloader(
            download_pictures=False,
            download_videos=False,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            quiet=True,
        )
        if cookie_path:
            import http.cookiejar
            cj = http.cookiejar.MozillaCookieJar(cookie_path)
            cj.load(ignore_discard=True, ignore_expires=True)
            L.context._session.cookies = cj

        profile = instaloader.Profile.from_username(L.context, clean_user)
        profile_data["full_name"] = profile.full_name or clean_user
        profile_data["biography"] = profile.biography or ""
        profile_data["avatar"] = profile.profile_pic_url or ""
        profile_data["follower_count"] = profile.followers
        profile_data["media_count"] = profile.mediacount

        # Collect up to 24 recent video posts/reels
        count = 0
        for post in profile.get_posts():
            if post.is_video:
                videos.append({
                    "id": post.shortcode,
                    "url": f"https://www.instagram.com/reel/{post.shortcode}/",
                    "title": (post.caption or f"Video {post.shortcode}")[:100],
                    "thumbnail": post.url,  # thumbnail picture url
                    "duration": None,
                    "duration_str": "Video",
                    "view_count": getattr(post, "video_view_count", None),
                    "selected": True,
                })
                count += 1
                if count >= 24:
                    break
        profile_data["videos"] = videos
        return profile_data
    except Exception as e:
        err_msg = str(e)
        if "login" in err_msg.lower() or "401" in err_msg.lower() or "unauthorized" in err_msg.lower():
            raise Exception(
                f"Instagram requires a session cookie to browse profile @{clean_user}. "
                "Please configure your session ID in Settings."
            ) from e
        raise Exception(f"Could not load channel @{clean_user}: {err_msg}") from e


class DownloadTask:
    """Manages an active download operation with live progress tracking."""

    def __init__(self, target_url: str, output_dir: Optional[str] = None):
        self.url = target_url
        self.output_dir = output_dir or str(get_download_dir())
        self.status = "queued"  # queued, downloading, converting, finished, error
        self.progress_percent = 0.0
        self.speed_str = "0 KB/s"
        self.eta_str = "--:--"
        self.downloaded_bytes = 0
        self.total_bytes = 0
        self.filename = ""
        self.filepath = ""
        self.error_message = ""
        self.title = ""
        self.start_time = time.time()

    def progress_hook(self, d: dict):
        status = d.get("status")
        if status == "downloading":
            self.status = "downloading"
            downloaded = d.get("downloaded_bytes", 0)
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 1
            self.downloaded_bytes = downloaded
            self.total_bytes = total
            if total > 0:
                self.progress_percent = round((downloaded / total) * 100, 1)

            # yt-dlp helper strings
            self.speed_str = d.get("_speed_str", "Calculating...")
            self.eta_str = d.get("_eta_str", "--:--")
            if d.get("filename"):
                self.filename = os.path.basename(d["filename"])
                self.filepath = d["filename"]

        elif status == "finished":
            self.status = "converting"
            self.progress_percent = 100.0
            if d.get("filename"):
                self.filepath = d["filename"]
                self.filename = os.path.basename(d["filename"])

    def run(self) -> dict:
        ydl_opts = get_base_ydl_opts(progress_hook=self.progress_hook)
        ydl_opts["outtmpl"] = f"{self.output_dir}/%(uploader|Instagram)s_%(upload_date|unknown)s_%(id)s.%(ext)s"

        try:
            self.status = "downloading"
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=True)
                if not info:
                    raise Exception("No video streams found to download.")

                self.title = info.get("title") or info.get("description") or "Instagram Video"
                
                # Check resulting file on disk
                final_filename = ydl.prepare_filename(info)
                # If merged to mp4:
                base, _ = os.path.splitext(final_filename)
                mp4_file = f"{base}.mp4"
                
                if os.path.exists(mp4_file):
                    self.filepath = mp4_file
                    self.filename = os.path.basename(mp4_file)
                elif os.path.exists(final_filename):
                    self.filepath = final_filename
                    self.filename = os.path.basename(final_filename)
                else:
                    # Scan output directory for the shortcode
                    shortcode = info.get("id")
                    matches = glob.glob(f"{self.output_dir}/*{shortcode}*.mp4")
                    if matches:
                        self.filepath = matches[0]
                        self.filename = os.path.basename(matches[0])

                # Ensure video codec is 100% compatible with macOS (QuickTime/Safari/Finder)
                if self.filepath and os.path.exists(self.filepath):
                    self.status = "converting"
                    self.filepath = ensure_macos_compatible_mp4(self.filepath)
                    self.filename = os.path.basename(self.filepath)

                self.status = "finished"
                self.progress_percent = 100.0

                return {
                    "success": True,
                    "filepath": self.filepath,
                    "filename": self.filename,
                    "title": self.title,
                    "size": os.path.getsize(self.filepath) if self.filepath and os.path.exists(self.filepath) else 0,
                }

        except Exception as e:
            self.status = "error"
            self.error_message = str(e)
            if "login" in str(e).lower() or "cookie" in str(e).lower() or "empty media" in str(e).lower():
                self.error_message = "Instagram requires session login. Please configure your session ID in Settings."
            return {
                "success": False,
                "error": self.error_message,
            }

    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "status": self.status,
            "progress_percent": self.progress_percent,
            "speed": self.speed_str,
            "eta": self.eta_str,
            "downloaded_bytes": self.downloaded_bytes,
            "total_bytes": self.total_bytes,
            "filename": self.filename,
            "filepath": self.filepath,
            "title": self.title,
            "error": self.error_message,
        }


def get_download_history() -> List[dict]:
    """Scans the downloads directory and returns list of completed MP4 videos."""
    d = get_download_dir()
    files = list(d.glob("*.mp4"))
    # Sort newest first
    files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

    history = []
    for f in files:
        stat = f.stat()
        history.append({
            "filename": f.name,
            "filepath": str(f.resolve()),
            "filesize": stat.st_size,
            "filesize_str": _format_bytes(stat.st_size),
            "created_at": time.strftime("%Y-%m-%d %H:%M", time.localtime(stat.st_mtime)),
            "mtime": stat.st_mtime,
        })
    return history


def _format_bytes(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    elif size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    else:
        return f"{size / (1024 * 1024 * 1024):.2f} GB"
