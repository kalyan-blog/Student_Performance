let predPage = 1;

document.addEventListener('DOMContentLoaded', () => {
    if (window.location.pathname.includes('prediction.html')) {
        loadPredictionHistory();

        // Check if URL contains query params from student directory (e.g. ?student_id=S001)
        const urlParams = new URLSearchParams(window.location.search);
        const autoSid = urlParams.get('student_id');
        if (autoSid) {
            fetchStudentAndPrefill(autoSid);
        }

        const form = document.getElementById('predictionForm');
        if (form) {
            form.addEventListener('submit', handlePredictionSubmit);
        }
    }
});

async function handlePredictionSubmit(e) {
    e.preventDefault();
    const btn = document.getElementById('btnPredict');
    
    // Client-side validation
    const sid = document.getElementById('predStudentId').value.trim();
    const sname = document.getElementById('predStudentName').value.trim();
    const attendance = parseFloat(document.getElementById('predAttendance').value);
    const internal = parseFloat(document.getElementById('predInternal').value);
    const assignment = parseFloat(document.getElementById('predAssign').value);
    const previous = parseFloat(document.getElementById('predPrevious').value);
    const study = parseFloat(document.getElementById('predStudy').value);
    const dept = document.getElementById('predDept').value;
    const sem = parseInt(document.getElementById('predSem').value) || 1;
    const algo = document.getElementById('predAlgo').value;

    if (!sid) {
        showToast('Please enter a valid Student ID', 'warning');
        document.getElementById('predStudentId').focus();
        return;
    }
    if (isNaN(attendance) || attendance < 0 || attendance > 100) {
        showToast('Please enter a valid attendance percentage between 0 and 100', 'warning');
        return;
    }
    if (isNaN(internal) || internal < 0 || internal > 100) {
        showToast('Please enter valid internal assessment marks between 0 and 100', 'warning');
        return;
    }
    if (isNaN(assignment) || assignment < 0 || assignment > 100) {
        showToast('Please enter a valid assignment completion percentage between 0 and 100', 'warning');
        return;
    }
    if (isNaN(previous) || previous < 0 || previous > 100) {
        showToast('Please enter valid previous semester marks between 0 and 100', 'warning');
        return;
    }
    if (isNaN(study) || study < 0) {
        showToast('Study hours per week cannot be negative', 'warning');
        return;
    }

    // Set loading state
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Analyzing student performance...';

    const payload = {
        student_id: sid,
        student_name: sname || `Student ${sid}`,
        department: dept,
        semester: sem,
        attendance: attendance,
        internal_marks: internal,
        assignment_completion: assignment,
        assignment_score: assignment,
        previous_semester_score: previous,
        previous_marks: previous,
        study_hours: study,
        algorithm: algo
    };

    try {
        const res = await fetch(`${API_URL}/api/predictions/predict`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(payload)
        });
        const data = await res.json();

        if (!res.ok) {
            showToast(data.error || 'Prediction calculation failed', 'error');
            return;
        }

        const p = data.prediction;
        renderPredictionResult(p);
        showToast('Performance analysis generated successfully!', 'success');
        loadPredictionHistory(1);

    } catch (err) {
        showToast('Unable to connect to prediction engine. Please check backend status.', 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-bolt me-2"></i> Predict Performance & Detect Risks';
    }
}

