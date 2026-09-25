/**
 * EduPredict AI — Predict Student Performance
 * Searchable Student Selection, Academic Profile Inspection, Live Edit, & ML Prediction
 */

let predPage = 1;
let currentSelectedStudent = null;
let searchDebounceTimer = null;

document.addEventListener('DOMContentLoaded', () => {
    if (window.location.pathname.includes('prediction.html')) {
        loadStudentsList();
        loadPredictionHistory(1);

        // Check if URL contains query param from student directory (e.g. ?student_id=S001)
        const urlParams = new URLSearchParams(window.location.search);
        const autoSid = urlParams.get('student_id');
        if (autoSid) {
            onStudentSelect(autoSid);
        }
    }
});

// =========================================================================
// 1. STUDENT SEARCH, FILTER & DROPDOWN MANAGEMENT
// =========================================================================

async function loadStudentsList(searchVal = '', deptVal = '', semVal = '') {
    const spinner = document.getElementById('studentLoadingSpinner');
    const select = document.getElementById('studentSelect');
    const countBadge = document.getElementById('studentCountBadge');
    const noAlert = document.getElementById('noStudentsFoundAlert');
    const noMsg = document.getElementById('noStudentsMsg');
    const addLink = document.getElementById('btnAddStudentsLink');

    if (spinner) spinner.classList.remove('d-none');
    if (noAlert) noAlert.classList.add('d-none');

    const searchInput = document.getElementById('studentSearchInput');
    const deptInput = document.getElementById('filterDept');
    const semInput = document.getElementById('filterSem');

    const search = searchVal !== '' ? searchVal : (searchInput ? searchInput.value.trim() : '');
    const dept = deptVal !== '' ? deptVal : (deptInput ? deptInput.value : 'all');
    const sem = semVal !== '' ? semVal : (semInput ? semInput.value : 'all');

    const params = new URLSearchParams({ per_page: 300 });
    if (search) params.append('search', search);
    if (dept && dept !== 'all') params.append('department', dept);
    if (sem && sem !== 'all') params.append('semester', sem);

    try {
        const res = await fetch(`${API_URL}/api/students?${params.toString()}`, { credentials: 'include' });
        const data = await res.json();

        if (!res.ok) {
            throw new Error(data.error || 'Failed to load students');
        }

        const students = data.students || [];
        const total = data.total !== undefined ? data.total : students.length;

        if (countBadge) {
            countBadge.textContent = `${total} Student${total === 1 ? '' : 's'}`;
        }

        // Rebuild dropdown options
        if (select) {
            select.innerHTML = '';
            
            const defaultOpt = document.createElement('option');
            defaultOpt.value = '';
            defaultOpt.textContent = students.length > 0 
                ? `-- Choose a student from database (${students.length} available) --`
                : '-- No matching students found --';
            select.appendChild(defaultOpt);

            students.forEach(s => {
                const opt = document.createElement('option');
                opt.value = s.student_id;
                const sName = s.student_name || s.name || 'Unnamed';
                const sDept = s.department || 'General';
                const sSem = s.semester ? `Sem ${s.semester}` : 'Sem 1';
                opt.textContent = `${s.student_id} — ${sName} (${sDept} • ${sSem})`;
                
                // If this student was already selected, keep selected
                if (currentSelectedStudent && currentSelectedStudent.student_id === s.student_id) {
                    opt.selected = true;
                }
                select.appendChild(opt);
            });
        }

        // Empty state handling
        if (students.length === 0) {
            if (noAlert) {
                noAlert.classList.remove('d-none');
                if (total === 0 && !search && dept === 'all' && sem === 'all') {
                    noMsg.textContent = 'No students have been added yet.';
                    if (addLink) addLink.classList.remove('d-none');
                } else {
                    noMsg.textContent = 'No students found. Try changing the search or filters.';
                    if (addLink) addLink.classList.add('d-none');
                }
            }
        }

    } catch (err) {
        showToast('Error loading student database records', 'error');
    } finally {
        if (spinner) spinner.classList.add('d-none');
    }
}

function onStudentSearchInput() {
    clearTimeout(searchDebounceTimer);
    searchDebounceTimer = setTimeout(() => {
        loadStudentsList();
    }, 250);
}

function onFilterChange() {
    loadStudentsList();
}

function clearSearch() {
    const input = document.getElementById('studentSearchInput');
    if (input) input.value = '';
    loadStudentsList();
}

