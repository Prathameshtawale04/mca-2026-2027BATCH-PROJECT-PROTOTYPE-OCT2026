/**
 * Main Application Client Scripts
 */

// Theme Management
function initTheme() {
    const savedTheme = localStorage.getItem("app_theme") || "dark";
    document.documentElement.setAttribute("data-theme", savedTheme);
    updateThemeIcon(savedTheme);
}

function toggleTheme() {
    const current = document.documentElement.getAttribute("data-theme") || "dark";
    const nextTheme = current === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", nextTheme);
    localStorage.setItem("app_theme", nextTheme);
    updateThemeIcon(nextTheme);
}

function updateThemeIcon(theme) {
    const icon = document.getElementById("theme-toggle-icon");
    if (icon) {
        if (theme === "light") {
            icon.className = "fas fa-moon";
        } else {
            icon.className = "fas fa-sun";
        }
    }
}

// Toast Notifications
function showToast(message, type = "info") {
    let container = document.getElementById("toast-container");
    if (!container) {
        container = document.createElement("div");
        container.id = "toast-container";
        document.body.appendChild(container);
    }

    const toast = document.createElement("div");
    toast.className = `toast-msg toast-${type}`;
    
    let iconClass = "fa-info-circle text-info";
    if (type === "success") iconClass = "fa-check-circle text-success";
    if (type === "warning") iconClass = "fa-exclamation-triangle text-warning";
    if (type === "danger") iconClass = "fa-times-circle text-danger";

    toast.innerHTML = `
        <i class="fas ${iconClass}"></i>
        <div style="flex: 1;">${message}</div>
    `;

    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = "0";
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// REST API Helpers
async function apiPost(url, payload = {}) {
    try {
        const response = await fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });
        const data = await response.json();
        return { ok: response.ok, status: response.status, data };
    } catch (err) {
        return { ok: false, status: 500, data: { message: err.message } };
    }
}

async function apiGet(url) {
    try {
        const response = await fetch(url);
        const data = await response.json();
        return { ok: response.ok, status: response.status, data };
    } catch (err) {
        return { ok: false, status: 500, data: { message: err.message } };
    }
}

document.addEventListener("DOMContentLoaded", () => {
    initTheme();
    const toggleBtn = document.getElementById("theme-toggle-btn");
    if (toggleBtn) {
        toggleBtn.addEventListener("click", toggleTheme);
    }
});
