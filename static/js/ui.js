/**
 * UI Utilities and Interaction Handlers
 * InstaDownloader Pro - Mac mini M4
 */

const UI = {
  // Show Toast Notification
  showToast(message, type = "info") {
    const container = document.getElementById("toast-container");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.innerHTML = `
      <div class="toast-content">${message}</div>
    `;

    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transform = "translateY(8px)";
      setTimeout(() => toast.remove(), 250);
    }, 4000);
  },

  // Modal Control
  openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.add("open");
  },

  closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.remove("open");
  },

  // Set Button Loading State
  setLoading(buttonElement, isLoading, normalText = "Submit", loadingText = "Processing...") {
    if (!buttonElement) return;
    if (isLoading) {
      buttonElement.disabled = true;
      buttonElement.innerHTML = `
        <div class="spinner-icon" style="width: 16px; height: 16px; border-width: 2px;"></div>
        <span>${loadingText}</span>
      `;
    } else {
      buttonElement.disabled = false;
      buttonElement.innerHTML = `<span>${normalText}</span>`;
    }
  },

  // Format Bytes Helper
  formatBytes(bytes) {
    if (!bytes || bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB", "TB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
  },
};
