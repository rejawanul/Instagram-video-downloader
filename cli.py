#!/usr/bin/env python3
"""
Instagram Video & Channel Downloader CLI for macOS (Mac mini M4)
Download Instagram Reels, Videos, and Channels in full original upload quality (.mp4).
"""

import argparse
import sys
import time
from pathlib import Path

import config
import engine


def print_banner():
    banner = """
\033[1;35m╭─────────────────────────────────────────────────────────────╮
│  \033[1;37m📸 INSTAGRAM VIDEO DOWNLOADER \033[1;33m[Mac mini M4 Edition]\033[1;35m       │
│  \033[0;36mFull Upload Quality (1080p/4K) • Strict .MP4 • Channels   \033[1;35m│
╰─────────────────────────────────────────────────────────────╯\033[0m
"""
    print(banner)


def main():
    parser = argparse.ArgumentParser(
        description="Download Instagram Reels, Videos, or full Channels in original quality MP4."
    )
    parser.add_argument("url", nargs="?", help="Instagram Reel/Post URL or @username / channel URL")
    parser.add_argument("-o", "--output", help="Output directory path (default: ./downloads)")
    parser.add_argument("-s", "--sessionid", help="Save Instagram sessionid cookie for HD/Channel access")
    parser.add_argument("-c", "--cookies", help="Path to Netscape cookies.txt file")
    parser.add_argument("-r", "--reveal", action="store_true", help="Reveal downloaded file in macOS Finder")
    parser.add_argument("--info-only", action="store_true", help="Extract and display metadata without downloading")
    parser.add_argument("--limit", type=int, default=20, help="Max videos to download from a channel (default: 20)")

    args = parser.parse_args()

    print_banner()

    # Handle session cookie setup
    if args.sessionid:
        config.save_session_cookie(args.sessionid)
        print("\033[1;32m✓ Session ID saved successfully! High-quality streams and channel downloads unlocked.\033[0m\n")
        if not args.url:
            return

    if args.cookies:
        p = Path(args.cookies)
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                config.save_raw_cookies_txt(f.read())
            print(f"\033[1;32m✓ Imported cookies from {args.cookies}!\033[0m\n")
        else:
            print(f"\033[1;31m✗ Cookies file not found: {args.cookies}\033[0m")
            return

    if not args.url:
        print("\033[1;33mUsage:\033[0m")
        print("  python3 cli.py <Instagram-URL-or-@username>")
        print("  python3 cli.py https://www.instagram.com/reel/Cxxxxxx/ -r")
        print("  python3 cli.py @natgeo --limit 10")
        print("\nOr launch the Web GUI with: ./start.sh\n")
        return

    output_dir = args.output or str(config.get_download_dir())
    url = args.url.strip()

    media_type, target_id = engine.get_media_type_and_id(url)
    print(f"\033[1;34m🔍 Analyzing target [{media_type.upper()}]: {url}\033[0m")

    try:
        info = engine.extract_media_info(url)
    except Exception as e:
        print(f"\033[1;31m✗ Extraction Error:\033[0m {e}")
        return

    if args.info_only:
        print(f"\n\033[1;32m✓ Metadata extracted:\033[0m")
        if media_type == "video":
            print(f"  • Title: {info.get('title')}")
            print(f"  • Uploader: @{info.get('uploader')}")
            print(f"  • Resolution: {info.get('resolution')} ({info.get('quality_badge')})")
            print(f"  • Duration: {info.get('duration_str')}")
        else:
            print(f"  • Channel: @{info.get('username')} ({info.get('full_name')})")
            print(f"  • Followers: {info.get('follower_count'):,}")
            print(f"  • Found Videos: {len(info.get('videos', []))}")
        return

    if media_type == "video":
        print(f"\n\033[1;36m🎬 Video: \033[0m{info.get('title')}")
        print(f"\033[1;36m👤 Creator: \033[0m@{info.get('uploader')} | \033[1;33mQuality: {info.get('resolution')} .MP4\033[0m")
        print(f"\033[1;34m⬇️  Starting download in full upload quality...\033[0m")

        task = engine.DownloadTask(url, output_dir=output_dir)
        res = task.run()

        if res.get("success"):
            print(f"\n\033[1;32m✓ Download Complete!\033[0m")
            print(f"  📁 File: \033[1;37m{res.get('filename')}\033[0m")
            print(f"  💾 Path: {res.get('filepath')}")
            if args.reveal:
                print("  🖥️  Revealing in macOS Finder...")
                config.reveal_in_finder(res.get("filepath"))
        else:
            print(f"\n\033[1;31m✗ Download Failed:\033[0m {res.get('error')}")

    elif media_type == "channel":
        videos = info.get("videos", [])
        total = min(len(videos), args.limit)
        print(f"\n\033[1;36m👤 Channel: \033[0m@{info.get('username')} ({info.get('full_name')})")
        print(f"\033[1;34m📦 Batch downloading {total} videos in full quality (.mp4)...\033[0m\n")

        completed = 0
        for i, v in enumerate(videos[:total], 1):
            v_url = v.get("url")
            print(f"\033[1;35m[{i}/{total}]\033[0m Downloading: {v.get('title', 'Video')[:50]}...")
            task = engine.DownloadTask(v_url, output_dir=output_dir)
            res = task.run()
            if res.get("success"):
                print(f"  \033[1;32m✓ Saved:\033[0m {res.get('filename')}")
                completed += 1
            else:
                print(f"  \033[1;31m✗ Failed:\033[0m {res.get('error')}")
            time.sleep(1.0)

        print(f"\n\033[1;32m✓ Batch Complete! Downloaded {completed}/{total} videos to {output_dir}\033[0m")
        if args.reveal:
            config.reveal_in_finder(output_dir)


if __name__ == "__main__":
    main()