// =========================================================================
// 2. STUDENT SELECTION & ACADEMIC PROFILE POPULATION
// =========================================================================

async function onStudentSelect(studentId) {
    const placeholder = document.getElementById('noStudentSelectedPlaceholder');
    const content = document.getElementById('selectedStudentContent');
    const actionBtns = document.getElementById('profileActionBtns');
    const statusText = document.getElementById('profileLoadedStatus');
    const select = document.getElementById('studentSelect');

    if (!studentId) {
        currentSelectedStudent = null;
        if (placeholder) placeholder.classList.remove('d-none');
        if (content) content.classList.add('d-none');
        if (actionBtns) actionBtns.classList.add('d-none');
        if (statusText) {
            statusText.innerHTML = '<span class="text-secondary"><i class="fas fa-hand-pointer me-1"></i>Select a student above to inspect metrics</span>';
        }
        return;
    }

    // Sync select dropdown value if called programmatically
    if (select && select.value !== studentId) {
        select.value = studentId;
    }

    if (statusText) {
        statusText.innerHTML = '<span class="text-primary"><span class="spinner-border spinner-border-sm me-1"></span> Loading student profile...</span>';
    }

    try {
        const res = await fetch(`${API_URL}/api/students/${encodeURIComponent(studentId)}`, { credentials: 'include' });
        const data = await res.json();

        if (!res.ok) {
            showToast(data.error || 'Student not found in database', 'error');
            return;
        }

        const s = data.student || data;
        currentSelectedStudent = {
            student_id: s.student_id || studentId,
            student_name: s.student_name || s.name || `Student ${studentId}`,
            name: s.student_name || s.name || `Student ${studentId}`,
            department: s.department || 'Computer Science',
            semester: parseInt(s.semester) || 1,
            attendance: parseFloat(s.attendance) || 0.0,
            internal_marks: parseFloat(s.internal_marks) || 0.0,
            assignment_completion: parseFloat(s.assignment_completion !== undefined ? s.assignment_completion : s.assignment_score) || 0.0,
            assignment_score: parseFloat(s.assignment_completion !== undefined ? s.assignment_completion : s.assignment_score) || 0.0,
            previous_semester_performance: parseFloat(s.previous_semester_performance !== undefined ? s.previous_semester_performance : s.previous_marks) || 0.0,
            previous_marks: parseFloat(s.previous_semester_performance !== undefined ? s.previous_semester_performance : s.previous_marks) || 0.0,
            study_hours: parseFloat(s.study_hours) || 0.0
        };

        renderStudentAcademicProfile(currentSelectedStudent);

        if (statusText) {
            statusText.innerHTML = '<span class="text-success fw-semibold"><i class="fas fa-check-circle me-1"></i>Student data loaded from database</span>';
        }

        showToast(`Loaded profile for ${currentSelectedStudent.student_name}`, 'success');

    } catch (err) {
        showToast('Error fetching student profile from database', 'error');
        if (statusText) {
            statusText.innerHTML = '<span class="text-danger"><i class="fas fa-circle-exclamation me-1"></i>Failed to load profile</span>';
        }
    }
}

