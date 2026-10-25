/**
 * Main Application Logic
 * InstaDownloader Pro - Mac mini M4
 */

document.addEventListener("DOMContentLoaded", () => {
  // State
  let currentMode = "single"; // 'single' | 'channel'
  let currentExtractedData = null;
  let activeTaskId = null;
  let activeSocket = null;
  let selectedChannelVideoUrls = new Set();
  let currentDownloadedFile = null;

  // DOM Elements
  const tabSingleBtn = document.getElementById("tab-single-btn");
  const tabChannelBtn = document.getElementById("tab-channel-btn");
  const urlInput = document.getElementById("url-input");
  const btnPaste = document.getElementById("btn-paste-clipboard");
  const downloadForm = document.getElementById("download-form");
  const btnAnalyze = document.getElementById("btn-analyze");
  const btnSubmitText = document.getElementById("btn-submit-text");

  // Single Video Preview Elements
  const singlePreviewCard = document.getElementById("single-preview-card");
  const previewThumbnail = document.getElementById("preview-thumbnail");
  const previewBadge = document.getElementById("preview-badge");
  const previewDuration = document.getElementById("preview-duration");
  const previewUploader = document.getElementById("preview-uploader");
  const previewTitle = document.getElementById("preview-title");
  const previewCaption = document.getElementById("preview-caption");
  const specResolution = document.getElementById("spec-resolution");
  const btnStartSingleDownload = document.getElementById("btn-start-single-download");

  // Download Progress Elements
  const progressCard = document.getElementById("download-progress-card");
  const progressBarFill = document.getElementById("progress-bar-fill");
  const progressPercentLabel = document.getElementById("progress-percent-label");
  const progressStatusLabel = document.getElementById("progress-status-label");
  const progressSpeed = document.getElementById("progress-speed");
  const progressDownloaded = document.getElementById("progress-downloaded");
  const progressEta = document.getElementById("progress-eta");
  const progressSpinner = document.getElementById("progress-spinner");
  const completeActions = document.getElementById("complete-actions");
  const btnRevealCurrent = document.getElementById("btn-reveal-current");
  const btnPlayCurrent = document.getElementById("btn-play-current");

  // Channel Elements
  const channelView = document.getElementById("channel-view-container");
  const channelAvatar = document.getElementById("channel-avatar");
  const channelFullName = document.getElementById("channel-full-name");
  const channelUsername = document.getElementById("channel-username");
  const channelBio = document.getElementById("channel-bio");
  const channelFollowers = document.getElementById("channel-followers");
  const channelVideoCount = document.getElementById("channel-video-count");
  const channelVideosGrid = document.getElementById("channel-videos-grid");
  const channelSelectionCount = document.getElementById("channel-selection-count");
  const btnSelectAll = document.getElementById("btn-select-all");
  const btnDeselectAll = document.getElementById("btn-deselect-all");
  const btnBatchDownload = document.getElementById("btn-batch-download");
  const btnBatchDownloadText = document.getElementById("btn-batch-download-text");

  // Library Elements
  const historyGrid = document.getElementById("history-grid");
  const btnRefreshHistory = document.getElementById("btn-refresh-history");
  const btnOpenFolder = document.getElementById("btn-open-folder");

  // Settings & Session Elements
  const sessionDot = document.getElementById("session-dot");
  const sessionStatusText = document.getElementById("session-status-text");
  const btnSessionStatus = document.getElementById("btn-session-status");
  const btnOpenSettings = document.getElementById("btn-open-settings");
  const settingsModal = document.getElementById("settings-modal");
  const btnCloseSettings = document.getElementById("btn-close-settings");
  const btnCancelSettings = document.getElementById("btn-cancel-settings");
  const btnSaveSettings = document.getElementById("btn-save-settings");
  const settingSessionId = document.getElementById("setting-session-id");
  const settingDownloadDir = document.getElementById("setting-download-dir");
  const cookieDropzone = document.getElementById("cookie-dropzone");
  const cookieFileInput = document.getElementById("cookie-file-input");

  // Video Player Modal Elements
  const playerModal = document.getElementById("player-modal");
  const btnClosePlayer = document.getElementById("btn-close-player");
  const html5VideoPlayer = document.getElementById("html5-video-player");
  const playerModalTitle = document.getElementById("player-modal-title");
  const btnPlayerFinder = document.getElementById("btn-player-finder");
  const btnPlayerDownloadLink = document.getElementById("btn-player-download-link");

  // -------------------------------------------------------------
  // INITIALIZATION
  // -------------------------------------------------------------
  loadSettings();
  loadHistory();

  // Mode Switchers
  tabSingleBtn.addEventListener("click", () => setMode("single"));
  tabChannelBtn.addEventListener("click", () => setMode("channel"));

  function setMode(mode) {
    currentMode = mode;
    if (mode === "single") {
      tabSingleBtn.classList.add("active");
      tabChannelBtn.classList.remove("active");
      urlInput.placeholder = "Paste Instagram Reel or Video URL (e.g. https://www.instagram.com/reel/...)";
      btnSubmitText.textContent = "Fetch Video";
      channelView.style.display = "none";
    } else {
      tabChannelBtn.classList.add("active");
      tabSingleBtn.classList.remove("active");
      urlInput.placeholder = "Enter Instagram Channel @handle or URL (e.g. @natgeo or instagram.com/natgeo)";
      btnSubmitText.textContent = "Explore Channel";
      singlePreviewCard.style.display = "none";
    }
  }

  // Clipboard Paste Helper
  btnPaste.addEventListener("click", async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text) {
        urlInput.value = text.trim();
        UI.showToast("Pasted from clipboard!", "info");
        handleAnalyze();
      }
    } catch (err) {
      UI.showToast("Clipboard access denied. Please paste manually.", "error");
    }
  });

  // Submit Handler
  downloadForm.addEventListener("submit", (e) => {
    e.preventDefault();
    handleAnalyze();
  });

  // -------------------------------------------------------------
  // EXTRACT / ANALYZE URL
  // -------------------------------------------------------------
  async function handleAnalyze() {
    const rawUrl = urlInput.value.trim();
    if (!rawUrl) {
      UI.showToast("Please enter an Instagram URL or username", "error");
      return;
    }

    UI.setLoading(btnAnalyze, true, btnSubmitText.textContent, "Analyzing...");
    singlePreviewCard.style.display = "none";
    channelView.style.display = "none";
    progressCard.style.display = "none";

    try {
      const res = await fetch("/api/extract", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: rawUrl }),
      });
      const data = await res.json();

      if (!data.success) {
        throw new Error(data.error || "Failed to analyze target");
      }

      currentExtractedData = data.data;

      if (currentExtractedData.type === "video") {
        renderSingleVideoPreview(currentExtractedData);
        setMode("single");
      } else if (currentExtractedData.type === "channel") {
        renderChannelView(currentExtractedData);
        setMode("channel");
      }

      UI.showToast("Target analyzed successfully!", "success");
    } catch (err) {
      UI.showToast(err.message, "error");
    } finally {
      UI.setLoading(btnAnalyze, false, currentMode === "single" ? "Fetch Video" : "Explore Channel");
    }
  }

  // -------------------------------------------------------------
  // RENDER SINGLE VIDEO PREVIEW
  // -------------------------------------------------------------
  function renderSingleVideoPreview(video) {
    previewThumbnail.src = video.thumbnail || "/static/assets/icon.svg";
    previewBadge.textContent = video.resolution || "Full Original HD";
    previewDuration.textContent = video.duration_str || "Video";
    previewUploader.textContent = `@${video.uploader}`;
    previewTitle.textContent = video.title || "Instagram Video";
    previewCaption.textContent = video.caption || "No caption provided.";
    specResolution.textContent = video.resolution || "Highest Available";

    singlePreviewCard.style.display = "block";
    singlePreviewCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  // Start Single Download
  btnStartSingleDownload.addEventListener("click", () => {
    if (!currentExtractedData || !currentExtractedData.webpage_url) return;
    startDownload(currentExtractedData.webpage_url);
  });

  // -------------------------------------------------------------
  // DOWNLOAD LOGIC & WEBSOCKET PROGRESS
  // -------------------------------------------------------------
  async function startDownload(videoUrl) {
    progressCard.style.display = "block";
    progressCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
    completeActions.style.display = "none";
    progressBarFill.style.width = "0%";
    progressPercentLabel.textContent = "0%";
    progressStatusLabel.textContent = "Connecting to Instagram stream...";
    progressSpinner.style.display = "block";

    try {
      const res = await fetch("/api/download", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: videoUrl }),
      });
      const data = await res.json();

      if (!data.success) {
        throw new Error(data.error || "Failed to start download");
      }

      activeTaskId = data.task_id;
      connectWebSocket(activeTaskId);
    } catch (err) {
      UI.showToast(err.message, "error");
      progressCard.style.display = "none";
    }
  }

  function connectWebSocket(taskId) {
    if (activeSocket) {
      activeSocket.close();
    }

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws/progress/${taskId}`;

    let wsConnected = false;

    try {
      activeSocket = new WebSocket(wsUrl);

      activeSocket.onopen = () => {
        wsConnected = true;
      };

      activeSocket.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        updateProgressUI(msg);
      };

      activeSocket.onerror = () => {
        pollTaskProgress(taskId);
      };

      // If WebSocket closes before finished, fall back to polling
      activeSocket.onclose = () => {
        if (activeTaskId === taskId) {
          pollTaskProgress(taskId);
        }
      };

      // Timeout: if WS not connected in 3s, start polling in parallel
      setTimeout(() => {
        if (!wsConnected) {
          pollTaskProgress(taskId);
        }
      }, 3000);

    } catch (e) {
      pollTaskProgress(taskId);
    }
  }

  let _pollingActive = {};
  function pollTaskProgress(taskId) {
    if (_pollingActive[taskId]) return; // Don't double-poll
    _pollingActive[taskId] = true;

    const interval = setInterval(async () => {
      try {
        const res = await fetch(`/api/progress/${taskId}`);
        if (res.ok) {
          const msg = await res.json();
          updateProgressUI(msg);
          if (msg.status === "finished" || msg.status === "error") {
            clearInterval(interval);
            delete _pollingActive[taskId];
          }
        }
      } catch (e) {
        clearInterval(interval);
        delete _pollingActive[taskId];
      }
    }, 1000);
  }

  function updateProgressUI(data) {
    if (data.status === "downloading") {
      progressBarFill.style.width = `${data.progress_percent}%`;
      progressPercentLabel.textContent = `${data.progress_percent}%`;
      progressStatusLabel.textContent = "Downloading stream in full resolution...";
      progressSpeed.textContent = `Speed: ${data.speed || "0 KB/s"}`;
      progressEta.textContent = `ETA: ${data.eta || "--:--"}`;
      progressDownloaded.textContent = `${UI.formatBytes(data.downloaded_bytes)} / ${UI.formatBytes(data.total_bytes)}`;
    } else if (data.status === "converting") {
      progressBarFill.style.width = "100%";
      progressPercentLabel.textContent = "100%";
      progressStatusLabel.textContent = "Remuxing to strict .MP4 via FFmpeg...";
      // Show save button hint during conversion (file not ready yet, but visible)
      progressSpinner.style.display = "block";
    } else if (data.status === "finished") {
      progressBarFill.style.width = "100%";
      progressPercentLabel.textContent = "100%";
      progressStatusLabel.textContent = `✓ Completed: ${data.filename || "Video saved"}`;
      progressSpinner.style.display = "none";
      completeActions.style.display = "flex";
      activeTaskId = null; // Stop polling

      const btnSaveDevice = document.getElementById("btn-save-device");
      if (btnSaveDevice && data.filename) {
        const dlUrl = `/api/download-file/${encodeURIComponent(data.filename)}`;
        btnSaveDevice.href = dlUrl;
        btnSaveDevice.download = data.filename;
        btnSaveDevice.style.display = "inline-flex";
        // Auto-trigger download after short delay
        setTimeout(() => {
          const a = document.createElement("a");
          a.href = dlUrl;
          a.download = data.filename;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
        }, 600);
      }

      currentDownloadedFile = {
        filename: data.filename,
        filepath: data.filepath,
      };

      UI.showToast("✅ Video ready! Saving to your device...", "success");
      loadHistory();
    } else if (data.status === "error") {
      progressStatusLabel.textContent = `✗ Error: ${data.error || "Download failed"}`;
      progressSpinner.style.display = "none";
      UI.showToast(data.error || "Download failed", "error");
    }
  }


  // Finder reveal for current downloaded file
  btnRevealCurrent.addEventListener("click", () => {
    if (currentDownloadedFile && currentDownloadedFile.filepath) {
      revealInFinder(currentDownloadedFile.filepath);
    }
  });

  // Play current downloaded file
  btnPlayCurrent.addEventListener("click", () => {
    if (currentDownloadedFile && currentDownloadedFile.filename) {
      openVideoPlayer(currentDownloadedFile.filename);
    }
  });

  // -------------------------------------------------------------
  // RENDER CHANNEL VIEW & BATCH SELECTION
  // -------------------------------------------------------------
  function renderChannelView(channel) {
    channelAvatar.src = channel.avatar || "/static/assets/icon.svg";
    channelFullName.textContent = channel.full_name || channel.username;
    channelUsername.textContent = `@${channel.username}`;
    channelBio.textContent = channel.biography || "No bio description.";
    channelFollowers.textContent = Number(channel.follower_count || 0).toLocaleString();
    channelVideoCount.textContent = (channel.videos || []).length;

    selectedChannelVideoUrls.clear();
    channelVideosGrid.innerHTML = "";

    const videos = channel.videos || [];
    if (videos.length === 0) {
      channelVideosGrid.innerHTML = `
        <div class="empty-history" style="grid-column: 1 / -1;">
          No public video reels found for this profile. If this account is private or age-restricted, please add your session ID in Settings.
        </div>
      `;
    } else {
      videos.forEach((v) => {
        selectedChannelVideoUrls.add(v.url); // default select all

        const card = document.createElement("div");
        card.className = "channel-item-card selected";
        card.dataset.url = v.url;

        card.innerHTML = `
          <div class="channel-thumb-box">
            <img src="${v.thumbnail || '/static/assets/icon.svg'}" alt="Reel thumbnail" class="channel-thumb-img" loading="lazy">
            <div class="select-checkbox">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"/>
              </svg>
            </div>
            <span class="duration-pill">${v.duration_str || 'Reel'}</span>
          </div>
          <div class="channel-card-body">
            <div class="channel-card-title">${v.title || 'Reel'}</div>
            <div class="channel-card-footer">
              <span style="font-size: 0.72rem; color: var(--accent-cyan); font-weight: 600;">Full Quality .MP4</span>
              <button class="btn-mini-download" title="Download this reel now">
                <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
                </svg>
              </button>
            </div>
          </div>
        `;

        // Card Click Selection
        card.addEventListener("click", (e) => {
          if (e.target.closest(".btn-mini-download")) {
            e.stopPropagation();
            startDownload(v.url);
            return;
          }
          if (selectedChannelVideoUrls.has(v.url)) {
            selectedChannelVideoUrls.delete(v.url);
            card.classList.remove("selected");
          } else {
            selectedChannelVideoUrls.add(v.url);
            card.classList.add("selected");
          }
          updateChannelSelectionCount();
        });

        channelVideosGrid.appendChild(card);
      });
    }

    updateChannelSelectionCount();
    channelView.style.display = "block";
    channelView.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  function updateChannelSelectionCount() {
    channelSelectionCount.textContent = `${selectedChannelVideoUrls.size} selected`;
    btnBatchDownloadText.textContent = `Download Selected (${selectedChannelVideoUrls.size})`;
    btnBatchDownload.disabled = selectedChannelVideoUrls.size === 0;
  }

  btnSelectAll.addEventListener("click", () => {
    document.querySelectorAll(".channel-item-card").forEach((card) => {
      card.classList.add("selected");
      selectedChannelVideoUrls.add(card.dataset.url);
    });
    updateChannelSelectionCount();
  });

  btnDeselectAll.addEventListener("click", () => {
    document.querySelectorAll(".channel-item-card").forEach((card) => {
      card.classList.remove("selected");
    });
    selectedChannelVideoUrls.clear();
    updateChannelSelectionCount();
  });

  // Batch Download Trigger
  btnBatchDownload.addEventListener("click", async () => {
    if (selectedChannelVideoUrls.size === 0) return;
    const urls = Array.from(selectedChannelVideoUrls);

    UI.setLoading(btnBatchDownload, true, btnBatchDownloadText.textContent, "Starting Batch...");

    try {
      const res = await fetch("/api/channel/batch-download", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          urls: urls,
          username: currentExtractedData ? currentExtractedData.username : "instagram",
        }),
      });
      const data = await res.json();
      if (!data.success) throw new Error(data.error || "Batch failed to start");

      UI.showToast(`Batch queued! Downloading ${urls.length} videos in background.`, "success");
      trackBatchProgress(data.batch_id);
    } catch (err) {
      UI.showToast(err.message, "error");
    } finally {
      UI.setLoading(btnBatchDownload, false, `Download Selected (${selectedChannelVideoUrls.size})`);
    }
  });

  function trackBatchProgress(batchId) {
    progressCard.style.display = "block";
    progressCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
    progressStatusLabel.textContent = "Processing channel batch download...";

    const interval = setInterval(async () => {
      try {
        const res = await fetch(`/api/channel/batch-progress/${batchId}`);
        if (res.ok) {
          const tracker = await res.json();
          const percent = Math.round(((tracker.completed + tracker.failed) / tracker.total) * 100);
          progressBarFill.style.width = `${percent}%`;
          progressPercentLabel.textContent = `${percent}%`;
          progressStatusLabel.textContent = `Batch: ${tracker.completed} of ${tracker.total} downloaded`;
          progressSpeed.textContent = `Items: ${tracker.total}`;
          progressEta.textContent = tracker.status === "completed" ? "Done" : "Downloading...";

          if (tracker.status === "completed") {
            clearInterval(interval);
            progressSpinner.style.display = "none";
            completeActions.style.display = "flex";
            UI.showToast(`Batch finished! ${tracker.completed} videos saved in full quality.`, "success");
            loadHistory();
          }
        }
      } catch (e) {
        clearInterval(interval);
      }
    }, 1500);
  }

  // -------------------------------------------------------------
  // DOWNLOAD HISTORY & LIBRARY
  // -------------------------------------------------------------
  async function loadHistory() {
    try {
      const res = await fetch("/api/history");
      const data = await res.json();
      if (!data.success) return;

      historyGrid.innerHTML = "";
      const videos = data.videos || [];

      if (videos.length === 0) {
        historyGrid.innerHTML = `
          <div class="empty-history" style="grid-column: 1 / -1;">
            No downloaded videos yet. Paste any Instagram link above to download!
          </div>
        `;
        return;
      }

      videos.forEach((item) => {
        const card = document.createElement("div");
        card.className = "history-card";
        card.innerHTML = `
          <div class="history-info">
            <div class="history-filename" title="${item.filename}">${item.filename}</div>
            <div class="history-meta">
              <span>${item.filesize_str}</span>
              <span>•</span>
              <span>${item.created_at}</span>
              <span>•</span>
              <span style="color: var(--accent-green); font-weight: 600;">.MP4</span>
            </div>
          </div>
          <div class="history-actions">
            <a class="btn-history-action" href="/api/download-file/${encodeURIComponent(item.filename)}" download="${item.filename}" title="Save MP4 to your phone or PC" style="text-decoration: none; color: var(--accent-cyan); border-color: rgba(0, 242, 254, 0.3);">
              <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
              </svg>
              Save
            </a>
            <button class="btn-history-action btn-play" title="Play video">
              <svg width="14" height="14" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
              Play
            </button>
            <button class="btn-history-action btn-finder-reveal" title="Show in macOS Finder">
              <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 19a2 2 0 01-2-2V7a2 2 0 012-2h4l2 2h4a2 2 0 012 2v1M5 19h14a2 2 0 002-2v-5a2 2 0 00-2-2H9a2 2 0 00-2 2v5a2 2 0 01-2 2z"/>
              </svg>
              Finder
            </button>
          </div>
        `;

        card.querySelector(".btn-play").addEventListener("click", () => {
          openVideoPlayer(item.filename, item.filepath);
        });

        card.querySelector(".btn-finder-reveal").addEventListener("click", () => {
          revealInFinder(item.filepath);
        });

        historyGrid.appendChild(card);
      });
    } catch (e) {
      console.error("Failed to load history", e);
    }
  }

  btnRefreshHistory.addEventListener("click", () => {
    loadHistory();
    UI.showToast("Library refreshed", "info");
  });

  // Open Downloads Folder in Finder
  btnOpenFolder.addEventListener("click", async () => {
    try {
      await fetch("/api/open-downloads", { method: "POST" });
      UI.showToast("Opened Downloads folder in Finder", "info");
    } catch (e) {
      UI.showToast("Could not open folder", "error");
    }
  });

  async function revealInFinder(filePath) {
    try {
      const res = await fetch("/api/reveal", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path: filePath }),
      });
      const data = await res.json();
      if (data.success) {
        UI.showToast("Revealed file in macOS Finder", "info");
      }
    } catch (e) {
      UI.showToast("Finder reveal error", "error");
    }
  }

  // -------------------------------------------------------------
  // VIDEO PLAYER MODAL
  // -------------------------------------------------------------
  function openVideoPlayer(filename, filepath = "") {
    playerModalTitle.textContent = filename;
    html5VideoPlayer.src = `/api/media/${encodeURIComponent(filename)}`;
    btnPlayerDownloadLink.href = `/api/media/${encodeURIComponent(filename)}`;
    btnPlayerDownloadLink.setAttribute("download", filename);

    btnPlayerFinder.onclick = () => {
      revealInFinder(filepath || filename);
    };

    UI.openModal("player-modal");
    html5VideoPlayer.play().catch(() => {});
  }

  btnClosePlayer.addEventListener("click", () => {
    html5VideoPlayer.pause();
    html5VideoPlayer.src = "";
    UI.closeModal("player-modal");
  });

  playerModal.addEventListener("click", (e) => {
    if (e.target === playerModal) {
      html5VideoPlayer.pause();
      html5VideoPlayer.src = "";
      UI.closeModal("player-modal");
    }
  });

  // -------------------------------------------------------------
  // SETTINGS & COOKIES MANAGEMENT
  // -------------------------------------------------------------
  async function loadSettings() {
    try {
      const res = await fetch("/api/settings");
      const data = await res.json();
      if (!data.success) return;

      settingDownloadDir.value = data.download_dir || "";
      if (data.has_session) {
        sessionDot.classList.add("active");
        sessionStatusText.textContent = "Session Active";
        settingSessionId.placeholder = data.session_masked || "Session ID active";
      } else {
        sessionDot.classList.remove("active");
        sessionStatusText.textContent = "Guest Mode";
      }
    } catch (e) {
      console.error("Failed to load settings", e);
    }
  }

  btnSessionStatus.addEventListener("click", () => UI.openModal("settings-modal"));
  btnOpenSettings.addEventListener("click", () => UI.openModal("settings-modal"));
  btnCloseSettings.addEventListener("click", () => UI.closeModal("settings-modal"));
  btnCancelSettings.addEventListener("click", () => UI.closeModal("settings-modal"));

  settingsModal.addEventListener("click", (e) => {
    if (e.target === settingsModal) UI.closeModal("settings-modal");
  });

  btnSaveSettings.addEventListener("click", async () => {
    const sid = settingSessionId.value.trim();
    const ddir = settingDownloadDir.value.trim();

    UI.setLoading(btnSaveSettings, true, "Save Settings", "Saving...");

    try {
      const res = await fetch("/api/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sid || undefined,
          download_dir: ddir || undefined,
        }),
      });
      const data = await res.json();
      if (data.success) {
        UI.showToast("Settings saved successfully!", "success");
        UI.closeModal("settings-modal");
        loadSettings();
      }
    } catch (e) {
      UI.showToast("Failed to save settings", "error");
    } finally {
      UI.setLoading(btnSaveSettings, false, "Save Settings");
    }
  });

  // Cookie Dropzone File Upload
  cookieDropzone.addEventListener("click", () => cookieFileInput.click());

  cookieDropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    cookieDropzone.style.borderColor = "var(--accent-cyan)";
  });

  cookieDropzone.addEventListener("dragleave", () => {
    cookieDropzone.style.borderColor = "var(--border-subtle)";
  });

  cookieDropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    cookieDropzone.style.borderColor = "var(--border-subtle)";
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleCookieFileUpload(e.dataTransfer.files[0]);
    }
  });

  cookieFileInput.addEventListener("change", () => {
    if (cookieFileInput.files && cookieFileInput.files[0]) {
      handleCookieFileUpload(cookieFileInput.files[0]);
    }
  });

  async function handleCookieFileUpload(file) {
    const formData = new FormData();
    formData.append("file", file);

    try {
      UI.showToast("Importing cookies...", "info");
      const res = await fetch("/api/settings/upload-cookies", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      if (data.success) {
        UI.showToast("Cookies imported successfully!", "success");
        loadSettings();
      } else {
        throw new Error(data.detail || "Import failed");
      }
    } catch (err) {
      UI.showToast(err.message, "error");
    }
  }
});
