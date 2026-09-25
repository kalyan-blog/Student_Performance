let atRiskPage = 1;

document.addEventListener('DOMContentLoaded', () => {
    if (window.location.pathname.includes('at-risk.html')) {
        loadAtRiskStudents();
    }
});

async function loadAtRiskStudents(page = atRiskPage) {
    atRiskPage = page;
    const search = document.getElementById('riskSearch')?.value.trim() || '';
    const riskLevel = document.getElementById('riskLevelFilter')?.value || '';
    const dept = document.getElementById('deptFilter')?.value || '';
    const sort = document.getElementById('sortFilter')?.value || 'score_asc';

    const tbody = document.getElementById('atRiskTableBody');
    const pagination = document.getElementById('atRiskPagination');

    try {
        const url = `${API_URL}/api/students/at-risk?page=${page}&per_page=15&search=${encodeURIComponent(search)}&risk=${encodeURIComponent(riskLevel)}&department=${encodeURIComponent(dept)}&sort=${encodeURIComponent(sort)}`;
        const res = await fetch(url, { credentials: 'include' });
        const data = await res.json();

        if (!res.ok) {
            tbody.innerHTML = `<tr><td colspan="7" class="text-center text-danger py-4">${data.error || 'Failed to load at-risk students'}</td></tr>`;
            return;
        }

        // Update KPI summary cards
        document.getElementById('kpiHighRisk').textContent = data.high_risk_count || 0;
        document.getElementById('kpiModerateRisk').textContent = data.moderate_risk_count || 0;
        document.getElementById('kpiTotalAtRisk').textContent = data.total || 0;
        
        const navCount = document.getElementById('navAtRiskCount');
        if (navCount) navCount.textContent = data.total || 0;

        if (!data.students || data.students.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted py-5">
                <i class="fas fa-check-circle text-success fs-3 mb-2 d-block"></i>
                No at-risk students found matching the selected filters.
            </td></tr>`;
            if (pagination) pagination.innerHTML = '';
            return;
        }

        tbody.innerHTML = data.students.map(s => {
            const attClass = s.attendance < 75 ? 'text-danger fw-bold' : 'text-muted';
            const internalClass = s.internal_marks < 60 ? 'text-danger fw-bold' : 'text-muted';
            const studyClass = s.study_hours < 10 ? 'text-danger fw-bold' : 'text-muted';

            return `
                <tr>
                    <td>
                        <div class="fw-bold">${s.student_name}</div>
                        <small class="text-muted">${s.student_id}</small>
                    </td>
                    <td>
                        <div>${s.department}</div>
                        <small class="text-muted">Semester ${s.semester}</small>
                    </td>
                    <td class="text-end">
                        <strong class="fs-6">${s.predicted_score}</strong>
                        <span class="text-muted small">/100</span>
                    </td>
                    <td>${getRiskBadge(s.risk_level)}</td>
                    <td>
                        <span class="badge bg-light text-dark border">
                            <i class="fas fa-triangle-exclamation text-warning me-1"></i> ${s.main_risk_factor}
                        </span>
                    </td>
                    <td>
                        <div class="small">
                            <span class="${attClass}">Att: ${s.attendance}%</span> &bull; 
                            <span class="${internalClass}">Int: ${s.internal_marks}</span> &bull; 
                            <span class="${studyClass}">Study: ${s.study_hours}h</span>
                        </div>
                    </td>
                    <td>
                        <div class="d-flex gap-1">
                            <button class="btn btn-sm btn-outline-primary py-1 px-2" onclick="openStudentDiagnostic('${s.student_id}')" title="Diagnostic Profile">
                                <i class="fas fa-notes-medical me-1"></i> Diagnose
                            </button>
                            <a href="prediction.html?student_id=${s.student_id}" class="btn btn-sm btn-outline-secondary py-1 px-2" title="Re-evaluate Performance">
                                <i class="fas fa-rotate"></i>
                            </a>
                        </div>
                    </td>
                </tr>
            `;
        }).join('');

        if (pagination) {
            paginate(data.total_pages || 1, data.page, 'atRiskPagination', 'loadAtRiskStudents');
        }

    } catch (e) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center text-danger py-4">Error connecting to server</td></tr>`;
    }
}

async function openStudentDiagnostic(studentId) {
    try {
        const res = await fetch(`${API_URL}/api/students/${studentId}`, { credentials: 'include' });
        const data = await res.json();
        if (!res.ok) { showToast(data.error || 'Failed to load student diagnostic', 'error'); return; }

        const s = data.student;
        const latest = data.latest_prediction;
        const modalBody = document.getElementById('studentDetailModalBody');
        if (!modalBody) return;

        let riskHtml = '';
        if (latest && latest.risk_factors && latest.risk_factors.length > 0) {
            riskHtml = latest.risk_factors.map(rf => `
                <div class="risk-factor-card ${rf.severity === 'critical' ? 'critical' : ''}">
                    <div class="d-flex justify-content-between">
                        <strong><i class="fas fa-triangle-exclamation ${rf.severity === 'critical' ? 'text-danger' : 'text-warning'} me-1"></i> ${rf.title}</strong>
                        <span class="badge ${rf.severity === 'critical' ? 'bg-danger' : 'bg-warning text-dark'}">${rf.severity.toUpperCase()}</span>
                    </div>
                    <div class="small text-muted mt-1">Current: <strong>${rf.current_value}</strong> &bull; Target: <strong>${rf.target_value}</strong></div>
                    <div class="small mt-1">${rf.description}</div>
                </div>
            `).join('');
        } else {
            riskHtml = '<p class="text-muted small">No active risk factors recorded.</p>';
        }

        let recHtml = '';
        if (latest && latest.recommendations && latest.recommendations.length > 0) {
            recHtml = latest.recommendations.map(r => `
                <div class="action-card mb-2 p-3">
                    <div class="action-step-num" style="width:28px;height:28px;font-size:12px;">0${r.priority}</div>
                    <div class="action-card-content">
                        <div class="fw-bold small">${r.title}</div>
                        <div class="small text-muted">${r.action}</div>
                        <span class="action-impact-pill mt-1" style="font-size:11px;">${r.impact}</span>
                    </div>
                </div>
            `).join('');
        }

        modalBody.innerHTML = `
            <div class="row g-3 mb-3 pb-3 border-bottom">
                <div class="col-md-7">
                    <h5 class="mb-1">${s.name} <small class="text-muted">(${s.student_id})</small></h5>
                    <div class="text-secondary small">${s.department} &bull; Semester ${s.semester} &bull; Age ${s.age || 20} &bull; Gender: ${s.gender}</div>
                </div>
                <div class="col-md-5 text-md-end">
                    ${latest ? `
                        <div class="fs-4 fw-bold text-primary">${latest.predicted_score || latest.predicted_marks}/100</div>
                        <div>${getRiskBadge(latest.risk_level)} ${getPerformanceBadge(latest.performance_level || latest.performance)}</div>
                    ` : '<span class="badge bg-secondary">No Predictions Yet</span>'}
                </div>
            </div>

            <!-- Current Academic Indicators -->
            <div class="row g-2 mb-3 p-3 bg-light rounded text-center small">
                <div class="col">Attendance<br><strong class="${s.attendance < 75 ? 'text-danger' : 'text-success'}">${s.attendance}%</strong></div>
                <div class="col">Internals<br><strong class="${s.internal_marks < 60 ? 'text-danger' : 'text-success'}">${s.internal_marks}/100</strong></div>
                <div class="col">Assignments<br><strong class="${s.assignment_score < 70 ? 'text-danger' : 'text-success'}">${s.assignment_score}%</strong></div>
                <div class="col">Study Hours<br><strong class="${s.study_hours < 10 ? 'text-danger' : 'text-success'}">${s.study_hours} h/wk</strong></div>
                <div class="col">Previous<br><strong class="${s.previous_marks < 60 ? 'text-danger' : 'text-success'}">${s.previous_marks}%</strong></div>
            </div>

            <div class="row g-3">
                <div class="col-md-6">
                    <h6 class="fw-bold mb-2"><i class="fas fa-magnifying-glass text-danger me-1"></i> Identified Risk Factors</h6>
                    ${riskHtml}
                </div>
                <div class="col-md-6">
                    <h6 class="fw-bold mb-2"><i class="fas fa-bullseye text-success me-1"></i> Recommended Action Plan</h6>
                    ${recHtml}
                </div>
            </div>

            <div class="d-flex justify-content-end gap-2 mt-3 pt-3 border-top">
                <a href="prediction.html?student_id=${s.student_id}" class="btn btn-primary btn-sm">
                    <i class="fas fa-wand-magic-sparkles me-1"></i> Open in Predictor
                </a>
            </div>
        `;

        const modal = new bootstrap.Modal(document.getElementById('studentDetailModal'));
        modal.show();

    } catch (e) {
        showToast('Error loading student diagnostic details', 'error');
    }
}