function renderStudentAcademicProfile(s) {
    const placeholder = document.getElementById('noStudentSelectedPlaceholder');
    const content = document.getElementById('selectedStudentContent');
    const actionBtns = document.getElementById('profileActionBtns');

    if (placeholder) placeholder.classList.add('d-none');
    if (content) content.classList.remove('d-none');
    if (actionBtns) actionBtns.classList.remove('d-none');

    // Header info
    document.getElementById('profStudentName').textContent = s.student_name;
    document.getElementById('profStudentId').textContent = `ID: ${s.student_id}`;
    document.getElementById('profStudentDeptSem').textContent = `${s.department} • Semester ${s.semester}`;

    // Read-only metric values & progress bars
    const att = s.attendance;
    const im = s.internal_marks;
    const ac = s.assignment_completion;
    const prev = s.previous_semester_performance;
    const sh = s.study_hours;

    document.getElementById('dispAttendance').textContent = `${att.toFixed(1)}%`;
    const barAtt = document.getElementById('barAttendance');
    barAtt.style.width = `${Math.min(100, Math.max(0, att))}%`;
    barAtt.className = `progress-bar ${att >= 75 ? 'bg-success' : (att >= 60 ? 'bg-warning' : 'bg-danger')}`;

    document.getElementById('dispInternal').textContent = `${im.toFixed(1)} / 100`;
    const barIm = document.getElementById('barInternal');
    barIm.style.width = `${Math.min(100, Math.max(0, im))}%`;
    barIm.className = `progress-bar ${im >= 60 ? 'bg-success' : (im >= 45 ? 'bg-warning' : 'bg-danger')}`;

    document.getElementById('dispAssignment').textContent = `${ac.toFixed(1)}%`;
    const barAc = document.getElementById('barAssignment');
    barAc.style.width = `${Math.min(100, Math.max(0, ac))}%`;
    barAc.className = `progress-bar ${ac >= 70 ? 'bg-success' : (ac >= 50 ? 'bg-warning' : 'bg-danger')}`;

    document.getElementById('dispPrevious').textContent = `${prev.toFixed(1)}%`;
    const barPrev = document.getElementById('barPrevious');
    barPrev.style.width = `${Math.min(100, Math.max(0, prev))}%`;
    barPrev.className = `progress-bar ${prev >= 60 ? 'bg-success' : (prev >= 45 ? 'bg-warning' : 'bg-danger')}`;

    document.getElementById('dispStudy').textContent = `${sh.toFixed(1)} hrs/week`;
    const barStudy = document.getElementById('barStudy');
    barStudy.style.width = `${Math.min(100, Math.max(0, (sh / 25) * 100))}%`;
    barStudy.className = `progress-bar ${sh >= 10 ? 'bg-success' : (sh >= 6 ? 'bg-warning' : 'bg-danger')}`;

    // Also populate edit form inputs with current values
    document.getElementById('editAttendance').value = att;
    document.getElementById('editInternal').value = im;
    document.getElementById('editAssignment').value = ac;
    document.getElementById('editPrevious').value = prev;
    document.getElementById('editStudy').value = sh;
}

// =========================================================================
// 3. EDIT MODE (FACULTY REVISION & SUPABASE PERSISTENCE)
// =========================================================================

function toggleEditMode() {
    const grid = document.getElementById('readOnlyMetricsGrid');
    const form = document.getElementById('editStudentForm');
    const btn = document.getElementById('btnToggleEdit');

    const isEditing = !form.classList.contains('d-none');
    if (isEditing) {
        cancelEditMode();
    } else {
        grid.classList.add('d-none');
        form.classList.remove('d-none');
        btn.innerHTML = '<i class="fas fa-eye me-1"></i> Read-Only';
        document.getElementById('editAttendance').focus();
    }
}

function cancelEditMode() {
    const grid = document.getElementById('readOnlyMetricsGrid');
    const form = document.getElementById('editStudentForm');
    const btn = document.getElementById('btnToggleEdit');

    form.classList.add('d-none');
    grid.classList.remove('d-none');
    btn.innerHTML = '<i class="fas fa-pen-to-square me-1"></i> Edit Data';

    // Revert inputs
    if (currentSelectedStudent) {
        document.getElementById('editAttendance').value = currentSelectedStudent.attendance;
        document.getElementById('editInternal').value = currentSelectedStudent.internal_marks;
        document.getElementById('editAssignment').value = currentSelectedStudent.assignment_completion;
        document.getElementById('editPrevious').value = currentSelectedStudent.previous_semester_performance;
        document.getElementById('editStudy').value = currentSelectedStudent.study_hours;
    }
}

