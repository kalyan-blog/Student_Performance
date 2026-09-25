async function generateReport(type) {
    const payload = { type };
    if (type === 'student') {
        const sid = prompt('Enter Student ID:');
        if (!sid) return;
        payload.student_id = sid;
    }
    if (type === 'department') {
        const dept = prompt('Enter Department name:');
        if (!dept) return;
        payload.department = dept;
    }

    try {
        const res = await fetch(`${API_URL}/api/reports/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(payload)
        });

        if (!res.ok) {
            const err = await res.json();
            showToast(err.error || 'Failed to generate report', 'error');
            return;
        }

        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${type}_report_${new Date().toISOString().slice(0, 10)}.pdf`;
        a.click();
        URL.revokeObjectURL(url);
        showToast('Report generated and downloaded', 'success');
        loadReports();
    } catch (e) {
        showToast('Failed to generate report', 'error');
    }
}

async function loadReports() {
    try {
        const res = await fetch(`${API_URL}/api/reports/history`, { credentials: 'include' });
        const data = await res.json();
        const tbody = document.getElementById('reportsTableBody');
        if (!tbody) return;
        if (!data.reports || data.reports.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted py-4">No reports generated</td></tr>';
            return;
        }
        tbody.innerHTML = data.reports.map(r => `
            <tr>
                <td><strong>${r.report_name || 'Report'}</strong></td>
                <td><span class="badge bg-primary">${r.report_type}</span></td>
                <td>${formatDate(r.created_at)}</td>
                <td class="actions">
                    <button class="btn btn-sm btn-outline-primary" onclick="generateReport('${r.report_type}')"><i class="fas fa-download"></i></button>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteReport('${r.id}')"><i class="fas fa-trash"></i></button>
                </td>
            </tr>
        `).join('');
    } catch { showToast('Failed to load reports', 'error'); }
}

async function deleteReport(id) {
    if (!confirm('Delete this report?')) return;
    try {
        await fetch(`${API_URL}/api/reports/${id}`, { method: 'DELETE', credentials: 'include' });
        showToast('Report deleted', 'success');
        loadReports();
    } catch { showToast('Failed to delete report', 'error'); }
}

document.addEventListener('DOMContentLoaded', () => {
    if (window.location.pathname.includes('reports.html')) loadReports();
});