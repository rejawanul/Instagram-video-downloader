---
title: Instagram Video Downloader Pro
emoji: 📸
colorFrom: pink
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# 📸 Instagram Video Downloader Pro

A high-performance Instagram Video & Channel Downloader built specifically for **macOS & Apple Silicon (Mac mini M4)**.

Downloads Instagram Reels, Video Posts, and Full Profiles/Channels in **100% Original Upload Quality** (Full Resolution 1080p / 4K) strictly in `.MP4` format with Apple Silicon VideoToolbox and lossless FFmpeg remuxing.

---

## ✨ Features

- 🎯 **Full Original Upload Resolution**: Preserves bit-for-bit video and audio stream quality (1080p, 4K, 60fps) without re-compression.
- 🎬 **Strict .MP4 Output**: Seamlessly remuxes and verifies container integrity via FFmpeg.
- 👤 **Channel & Profile Explorer**: Enter any `@username` or channel URL to fetch, preview, and batch-download all reels and videos with 1-click.
- ⚡ **Mac mini M4 Native Speed**: Optimized with Apple Silicon hardware acceleration and asynchronous background pipelines.
- 🖥️ **macOS Finder Integration**: Instant "Reveal in Finder" button (`open -R`) to view downloaded files immediately in macOS.
- 🌐 **Sleek macOS Sequoia Web Dashboard**: Glassmorphism UI, real-time download speedometer, live percentage, ETA countdown, and built-in cinema video player.
- 💻 **Terminal CLI Included**: Prefer the terminal? Use `python3 cli.py <url>` directly from your command line.
- 🔐 **Session & Cookies Support**: Easy 10-second setup for your Instagram `sessionid` or `cookies.txt` to bypass login walls, download private content you follow, and prevent rate limits.

---

## 🚀 Quick Start

### 1. Launch the Web Application (Recommended)
Double-click **`run.command`** in Finder, or run in Terminal:
```bash
./start.sh
```
This automatically launches the server and opens your browser at:
👉 **`http://localhost:5055`**

### 2. Or Use via Command Line (CLI)
```bash
# Download a single Reel in Full Quality .mp4
./venv/bin/python3 cli.py "https://www.instagram.com/reel/Cxxxxxx/" -r

# Batch download 10 videos from a channel/profile
./venv/bin/python3 cli.py @natgeo --limit 10

# Save your Instagram sessionid once for unlimited HD/Channel access
./venv/bin/python3 cli.py --sessionid "YOUR_SESSION_ID"
```

---

## 💡 How to Add Your Instagram Session ID (10 Seconds)
To download from channels without rate-limiting and access HD streams if Instagram prompts for login:
1. Open [instagram.com](https://www.instagram.com) in Chrome or Safari on your Mac where you are logged in.
2. Press **Right-Click -> Inspect** (or `Cmd + Option + I`) and go to the **Application** (or **Storage**) tab.
3. Under **Cookies** -> `https://www.instagram.com`, copy the value of `sessionid`.
4. In the app, click **Settings** (top right) and paste your `sessionid` into the box, then click **Save**!

---

## 📁 Downloads Folder
All downloaded `.mp4` videos are saved to:
`/Volumes/SSD/Programming/Instagram video downloader/downloads`

You can change this anytime from the **Settings** modal or click the **Finder** icon in the header to open the folder instantly.

---

## 🇧🇩 বাংলা নির্দেশিকা (Bengali Guide)

### কীভাবে ব্যবহার করবেন:
1. **ওয়েব অ্যাপ চালু করতে:** টার্মিনালে `./start.sh` চালান অথবা ফাইন্ডার থেকে `run.command` এ ডাবল ক্লিক করুন। আপনার ব্রাউজারে `http://localhost:5055` ওপেন হবে।
2. **একক ভিডিও / রিল ডাউনলোড:**
   - যেকোনো ইনস্টাগ্রাম রিল বা ভিডিওর লিঙ্ক সার্চ বক্সে পেস্ট করে **"Fetch Video"** চাপুন।
   - প্রিভিউ কার্ডে ফুল রেজোলিউশন (1080p/4K) এবং ক্যাপশন দেখে **"Download Full Quality MP4"** চাপুন।
3. **ইনস্টাগ্রাম চ্যানেল / প্রোফাইল থেকে সব ভিডিও ডাউনলোড:**
   - **"Channel / Profile Explorer"** ট্যাবে ক্লিক করুন।
   - চ্যানেলের লিঙ্ক বা ইউজারনেম (যেমন `@username`) দিন।
   - প্রোফাইলের সব রিল/ভিডিও চলে আসবে। আপনি "Select All" বা নির্দিষ্ট ভিডিও সিলেক্ট করে **"Download Selected Videos"** চাপলে একসাথে সব ভিডিও ফুল কোয়ালিটি `.mp4` এ ডাউনলোড হয়ে যাবে।
4. **ম্যাক ফাইন্ডারে দেখা:**
   - ভিডিও ডাউনলোড শেষ হলে সরাসরি **"Reveal in macOS Finder"** বাটনে ক্লিক করলেই ম্যাকের ফাইন্ডারে ফাইলটি হাইলাইট হয়ে ওপেন হবে।
