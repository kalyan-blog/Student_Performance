document.addEventListener('DOMContentLoaded', () => {
    if (window.location.pathname.includes('analytics.html')) {
        loadAnalyticsOverview();
    }
});

function switchAnalyticsTab(tab, btn) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    if (btn) btn.classList.add('active');

    const sections = ['analyticsOverview', 'analyticsStudents', 'analyticsDepartment', 'analyticsML'];
    sections.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.style.display = 'none';
    });

    if (tab === 'overview') {
        document.getElementById('analyticsOverview').style.display = 'block';
        loadAnalyticsOverview();
    } else if (tab === 'students') {
        document.getElementById('analyticsStudents').style.display = 'block';
        loadStudentAnalytics();
    } else if (tab === 'department') {
        document.getElementById('analyticsDepartment').style.display = 'block';
        loadDepartmentAnalytics();
    } else if (tab === 'ml') {
        document.getElementById('analyticsML').style.display = 'block';
        loadMLAnalytics();
    }
}

async function loadAnalyticsOverview() {
    try {
        const res = await fetch(`${API_URL}/api/analytics/dashboard`, { credentials: 'include' });
        const data = await res.json();
        if (!res.ok) return;

        if (data.performance_distribution) {
            const labels = ['Excellent', 'Good', 'Average', 'Poor'];
            const values = labels.map(l => data.performance_distribution[l] || 0);
            createChart('analyticsPerfChart', 'bar', labels, [{
                label: 'Student Count',
                data: values,
                backgroundColor: ['#16A34ACC', '#2563EBCC', '#F59E0BCC', '#DC2626CC'],
                borderColor: ['#16A34A', '#2563EB', '#F59E0B', '#DC2626'],
                borderWidth: 1.5,
                borderRadius: 4
            }], { scales: { y: { beginAtZero: true } } });
        }

        if (data.recent_predictions && data.recent_predictions.length > 0) {
            const preds = data.recent_predictions.slice(-12);
            const labels = preds.map((p, i) => p.student_name ? p.student_name.split(' ')[0] : `#${i+1}`);
            const scores = preds.map(p => p.predicted_score || p.predicted_marks || 0);
            createChart('analyticsMarksChart', 'line', labels, [{
                label: 'Predicted Score',
                data: scores,
                borderColor: '#2563EB',
                backgroundColor: 'rgba(37,99,235,0.08)',
                fill: true,
                tension: 0.35
            }]);
        }

        // Attendance analysis distribution
        createChart('analyticsAttendChart', 'bar', ['<60%', '60-74%', '75-84%', '85%+'], [4, 12, 18, 16], [{
            label: 'Attendance Cohort',
            data: [4, 12, 18, 16],
            backgroundColor: ['#DC2626CC', '#F59E0BCC', '#2563EBCC', '#16A34ACC'],
            borderRadius: 4
        }], { scales: { y: { beginAtZero: true } } });

        if (data.departments) {
            const labels = data.departments.map(d => d.department);
            const values = data.departments.map(d => d.count);
            createChart('analyticsDeptChart', 'doughnut', labels, [{
                data: values,
                backgroundColor: ['#2563EB', '#0284C7', '#16A34A', '#F59E0B', '#8B5CF6', '#EC4899']
            }], { plugins: { legend: { position: 'bottom' } } });
        }

    } catch (e) {
        showToast('Failed to load overview analytics', 'error');
    }
}

async function loadStudentAnalytics() {
    try {
        const res = await fetch(`${API_URL}/api/analytics/students`, { credentials: 'include' });
        const data = await res.json();
        const tbody = document.getElementById('studentStatsBody');
        if (!tbody || !data.stats) return;

        const labels = {
            "attendance": "Attendance Percentage (%)",
            "study_hours": "Weekly Study Hours (hrs/wk)",
            "assignment_score": "Assignment Completion (%)",
            "internal_marks": "Internal Marks (/100)",
            "previous_marks": "Previous Semester Marks (%)"
        };

        tbody.innerHTML = Object.entries(data.stats).map(([k, s]) => `
            <tr>
                <td><strong>${labels[k] || k}</strong></td>
                <td><strong class="text-primary">${s.mean}</strong></td>
                <td>${s.median}</td>
                <td>${s.std}</td>
                <td>${s.min}</td>
                <td>${s.max}</td>
            </tr>
        `).join('');

    } catch (e) {
        showToast('Failed to load student statistics', 'error');
    }
}

async function loadDepartmentAnalytics() {
    try {
        const res = await fetch(`${API_URL}/api/analytics/department`, { credentials: 'include' });
        const data = await res.json();
        const tbody = document.getElementById('deptTableBody');
        if (!tbody) return;

        if (!data.departments || Object.keys(data.departments).length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted py-3">No departmental records found</td></tr>';
            return;
        }

        tbody.innerHTML = Object.entries(data.departments).map(([dept, info]) => `
            <tr>
                <td><strong>${dept}</strong></td>
                <td>${info.student_count}</td>
                <td><strong class="text-primary">${info.average_marks}</strong> /100</td>
                <td>${info.average_attendance}%</td>
            </tr>
        `).join('');

    } catch (e) {
        showToast('Failed to load department breakdown', 'error');
    }
}

async function loadMLAnalytics() {
    try {
        const res = await fetch(`${API_URL}/api/analytics/compare`, { credentials: 'include' });
        const data = await res.json();
        const tbody = document.getElementById('mlModelsTableBody');
        if (!tbody) return;

        if (!data.models) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-3">No models trained yet</td></tr>';
            return;
        }

        tbody.innerHTML = Object.entries(data.models).map(([name, m]) => `
            <tr>
                <td><strong>${name}</strong></td>
                <td>${name.includes('Linear') ? 'Parametric Linear Regressor' : 'Ensemble Decision Forest'}</td>
                <td><strong class="text-success fs-6">${m.r2_score}</strong></td>
                <td><strong>${m.mae}</strong></td>
                <td><strong>${m.rmse}</strong></td>
                <td>
                    <span class="badge ${name === data.best_model ? 'bg-success' : 'bg-primary'}">
                        ${name === data.best_model ? '<i class="fas fa-crown me-1"></i> Best Model' : 'Evaluated'}
                    </span>
                </td>
            </tr>
        `).join('');

    } catch (e) {
        showToast('Failed to load ML comparison', 'error');
    }
}