function renderPredictionResult(p) {
    const placeholder = document.getElementById('resultPlaceholder');
    const container = document.getElementById('resultContainer');
    if (placeholder) placeholder.style.display = 'none';
    if (container) {
        container.style.display = 'block';
        container.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    // 1. Hero Card Elements
    document.getElementById('resScore').textContent = p.predicted_score || p.predicted_marks;
    document.getElementById('resPerfBadge').outerHTML = getPerformanceBadge(p.performance_level || p.performance);
    document.getElementById('resRiskBadge').outerHTML = getRiskBadge(p.risk_level);
    document.getElementById('resGradeBadge').outerHTML = getGradeBadge(p.grade);
    
    const info = p.student_info || {};
    document.getElementById('resStudentSub').innerHTML = `
        Student: <strong>${info.student_name || p.student_name || 'Student'}</strong> (ID: ${info.student_id || p.student_id || '-'}) &bull; Department: ${info.department || p.department || '-'} &bull; Model: ${p.algorithm || 'Random Forest Regressor'}
    `;

    // 2. Factor Progress Bars vs Benchmark
    renderFactorBars(p);

    // 3. Risk Factors Card
    renderRiskFactors(p.risk_factors || []);

    // 4. Personalized Recommendations Card
    renderRecommendations(p.recommendations || []);
}

function renderFactorBars(p) {
    const container = document.getElementById('factorBarsContainer');
    if (!container) return;

    const factors = p.factors || {};
    const items = [
        { key: 'attendance', label: 'Attendance', current: factors.attendance?.current ?? p.attendance ?? 0, target: 75, unit: '%' },
        { key: 'internal_marks', label: 'Internal Assessment', current: factors.internal_marks?.current ?? p.internal_marks ?? 0, target: 60, unit: '/100' },
        { key: 'assignment_completion', label: 'Assignment Completion', current: factors.assignment_completion?.current ?? p.assignment_score ?? 0, target: 70, unit: '%' },
        { key: 'previous_semester_score', label: 'Previous Semester Score', current: factors.previous_semester_score?.current ?? p.previous_marks ?? 0, target: 60, unit: '%' },
        { key: 'study_hours', label: 'Weekly Study Hours', current: factors.study_hours?.current ?? p.study_hours ?? 0, target: 10, unit: ' hrs/wk', maxScale: 40 }
    ];

    container.innerHTML = items.map(item => {
        const isHealthy = item.current >= item.target;
        const maxScale = item.maxScale || 100;
        const fillPercent = Math.min(100, Math.round((item.current / maxScale) * 100));
        const targetPercent = Math.min(100, Math.round((item.target / maxScale) * 100));
        const color = isHealthy ? 'var(--success)' : 'var(--danger)';

        return `
            <div class="factor-bar-item">
                <div class="factor-bar-header">
                    <span>
                        ${item.label}
                        <strong class="${isHealthy ? 'text-success' : 'text-danger'} ms-1">${item.current}${item.unit}</strong>
                    </span>
                    <span class="text-muted small">
                        Benchmark: <strong>&ge; ${item.target}${item.unit}</strong>
                        ${isHealthy ? '<i class="fas fa-check-circle text-success ms-1"></i>' : '<i class="fas fa-triangle-exclamation text-danger ms-1"></i>'}
                    </span>
                </div>
                <div class="factor-bar-track position-relative">
                    <div class="factor-bar-fill" style="width: ${fillPercent}%; background-color: ${color};"></div>
                    <div class="factor-benchmark-line" style="left: ${targetPercent}%;" title="Target Benchmark (${item.target}${item.unit})"></div>
                </div>
            </div>
        `;
    }).join('');
}

function renderRiskFactors(factors) {
    const container = document.getElementById('riskFactorsContainer');
    const tag = document.getElementById('riskCountTag');
    if (!container) return;

    if (!factors || factors.length === 0) {
        if (tag) {
            tag.className = 'badge bg-success-subtle text-success border';
            tag.textContent = 'No Critical Risks';
        }
        container.innerHTML = `
            <div class="alert alert-success d-flex align-items-center gap-2 mb-0" style="display:flex;">
                <i class="fas fa-shield-check fs-5 text-success"></i>
                <div>
                    <strong>Optimal Academic Health:</strong>
                    No significant risk factors identified. Student inputs are within recommended institutional benchmarks.
                </div>
            </div>
        `;
        return;
    }

    if (tag) {
        tag.className = 'badge bg-danger-subtle text-danger border';
        tag.textContent = `${factors.length} Factor${factors.length > 1 ? 's' : ''} Detected`;
    }

    container.innerHTML = factors.map(f => `
        <div class="risk-factor-card ${f.severity === 'critical' ? 'critical' : ''}">
            <div class="risk-factor-header">
                <div class="risk-factor-title">
                    <i class="fas ${f.icon || 'fa-triangle-exclamation'} ${f.severity === 'critical' ? 'text-danger' : 'text-warning'}"></i>
                    ${f.title}
                </div>
                <span class="badge ${f.severity === 'critical' ? 'bg-danger' : 'bg-warning text-dark'}">${f.severity.toUpperCase()}</span>
            </div>
            <div class="risk-factor-metrics">
                <span>Current: <strong>${f.current_value}</strong></span>
                <span>Target Benchmark: <strong>${f.target_value}</strong></span>
                <span class="text-danger ms-auto"><i class="fas fa-arrow-down me-1"></i>${f.deficit}</span>
            </div>
            <p class="risk-factor-desc">${f.description}</p>
        </div>
    `).join('');
}

function renderRecommendations(recs) {
    const container = document.getElementById('recommendationsContainer');
    if (!container) return;

    if (!recs || recs.length === 0) {
        container.innerHTML = '<p class="text-muted small">No specific interventions needed. Maintain current performance.</p>';
        return;
    }

    container.innerHTML = recs.map(r => `
        <div class="action-card">
            <div class="action-step-num">0${r.priority}</div>
            <div class="action-card-content">
                <div class="action-card-title">
                    <i class="fas ${r.icon || 'fa-arrow-right'} text-primary me-1"></i>
                    ${r.title}
                    <span class="badge bg-secondary-subtle text-secondary ms-auto small">${r.category}</span>
                </div>
                <div class="action-card-stats">
                    <span>Current: <strong>${r.current_value}</strong></span> &bull; 
                    <span>Target: <strong>${r.target_value}</strong></span>
                </div>
                <div class="action-card-guidance">${r.action}</div>
                <div>
                    <span class="action-impact-pill">
                        <i class="fas fa-circle-arrow-up"></i> ${r.impact}
                    </span>
                </div>
            </div>
        </div>
    `).join('');
}

function loadPreset(type) {
    if (type === 'high_risk') {
        document.getElementById('predStudentId').value = 'S' + Math.floor(100 + Math.random() * 899);
        document.getElementById('predStudentName').value = 'Rohan Gupta';
        document.getElementById('predAttendance').value = '54.0';
        document.getElementById('predInternal').value = '42.0';
        document.getElementById('predAssign').value = '45.0';
        document.getElementById('predPrevious').value = '52.0';
        document.getElementById('predStudy').value = '4.0';
        document.getElementById('predAlgo').value = 'Random Forest Regressor';
    } else if (type === 'moderate_risk') {
        document.getElementById('predStudentId').value = 'S' + Math.floor(100 + Math.random() * 899);
        document.getElementById('predStudentName').value = 'Isha Deshmukh';
        document.getElementById('predAttendance').value = '71.5';
        document.getElementById('predInternal').value = '64.0';
        document.getElementById('predAssign').value = '67.0';
        document.getElementById('predPrevious').value = '72.0';
        document.getElementById('predStudy').value = '8.5';
        document.getElementById('predAlgo').value = 'Random Forest Regressor';
    } else if (type === 'low_risk') {
        document.getElementById('predStudentId').value = 'S' + Math.floor(100 + Math.random() * 899);
        document.getElementById('predStudentName').value = 'Ananya Rao';
        document.getElementById('predAttendance').value = '94.0';
        document.getElementById('predInternal').value = '88.5';
        document.getElementById('predAssign').value = '95.0';
        document.getElementById('predPrevious').value = '89.0';
        document.getElementById('predStudy').value = '22.0';
        document.getElementById('predAlgo').value = 'Random Forest Regressor';
    }
    showToast(`Loaded ${type.replace('_', ' ')} scenario into form`, 'info');
}

function resetForm() {
    document.getElementById('predictionForm').reset();
    document.getElementById('resultContainer').style.display = 'none';
    document.getElementById('resultPlaceholder').style.display = 'block';
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

async function loadPredictionHistory(page = predPage) {
    predPage = page;
    const search = document.getElementById('predHistSearch')?.value || '';
    const dept = document.getElementById('filterDepartment')?.value || '';
    const perf = document.getElementById('filterPerformance')?.value || '';
    const risk = document.getElementById('filterRisk')?.value || '';

    try {
        const url = `${API_URL}/api/predictions/history?page=${page}&per_page=10&search=${encodeURIComponent(search)}&department=${encodeURIComponent(dept)}&performance=${encodeURIComponent(perf)}&risk_level=${encodeURIComponent(risk)}`;
        const res = await fetch(url, { credentials: 'include' });
        const data = await res.json();
        const tbody = document.getElementById('predHistoryBody');
        const pagination = document.getElementById('predPagination');

        if (!tbody) return;

        if (!data.predictions || data.predictions.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" class="text-center text-muted py-4">No prediction records matching filter criteria</td></tr>';
            if (pagination) pagination.innerHTML = '';
            return;
        }

        tbody.innerHTML = data.predictions.map(p => `
            <tr>
                <td>
                    <div class="fw-bold">${p.student_name || 'N/A'}</div>
                    <small class="text-muted">${p.student_id || ''}</small>
                </td>
                <td>${p.department || '-'}</td>
                <td>${p.attendance ? p.attendance + '%' : '-'}</td>
                <td>${p.internal_marks ?? '-'}</td>
                <td>${p.study_hours ? p.study_hours + ' hrs' : '-'}</td>
                <td>
                    <strong class="fs-6">${p.predicted_score || p.predicted_marks || 0}</strong>
                    <span class="text-muted small">/100</span>
                </td>
                <td>${getRiskBadge(p.risk_level)}</td>
                <td>${getPerformanceBadge(p.performance_level || p.performance)}</td>
                <td>
                    <div class="d-flex gap-1">
                        <button class="btn btn-sm btn-outline-primary py-1 px-2" onclick="viewPredictionDetail('${p.id}')" title="Inspect Full Analysis">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-danger py-1 px-2" onclick="deletePrediction('${p.id}')" title="Delete">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');

        if (pagination) {
            paginate(data.total_pages || 1, data.page, 'predPagination', 'loadPredictionHistory');
        }
    } catch {
        // Silently handle transient network errors
    }
}

async function viewPredictionDetail(id) {
    try {
        const res = await fetch(`${API_URL}/api/predictions/${id}`, { credentials: 'include' });
        const data = await res.json();
        if (!res.ok) { showToast(data.error || 'Failed to load details', 'error'); return; }

        const p = data.prediction;
        const modalBody = document.getElementById('predDetailBody');
        if (!modalBody) return;

        let riskHtml = '';
        if (p.risk_factors && p.risk_factors.length > 0) {
            riskHtml = p.risk_factors.map(rf => `
                <div class="border rounded p-2 mb-2 bg-light">
                    <div class="d-flex justify-content-between font-weight-bold">
                        <strong><i class="fas fa-triangle-exclamation text-warning me-1"></i> ${rf.title}</strong>
                        <span class="badge ${rf.severity === 'critical' ? 'bg-danger' : 'bg-warning text-dark'}">${rf.severity}</span>
                    </div>
                    <div class="small text-muted mt-1">Current: ${rf.current_value} | Target: ${rf.target_value}</div>
                    <div class="small mt-1">${rf.description}</div>
                </div>
            `).join('');
        } else {
            riskHtml = '<div class="alert alert-success py-2 mb-0"><i class="fas fa-check-circle me-1"></i> No critical risk factors identified.</div>';
        }

        let recHtml = '';
        if (p.recommendations && p.recommendations.length > 0) {
            recHtml = p.recommendations.map(r => `
                <div class="border-start border-4 border-primary ps-3 py-1 mb-3">
                    <div class="fw-bold">${r.priority ? '0' + r.priority + '. ' : ''}${r.title}</div>
                    <div class="small text-muted mb-1">${r.action}</div>
                    <span class="badge bg-success-subtle text-success">${r.impact || 'Score Improvement'}</span>
                </div>
            `).join('');
        } else {
            recHtml = '<p class="text-muted small">Maintain regular academic habits.</p>';
        }

        modalBody.innerHTML = `
            <div class="row g-3 mb-3 pb-3 border-bottom">
                <div class="col-md-6">
                    <h5 class="mb-1">${p.student_name || 'Student'} <small class="text-muted">(${p.student_id})</small></h5>
                    <div class="text-muted small">${p.department || 'General'} &bull; Semester ${p.semester || 1} &bull; ${formatDate(p.created_at)}</div>
                </div>
                <div class="col-md-6 text-md-end">
                    <div class="fs-4 fw-bold text-primary">${p.predicted_score || p.predicted_marks}/100</div>
                    <div>${getRiskBadge(p.risk_level)} ${getPerformanceBadge(p.performance_level || p.performance)}</div>
                </div>
            </div>

            <div class="row g-2 mb-3 p-2 bg-light rounded text-center small">
                <div class="col">Attendance<br><strong>${p.attendance}%</strong></div>
                <div class="col">Internals<br><strong>${p.internal_marks}/100</strong></div>
                <div class="col">Assignments<br><strong>${p.assignment_score}%</strong></div>
                <div class="col">Study Hours<br><strong>${p.study_hours} hrs/wk</strong></div>
                <div class="col">Previous<br><strong>${p.previous_marks}%</strong></div>
            </div>

            <h6 class="fw-bold mb-2"><i class="fas fa-magnifying-glass text-danger me-1"></i> Identified Risk Factors</h6>
            <div class="mb-3">${riskHtml}</div>

            <h6 class="fw-bold mb-2"><i class="fas fa-bullseye text-success me-1"></i> Action Recommendations</h6>
            <div>${recHtml}</div>
        `;

        const modal = new bootstrap.Modal(document.getElementById('predDetailModal'));
        modal.show();

    } catch (e) {
        showToast('Error opening prediction analysis', 'error');
    }
}

async function deletePrediction(id) {
    if (!confirm('Are you sure you want to delete this prediction record?')) return;
    try {
        const res = await fetch(`${API_URL}/api/predictions/${id}`, { method: 'DELETE', credentials: 'include' });
        if (res.ok) {
            showToast('Prediction deleted', 'success');
            loadPredictionHistory(predPage);
        } else {
            showToast('Failed to delete', 'error');
        }
    } catch {
        showToast('Error deleting prediction', 'error');
    }
}

async function exportPredictions() {
    try {
        const res = await fetch(`${API_URL}/api/predictions/export`, { credentials: 'include' });
        const data = await res.json();
        if (!data.predictions || data.predictions.length === 0) {
            showToast('No prediction history to export', 'warning');
            return;
        }

        let csv = 'Student ID,Student Name,Department,Semester,Attendance %,Internal Marks,Assignment %,Study Hours/Wk,Previous Semester %,Predicted Score,Grade,Performance,Risk Level,Date\n';
        data.predictions.forEach(p => {
            csv += `"${p.student_id || ''}","${p.student_name || ''}","${p.department || ''}",${p.semester || 1},${p.attendance || 0},${p.internal_marks || 0},${p.assignment_score || 0},${p.study_hours || 0},${p.previous_marks || 0},${p.predicted_score || p.predicted_marks || 0},"${p.grade || ''}","${p.performance_level || p.performance || ''}","${p.risk_level || ''}","${p.created_at || ''}"\n`;
        });

        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `edupredict_predictions_${new Date().toISOString().slice(0, 10)}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
        showToast('Prediction data exported successfully', 'success');
    } catch {
        showToast('Export failed', 'error');
    }
}

async function fetchStudentAndPrefill(sid) {
    try {
        const res = await fetch(`${API_URL}/api/students/${sid}`, { credentials: 'include' });
        const data = await res.json();
        if (data.student) {
            const s = data.student;
            document.getElementById('predStudentId').value = s.student_id || sid;
            document.getElementById('predStudentName').value = s.name || '';
            document.getElementById('predDept').value = s.department || 'Computer Science';
            document.getElementById('predSem').value = s.semester || 1;
            document.getElementById('predAttendance').value = s.attendance || 75;
            document.getElementById('predInternal').value = s.internal_marks || 65;
            document.getElementById('predAssign').value = s.assignment_score || 70;
            document.getElementById('predPrevious').value = s.previous_marks || 65;
            document.getElementById('predStudy').value = s.study_hours || 10;
            showToast(`Prefilled details for ${s.name}`, 'info');
        }
    } catch { /* ignore */ }
}