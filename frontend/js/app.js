const API_URL = window.API_URL || (window.__ENV__ && window.__ENV__.API_URL) || window.location.origin;
let currentPage = 1;
let charts = {};

function showToast(message, type = 'info') {
    const container = document.getElementById('notifContainer');
    if (!container) return;
    const icons = { success: 'fa-check-circle', error: 'fa-times-circle', warning: 'fa-exclamation-circle', info: 'fa-info-circle' };
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<i class="fas ${icons[type] || icons.info}"></i><span>${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => { toast.style.opacity = '0'; toast.style.transform = 'translateX(100%)'; toast.style.transition = 'all 0.3s'; setTimeout(() => toast.remove(), 300); }, 3000);
}

function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('open');
    const overlay = document.getElementById('sidebarOverlay');
    if (overlay) overlay.classList.toggle('active');
}

function toggleTheme() {
    const html = document.documentElement;
    const icon = document.getElementById('themeIcon');
    const isDark = html.getAttribute('data-theme') === 'dark';
    html.setAttribute('data-theme', isDark ? 'light' : 'dark');
    if (icon) icon.className = isDark ? 'fas fa-moon' : 'fas fa-sun';
    localStorage.setItem('theme', isDark ? 'light' : 'dark');
}

function loadTheme() {
    const saved = localStorage.getItem('theme');
    if (saved) {
        document.documentElement.setAttribute('data-theme', saved);
        const icon = document.getElementById('themeIcon');
        if (icon) icon.className = saved === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
    }
}

function setLoading(btnId, loading, text = 'Loading...') {
    const btn = document.getElementById(btnId);
    if (!btn) return;
    if (loading) {
        btn.disabled = true;
        btn.innerHTML = `<span class="spinner"></span> ${text}`;
    } else {
        btn.disabled = false;
        btn.innerHTML = text;
    }
}

function formatDate(dateStr) {
    if (!dateStr) return '-';
    try {
        const d = new Date(dateStr);
        return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
    } catch { return dateStr; }
}

function getGradeBadge(grade) {
    const colors = { 'A+': 'grade-A', 'A': 'grade-A', 'B+': 'grade-B', 'B': 'grade-B', 'C': 'grade-C', 'D': 'grade-D', 'F': 'grade-F' };
    return `<span class="grade-badge ${colors[grade] || 'grade-C'}">${grade || 'N/A'}</span>`;
}

function getRiskBadge(risk) {
    const r = String(risk || 'Low Risk').toLowerCase();
    if (r.includes('high')) {
        return `<span class="risk-badge risk-high"><i class="fas fa-triangle-exclamation"></i> High Risk</span>`;
    } else if (r.includes('mod') || r.includes('med')) {
        return `<span class="risk-badge risk-moderate"><i class="fas fa-exclamation-triangle"></i> Moderate Risk</span>`;
    } else {
        return `<span class="risk-badge risk-low"><i class="fas fa-shield-check"></i> Low Risk</span>`;
    }
}

function getPerformanceBadge(perf) {
    const p = String(perf || 'Average');
    const classes = { 'Excellent': 'perf-excellent', 'Good': 'perf-good', 'Average': 'perf-average', 'Poor': 'perf-poor' };
    return `<span class="perf-badge ${classes[p] || 'perf-average'}">${p}</span>`;
}

function paginate(totalPages, current, containerId, callback) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = '';
    if (totalPages <= 1) return;
    container.innerHTML += `<button onclick="${callback}(1)" ${current === 1 ? 'disabled' : ''}><i class="fas fa-chevron-left"></i></button>`;
    for (let i = Math.max(1, current - 2); i <= Math.min(totalPages, current + 2); i++) {
        container.innerHTML += `<button class="${i === current ? 'active' : ''}" onclick="${callback}(${i})">${i}</button>`;
    }
    container.innerHTML += `<button onclick="${callback}(${totalPages})" ${current === totalPages ? 'disabled' : ''}><i class="fas fa-chevron-right"></i></button>`;
}

function showModal(id) {
    const modal = document.getElementById(id);
    if (modal) modal.classList.add('active');
}

function hideModal(id) {
    const modal = document.getElementById(id);
    if (modal) modal.classList.remove('active');
}

function logout() {
    fetch(`${API_URL}/api/auth/logout`, { method: 'POST', credentials: 'include' })
        .finally(() => { window.location.href = 'login.html'; });
}

async function checkDatabaseHealth() {
    const label = document.getElementById('dbStatusLabel');
    const dot = document.getElementById('dbIndicatorDot');
    if (!label && !dot) return;
    try {
        const res = await fetch(`${API_URL}/api/health`);
        const data = await res.json();
        if (res.ok && data.database === 'connected') {
            if (label) label.innerHTML = `Database: <strong class="text-success">Connected</strong>`;
            if (dot) dot.style.background = '#16a34a';
        } else {
            if (label) label.innerHTML = `Database: <strong class="text-danger">Disconnected</strong>`;
            if (dot) dot.style.background = '#dc2626';
        }
    } catch {
        if (label) label.innerHTML = `Database: <strong class="text-danger">Disconnected</strong>`;
        if (dot) dot.style.background = '#dc2626';
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    loadTheme();
    checkAuth();
    checkDatabaseHealth();
});