# 🌐 How to Publish Instagram Video Downloader Online

You can publish this application online so that **anyone on mobile (iOS/Android), tablet, or PC** can open the website and download Instagram videos directly to their device.

---

## 🚀 Option 1: Host Free from your Mac mini M4 (Cloudflare Tunnel) - ⭐ RECOMMENDED

Since you have a **Mac mini M4**, you can use it as a 24/7 high-speed server. 
With **Cloudflare Tunnel (100% Free)**:
- No router port-forwarding needed.
- Free SSL (HTTPS) certificate provided.
- **Huge Advantage**: Traffic comes from your home residential IP, so Instagram will NOT block you like it does with cloud datacenters (AWS/DigitalOcean)!

### Steps:
1. Install Cloudflare Tunnel on your Mac:
   ```bash
   brew install cloudflared
   ```
2. Start your downloader:
   ```bash
   ./start.sh
   ```
3. In a new terminal tab, launch the tunnel:
   ```bash
   cloudflared tunnel --url http://localhost:5055
   ```
4. Cloudflare will give you a public URL like:
   👉 `https://apple-banana-1234.trycloudflare.com`

Share this link with anyone! They can open it on their iPhone or PC, paste an Instagram link, and the MP4 video will download straight to their device.

*(Optional: You can also connect your own custom domain, e.g. `insta.yourdomain.com`, for free in the Cloudflare Dashboard!)*

---

## ☁️ Option 2: Deploy to Railway / Render (Cloud Container)

If you want the website running in the cloud without keeping your Mac turned on:

### Deploying to Railway.app:
1. Push your code to a GitHub repository:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   gh repo create instagram-downloader --public --push --source=.
   ```
2. Go to [railway.app](https://railway.app) and click **"New Project"** -> **"Deploy from GitHub repo"**.
3. Select your repository. Railway will automatically detect the `Dockerfile`, install FFmpeg and Python, and deploy your site with a free HTTPS domain.

---

## 🖥️ Option 3: Deploy to a Linux VPS (DigitalOcean / Hetzner)

For full control, scalability, and handling high user traffic:
1. Rent a $4–$5/mo VPS (Ubuntu 22.04/24.04).
2. Clone your repository:
   ```bash
   git clone <your-repo-url>
   cd "Instagram video downloader"
   ```
3. Run with Docker Compose:
   ```bash
   docker compose up -d --build
   ```
4. Point your domain with Nginx + Certbot (Free Let's Encrypt SSL).

---

## ⚠️ Important Considerations for Public Multi-User Websites

1. **Direct Device Download**:
   - The app is already configured so that when a remote user on a phone or laptop clicks Download, the browser triggers a direct file download (`/api/download-file/{filename}`) straight to their phone's Files / Gallery or computer's Downloads.

2. **Instagram IP Rate Limiting (Cloud vs Home IP)**:
   - When hosted on Cloud Datacenters (AWS, DigitalOcean, Hetzner), Instagram might periodically prompt for login because thousands of bots share those datacenter IP ranges.
   - **Solution A**: Host on your Mac mini M4 (Option 1) using residential IP.
   - **Solution B**: Keep a valid Instagram `sessionid` configured in the server's Settings.
   - **Solution C**: For commercial scale, configure a rotating residential proxy in `engine.py` (e.g. Smartproxy, Webshare, BrightData).

3. **Storage Auto-Cleanup**:
   - The server is equipped with automated storage management so downloaded video cache older than 2 hours is purged to keep server disk space healthy.
