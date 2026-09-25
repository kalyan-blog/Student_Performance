async function checkAuth() {
    try {
        const res = await fetch(`${API_URL}/api/auth/session`, { credentials: 'include' });
        if (!res.ok) {
            if (!window.location.pathname.includes('login.html') && !window.location.pathname.includes('register.html') && !window.location.pathname.includes('forgot-password.html') && window.location.pathname !== '/') {
                window.location.href = 'login.html';
            }
            return;
        }
        const data = await res.json();
        if (data.user) {
            updateUI(data.user);
            if (data.user.role === 'admin') {
                const navUsers = document.getElementById('navUsers');
                if (navUsers) navUsers.style.display = 'flex';
            }
            if (window.location.pathname.includes('login.html') || window.location.pathname.includes('register.html')) {
                window.location.href = 'dashboard.html';
            }
        }
    } catch (err) {
        console.error('Auth check failed:', err);
    }
}

function updateUI(user) {
    const elements = ['sidebarName', 'sidebarRole', 'sidebarAvatar', 'topbarAvatar'];
    elements.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            if (id === 'sidebarName') el.textContent = user.name || 'User';
            else if (id === 'sidebarRole') el.textContent = user.role || 'Faculty';
            else el.textContent = (user.name || 'U').charAt(0).toUpperCase();
        }
    });
}

function logout() {
    fetch(`${API_URL}/api/auth/logout`, {
        method: 'POST',
        credentials: 'include'
    }).finally(() => {
        window.location.href = 'login.html';
    });
}

function refreshDashboard() {
    if (window.location.pathname.includes('dashboard.html')) {
        loadDashboard();
    }
}

function showNotifications() {
    showToast('No new notifications', 'info');
}

async function loadUsers() {
    try {
        const res = await fetch(`${API_URL}/api/auth/users`, { credentials: 'include' });
        const data = await res.json();
        const body = document.getElementById('usersModalBody');
        if (!body) return;
        if (!res.ok) { body.innerHTML = `<p class="text-danger">${data.error}</p>`; return; }
        let html = '<table class="data-table"><thead><tr><th>Name</th><th>Email</th><th>Role</th><th>Actions</th></tr></thead><tbody>';
        data.users.forEach(u => {
            html += `<tr><td>${u.name}</td><td>${u.email}</td><td><span class="badge bg-${u.role === 'admin' ? 'danger' : 'primary'}">${u.role}</span></td><td><button class="btn btn-sm btn-danger" onclick="deleteUser('${u.id}')"><i class="fas fa-trash"></i></button></td></tr>`;
        });
        html += '</tbody></table>';
        body.innerHTML = html;
    } catch (e) {
        showToast('Failed to load users', 'error');
    }
}

async function deleteUser(id) {
    if (!confirm('Delete this user?')) return;
    try {
        await fetch(`${API_URL}/api/auth/users/${id}`, { method: 'DELETE', credentials: 'include' });
        showToast('User deleted', 'success');
        loadUsers();
    } catch { showToast('Failed to delete user', 'error'); }
}

document.addEventListener('DOMContentLoaded', () => {
    const usersModal = document.getElementById('usersModal');
    if (usersModal) {
        usersModal.addEventListener('show.bs.modal', loadUsers);
    }
    const navUsers = document.getElementById('navUsers');
    if (navUsers) {
        navUsers.addEventListener('click', () => {
            const usersModal = new bootstrap.Modal(document.getElementById('usersModal'));
            usersModal.show();
        });
    }
});