async function saveStudentChanges() {
    if (!currentSelectedStudent) return;

    const attVal = parseFloat(document.getElementById('editAttendance').value);
    const imVal = parseFloat(document.getElementById('editInternal').value);
    const acVal = parseFloat(document.getElementById('editAssignment').value);
    const prevVal = parseFloat(document.getElementById('editPrevious').value);
    const studyVal = parseFloat(document.getElementById('editStudy').value);

    // Validation
    if (isNaN(attVal) || attVal < 0 || attVal > 100) {
        showToast('Attendance must be between 0 and 100%', 'warning');
        return;
    }
    if (isNaN(imVal) || imVal < 0 || imVal > 100) {
        showToast('Internal marks must be between 0 and 100', 'warning');
        return;
    }
    if (isNaN(acVal) || acVal < 0 || acVal > 100) {
        showToast('Assignment completion must be between 0 and 100%', 'warning');
        return;
    }
    if (isNaN(prevVal) || prevVal < 0 || prevVal > 100) {
        showToast('Previous semester marks must be between 0 and 100', 'warning');
        return;
    }
    if (isNaN(studyVal) || studyVal < 0) {
        showToast('Study hours per week cannot be negative', 'warning');
        return;
    }

    const saveBtn = document.getElementById('btnSaveStudentChanges');
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Saving...';

    const payload = {
        attendance: attVal,
        internal_marks: imVal,
        assignment_completion: acVal,
        assignment_score: acVal,
        previous_semester_performance: prevVal,
        previous_marks: prevVal,
        study_hours: studyVal
    };

    try {
        const res = await fetch(`${API_URL}/api/students/${encodeURIComponent(currentSelectedStudent.student_id)}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(payload)
        });

        const data = await res.json();

        if (res.ok) {
            // Update local object
            currentSelectedStudent.attendance = attVal;
            currentSelectedStudent.internal_marks = imVal;
            currentSelectedStudent.assignment_completion = acVal;
            currentSelectedStudent.assignment_score = acVal;
            currentSelectedStudent.previous_semester_performance = prevVal;
            currentSelectedStudent.previous_marks = prevVal;
            currentSelectedStudent.study_hours = studyVal;

            renderStudentAcademicProfile(currentSelectedStudent);
            cancelEditMode();
            showToast('Student academic record updated in database!', 'success');
        } else {
            showToast(data.error || 'Failed to update student record', 'error');
        }
    } catch (err) {
        showToast('Error updating student record in database', 'error');
    } finally {
        saveBtn.disabled = false;
        saveBtn.innerHTML = '<i class="fas fa-check me-1"></i> Save Changes';
    }
}

// =========================================================================
// 4. PREDICTION EXECUTION (ML INFERENCE & RISK ATTRIBUTION)
// =========================================================================

async function runPredictionForSelectedStudent() {
    if (!currentSelectedStudent) {
        showToast('Please select a student before generating a prediction.', 'warning');
        const select = document.getElementById('studentSelect');
        if (select) select.focus();
        return;
    }

    const btn = document.getElementById('btnPredict');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span> Analyzing academic performance...';

    const algo = document.getElementById('predAlgo') ? document.getElementById('predAlgo').value : 'Random Forest Regressor';

    const payload = {
        student_id: currentSelectedStudent.student_id,
        student_name: currentSelectedStudent.student_name,
        department: currentSelectedStudent.department,
        semester: currentSelectedStudent.semester,
        attendance: currentSelectedStudent.attendance,
        internal_marks: currentSelectedStudent.internal_marks,
        assignment_completion: currentSelectedStudent.assignment_completion,
        assignment_score: currentSelectedStudent.assignment_completion,
        previous_semester_score: currentSelectedStudent.previous_semester_performance,
        previous_marks: currentSelectedStudent.previous_semester_performance,
        study_hours: currentSelectedStudent.study_hours,
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

        const p = Object.assign({}, currentSelectedStudent || {}, data, data.prediction || {}, (data.prediction && data.prediction.student_info) || {});
        if (data.risk_factors && !p.risk_factors) p.risk_factors = data.risk_factors;
        if (data.recommendations && !p.recommendations) p.recommendations = data.recommendations;

        renderPredictionResult(p);
        showToast('Performance analysis generated successfully!', 'success');
        loadPredictionHistory(1);

    } catch (err) {
        showToast('Unable to connect to prediction engine.', 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-bolt me-2"></i> Predict Performance';
    }
}

// =========================================================================
// 5. PREDICTION RESULT PRESENTATION
// =========================================================================

function renderPredictionResult(p) {
    const placeholder = document.getElementById('resultPlaceholder');
    const container = document.getElementById('resultContainer');
    if (placeholder) placeholder.style.display = 'none';
    if (container) {
        container.style.display = 'block';
        container.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    // 1. Hero Card Elements
    const scoreVal = p.predicted_score !== undefined ? p.predicted_score : p.predicted_marks;
    const scoreEl = document.getElementById('resScore');
    if (scoreEl) scoreEl.textContent = parseFloat(scoreVal || 0).toFixed(1);

    const metaPills = document.getElementById('resMetaPills');
    if (metaPills) {
        metaPills.innerHTML = `
            ${getPerformanceBadge(p.performance_level || p.performance)}
            ${getRiskBadge(p.risk_level)}
            ${getGradeBadge(p.grade)}
        `;
    }

    const subEl = document.getElementById('resStudentSub');
    if (subEl) {
        subEl.innerHTML = `
            Student: <strong>${p.student_name || (currentSelectedStudent ? currentSelectedStudent.student_name : 'Student')}</strong> 
            (ID: <code>${p.student_id || (currentSelectedStudent ? currentSelectedStudent.student_id : '-')}</code>) 
            &bull; Model: <strong>${p.algorithm || 'ML Regressor'}</strong>
        `;
    }

    // 2. Academic Factors Progress Bars
    renderFactorBars(p);

    // 3. Multi-Factor Diagnostic Risk Cards
    renderRiskFactorCards(p.risk_factors);

    // 4. Personalized Recommendations / Action Plan Cards
    renderActionPlanCards(p.recommendations);
}

function renderFactorBars(p) {
    const container = document.getElementById('factorBarsContainer');
    if (!container) return;

    const factors = [
        { label: 'Class Attendance', actual: p.attendance, target: 75, unit: '%', icon: 'fa-calendar-check' },
        { label: 'Internal Assessment', actual: p.internal_marks, target: 60, unit: '/100', icon: 'fa-pen-to-square' },
        { label: 'Assignment Completion', actual: p.assignment_score || p.assignment_completion, target: 70, unit: '%', icon: 'fa-tasks' },
        { label: 'Previous Semester', actual: p.previous_marks || p.previous_semester_performance, target: 60, unit: '%', icon: 'fa-graduation-cap' },
        { label: 'Weekly Study Hours', actual: p.study_hours, target: 10, unit: ' hrs/wk', maxScale: 20, icon: 'fa-clock' }
    ];

    let html = '';
    factors.forEach(f => {
        const actualVal = parseFloat(f.actual) || 0;
        const targetVal = f.target;
        const isMet = actualVal >= targetVal;
        const scale = f.maxScale || 100;
        const pct = Math.min(100, Math.max(5, (actualVal / scale) * 100));
        const color = isMet ? 'var(--success)' : (actualVal >= targetVal * 0.8 ? 'var(--warning)' : 'var(--danger)');

        html += `
            <div class="mb-3">
                <div class="d-flex justify-content-between align-items-center mb-1">
                    <span class="small fw-semibold"><i class="fas ${f.icon} me-1 text-primary"></i>${f.label}</span>
                    <span class="small">
                        <strong style="color:${color}">${actualVal}${f.unit}</strong> 
                        <span class="text-muted">(Target: &ge; ${targetVal}${f.unit})</span>
                        ${isMet 
                            ? '<span class="badge bg-success-subtle text-success ms-1" style="font-size:10px;"><i class="fas fa-check"></i> Benchmark Met</span>' 
                            : '<span class="badge bg-danger-subtle text-danger ms-1" style="font-size:10px;"><i class="fas fa-triangle-exclamation"></i> Deficit</span>'
                        }
                    </span>
                </div>
                <div class="progress" style="height: 8px;">
                    <div class="progress-bar" style="width: ${pct}%; background-color: ${color}; transition: width 0.8s ease;"></div>
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
}

function renderRiskFactorCards(factors) {
    const container = document.getElementById('riskFactorsContainer') || document.getElementById('riskCardsContainer');
    const countTag = document.getElementById('riskCountTag');
    if (!container) return;

    let parsed = factors || [];
    if (typeof factors === 'string') {
        try { parsed = JSON.parse(factors); } catch { parsed = []; }
    }

    if (countTag) {
        countTag.textContent = `${parsed.length} Factor${parsed.length === 1 ? '' : 's'} Detected`;
    }

    if (parsed.length === 0) {
        container.innerHTML = `
            <div class="p-3 bg-success-subtle border border-success-subtle rounded text-success small d-flex align-items-center">
                <i class="fas fa-circle-check fs-5 me-2"></i>
                <div><strong>Optimal Academic Profile:</strong> No acute risk factor deficits identified across core academic benchmarks.</div>
            </div>
        `;
        return;
    }

    let html = '<div class="row g-2">';
    parsed.forEach(rf => {
        const isCritical = rf.severity === 'critical';
        const borderCol = isCritical ? 'var(--danger)' : 'var(--warning)';
        const bgCol = isCritical ? '#FEF2F2' : '#FFFBEB';
        const badgeCol = isCritical ? 'danger' : 'warning';

        html += `
            <div class="col-md-6">
                <div class="p-3 rounded h-100 border" style="background:${bgCol}; border-left: 4px solid ${borderCol} !important;">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <h6 class="fw-bold mb-0 text-dark" style="font-size:13.5px;">
                            <i class="fas ${rf.icon || 'fa-triangle-exclamation'} me-1 text-${badgeCol}"></i> ${rf.title}
                        </h6>
                        <span class="badge bg-${badgeCol}-subtle text-${badgeCol} border border-${badgeCol}-subtle text-uppercase" style="font-size:10px;">
                            ${rf.severity}
                        </span>
                    </div>
                    <div class="small text-secondary mb-2" style="font-size:12px; line-height:1.4;">
                        ${rf.description}
                    </div>
                    <div class="d-flex justify-content-between align-items-center pt-2 border-top border-light-subtle" style="font-size:11.5px;">
                        <span>Actual: <strong>${rf.current_value}</strong></span>
                        <span class="text-danger fw-semibold">${rf.deficit}</span>
                    </div>
                </div>
            </div>
        `;
    });
    html += '</div>';

    container.innerHTML = html;
}

function renderActionPlanCards(recs) {
    const container = document.getElementById('recommendationsContainer') || document.getElementById('actionPlansContainer');
    if (!container) return;

    let parsed = recs || [];
    if (typeof recs === 'string') {
        try { parsed = JSON.parse(recs); } catch { parsed = []; }
    }

    if (parsed.length === 0) {
        container.innerHTML = `
            <div class="p-3 bg-light border rounded text-secondary small">
                <i class="fas fa-info-circle me-1"></i> Continue standard coursework and maintain existing study routine.
            </div>
        `;
        return;
    }

    let html = '';
    parsed.forEach(rec => {
        const isCritical = rec.severity === 'critical';
        const badgeBg = isCritical ? 'bg-danger' : 'bg-primary';

        html += `
            <div class="p-3 bg-white border rounded shadow-xs mb-2">
                <div class="d-flex align-items-start gap-3">
                    <div class="badge ${badgeBg} rounded-circle p-2 flex-shrink-0" style="width:28px;height:28px;display:flex;align-items:center;justify-content:center;">
                        ${rec.priority}
                    </div>
                    <div class="flex-grow-1">
                        <div class="d-flex justify-content-between align-items-center mb-1">
                            <h6 class="fw-bold mb-0 text-dark" style="font-size:14px;">${rec.title}</h6>
                            <span class="badge bg-light text-primary border small" style="font-size:11px;">
                                <i class="fas fa-arrow-trend-up me-1"></i> ${rec.impact}
                            </span>
                        </div>
                        <p class="text-secondary small mb-2" style="font-size:12.5px; line-height:1.45;">
                            ${rec.action}
                        </p>
                        <div class="d-flex gap-3 text-muted" style="font-size:11px;">
                            <span><i class="fas fa-bullseye me-1"></i>Target: <strong>${rec.target_value}</strong></span>
                            <span><i class="fas fa-clock-rotate-left me-1"></i>Category: <strong>${rec.category}</strong></span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
}

function resetForm() {
    currentSelectedStudent = null;
    const select = document.getElementById('studentSelect');
    if (select) select.value = '';
    onStudentSelect('');
    const resultContainer = document.getElementById('resultContainer');
    const placeholder = document.getElementById('resultPlaceholder');
    if (resultContainer) resultContainer.style.display = 'none';
    if (placeholder) placeholder.style.display = 'block';
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// =========================================================================
// 6. PREDICTION HISTORY TABLE & ACTIONS
// =========================================================================

async function loadPredictionHistory(page = 1) {
    predPage = page;
    const tbody = document.getElementById('predHistoryBody') || document.getElementById('historyTableBody');
    if (!tbody) return;

    const searchInput = document.getElementById('predHistSearch') || document.getElementById('historySearch');
    const riskInput = document.getElementById('filterRisk') || document.getElementById('historyRiskFilter');
    const deptInput = document.getElementById('filterDepartment') || document.getElementById('historyDeptFilter');
    const perfInput = document.getElementById('filterPerformance');

    const search = searchInput ? searchInput.value.trim() : '';
    const risk = riskInput ? riskInput.value : '';
    const dept = deptInput ? deptInput.value : '';
    const perf = perfInput ? perfInput.value : '';

    const params = new URLSearchParams({
        page: page,
        per_page: 8,
        search: search,
        risk_level: risk,
        department: dept,
        performance: perf
    });

    try {
        const res = await fetch(`${API_URL}/api/predictions/history?${params.toString()}`, { credentials: 'include' });
        const data = await res.json();

        tbody.innerHTML = '';
        if (!data.predictions || data.predictions.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" class="text-center text-muted py-4">No prediction records found.</td></tr>';
            return;
        }

        data.predictions.forEach(p => {
            const tr = document.createElement('tr');
            const scoreVal = p.predicted_score !== undefined ? p.predicted_score : p.predicted_marks;
            tr.innerHTML = `
                <td>
                    <div class="fw-semibold text-dark">${p.student_name || 'Student'}</div>
                    <code style="font-size:11px;">${p.student_id || '-'}</code>
                </td>
                <td><span class="badge bg-light text-secondary border">${p.department || '-'} &bull; Sem ${p.semester || 1}</span></td>
                <td><strong>${parseFloat(p.attendance || 0).toFixed(1)}%</strong></td>
                <td>${parseFloat(p.internal_marks || 0).toFixed(1)}</td>
                <td>${parseFloat(p.study_hours || 0).toFixed(1)} hrs</td>
                <td><strong class="text-primary fs-6">${parseFloat(scoreVal || 0).toFixed(1)}</strong> / 100</td>
                <td>${getRiskBadge(p.risk_level)}</td>
                <td>${getPerformanceBadge(p.performance_level || p.performance)}</td>
                <td>
                    <button class="btn btn-xs btn-outline-primary py-1 px-2" onclick="viewPredictionDetails('${p.id}')" title="View Diagnostics">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="btn btn-xs btn-outline-danger py-1 px-2 ms-1" onclick="deletePrediction('${p.id}')" title="Delete">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });

        paginate(data.total_pages, data.page, 'predPagination', 'loadPredictionHistory');

    } catch (err) {
        tbody.innerHTML = '<tr><td colspan="9" class="text-center text-danger py-4">Failed to load prediction history.</td></tr>';
    }
}

async function viewPredictionDetails(id) {
    try {
        const res = await fetch(`${API_URL}/api/predictions/${id}`, { credentials: 'include' });
        const p = await res.json();

        let riskHtml = '';
        if (p.risk_factors && Array.isArray(p.risk_factors)) {
            p.risk_factors.forEach(rf => {
                riskHtml += `<div class="p-2 mb-2 bg-light border-start border-danger border-3 rounded small"><strong>${rf.title}:</strong> ${rf.description} (${rf.deficit})</div>`;
            });
        }
        if (!riskHtml) riskHtml = '<div class="text-muted small">No specific risk deficits recorded.</div>';

        let recHtml = '';
        if (p.recommendations && Array.isArray(p.recommendations)) {
            p.recommendations.forEach(r => {
                recHtml += `<div class="p-2 mb-2 bg-light border-start border-primary border-3 rounded small"><strong>${r.title}:</strong> ${r.action} <span class="badge bg-primary ms-1">${r.impact}</span></div>`;
            });
        }
        if (!recHtml) recHtml = '<div class="text-muted small">Standard curriculum progress recommended.</div>';

        const modalBody = document.getElementById('predDetailBody') || document.getElementById('predModalBody');
        modalBody.innerHTML = `
            <div class="row align-items-center mb-3 pb-2 border-bottom">
                <div class="col-md-6">
                    <h5 class="fw-bold mb-0 text-dark">${p.student_name || 'Student'}</h5>
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
                <div class="col">Assignments<br><strong>${p.assignment_score || p.assignment_completion}%</strong></div>
                <div class="col">Study Hours<br><strong>${p.study_hours} hrs/wk</strong></div>
                <div class="col">Previous<br><strong>${p.previous_marks || p.previous_semester_performance}%</strong></div>
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
            csv += `"${p.student_id || ''}","${p.student_name || ''}","${p.department || ''}",${p.semester || 1},${p.attendance || 0},${p.internal_marks || 0},${p.assignment_score || p.assignment_completion || 0},${p.study_hours || 0},${p.previous_marks || p.previous_semester_performance || 0},${p.predicted_score || p.predicted_marks || 0},"${p.grade || ''}","${p.performance_level || p.performance || ''}","${p.risk_level || ''}","${p.created_at || ''}"\n`;
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