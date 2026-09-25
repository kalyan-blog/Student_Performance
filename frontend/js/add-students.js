/**
 * EduPredict AI - Add Students (Manual Entry & CSV/Excel Import)
 */

let selectedFile = null;
let currentPreviewData = null;

// Tab Switching
function switchTab(tab) {
    const btnManual = document.getElementById('tabBtnManual');
    const btnUpload = document.getElementById('tabBtnUpload');
    const paneManual = document.getElementById('paneManual');
    const paneUpload = document.getElementById('paneUpload');

    hideGlobalAlerts();

    if (tab === 'manual') {
        btnManual.classList.add('active');
        btnUpload.classList.remove('active');
        paneManual.classList.add('active');
        paneUpload.classList.remove('active');
    } else {
        btnUpload.classList.add('active');
        btnManual.classList.remove('active');
        paneUpload.classList.add('active');
        paneManual.classList.remove('active');
    }
}

function showGlobalSuccess(msg) {
    const el = document.getElementById('globalSuccessAlert');
    const txt = document.getElementById('globalSuccessText');
    txt.textContent = msg || 'Student added successfully.';
    el.classList.remove('d-none');
    document.getElementById('globalErrorAlert').classList.add('d-none');
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function showGlobalError(msg) {
    const el = document.getElementById('globalErrorAlert');
    const txt = document.getElementById('globalErrorText');
    txt.textContent = msg || 'An error occurred. Please check the values.';
    el.classList.remove('d-none');
    document.getElementById('globalSuccessAlert').classList.add('d-none');
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function hideGlobalAlerts() {
    document.getElementById('globalSuccessAlert').classList.add('d-none');
    document.getElementById('globalErrorAlert').classList.add('d-none');
}

// =========================================================================
// TAB 1: MANUAL STUDENT ENTRY FORM
// =========================================================================

function resetValidationErrors() {
    const fields = ['student_id', 'student_name', 'attendance', 'internal_marks', 'assignment_completion', 'previous_marks', 'study_hours'];
    fields.forEach(f => {
        const input = document.getElementById(`m_${f}`);
        const err = document.getElementById(`err_${f}`);
        if (input) input.classList.remove('is-invalid');
        if (err) err.style.display = 'none';
    });
}

function showFieldError(field, message) {
    const input = document.getElementById(`m_${field}`);
    const err = document.getElementById(`err_${field}`);
    if (input) input.classList.add('is-invalid');
    if (err) {
        err.textContent = message;
        err.style.display = 'block';
    }
}

document.getElementById('manualStudentForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    hideGlobalAlerts();
    resetValidationErrors();

    const studentId = document.getElementById('m_student_id').value.trim();
    const studentName = document.getElementById('m_student_name').value.trim();
    const attendanceVal = document.getElementById('m_attendance').value;
    const internalVal = document.getElementById('m_internal_marks').value;
    const assignmentVal = document.getElementById('m_assignment_completion').value;
    const prevVal = document.getElementById('m_previous_marks').value;
    const studyVal = document.getElementById('m_study_hours').value;
    const department = document.getElementById('m_department').value;
    const semester = parseInt(document.getElementById('m_semester').value) || 1;

    let hasError = false;

    if (!studentId) {
        showFieldError('student_id', 'Student ID is required.');
        hasError = true;
    }
    if (!studentName) {
        showFieldError('student_name', 'Student Name is required.');
        hasError = true;
    }

    const attendance = parseFloat(attendanceVal);
    if (isNaN(attendance) || attendance < 0 || attendance > 100) {
        showFieldError('attendance', 'Attendance must be between 0 and 100%.');
        hasError = true;
    }

    const internal = parseFloat(internalVal);
    if (isNaN(internal) || internal < 0 || internal > 100) {
        showFieldError('internal_marks', 'Internal marks must be between 0 and 100.');
        hasError = true;
    }

    const assignment = parseFloat(assignmentVal);
    if (isNaN(assignment) || assignment < 0 || assignment > 100) {
        showFieldError('assignment_completion', 'Assignment completion must be between 0 and 100%.');
        hasError = true;
    }

    const prevMarks = parseFloat(prevVal);
    if (isNaN(prevMarks) || prevMarks < 0 || (prevMarks > 10 && prevMarks > 100)) {
        showFieldError('previous_marks', 'Enter valid performance (0-100% or 0-10 GPA).');
        hasError = true;
    }

    const studyHours = parseFloat(studyVal);
    if (isNaN(studyHours) || studyHours < 0) {
        showFieldError('study_hours', 'Study hours per week must be non-negative.');
        hasError = true;
    }

    if (hasError) {
        showGlobalError('Please resolve the highlighted field errors before submitting.');
        return;
    }

    const btn = document.getElementById('btnAddStudent');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Adding...';

    try {
        const payload = {
            student_id: studentId,
            student_name: studentName,
            attendance: attendance,
            internal_marks: internal,
            assignment_completion: assignment,
            previous_semester_performance: prevMarks,
            study_hours: studyHours,
            department: department,
            semester: semester
        };

        const res = await fetch(`${API_URL}/api/students`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(payload)
        });

        const data = await res.json();

        if (res.ok) {
            showGlobalSuccess('Student added successfully.');
            document.getElementById('manualStudentForm').reset();
            // Automatically refresh dashboard badges if applicable
            if (typeof loadStudentsList === 'function') loadStudentsList();
        } else {
            if (data.errors) {
                for (const [k, msg] of Object.entries(data.errors)) {
                    showFieldError(k, msg);
                }
            }
            showGlobalError(data.error || 'Failed to add student.');
        }
    } catch (err) {
        showGlobalError('Connection error while saving student.');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-plus me-1"></i> Add Student';
    }
});


// =========================================================================
// TAB 2: CSV / EXCEL DRAG & DROP IMPORT
// =========================================================================

const dropzone = document.getElementById('dropzone');

['dragenter', 'dragover'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.add('dragover');
    }, false);
});

['dragleave', 'drop'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.remove('dragover');
    }, false);
});

dropzone.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files.length > 0) {
        handleFileSelected(files[0]);
    }
});

function handleFileSelected(file) {
    if (!file) return;

    const ext = file.name.split('.').pop().toLowerCase();
    if (!['csv', 'xlsx', 'xls'].includes(ext)) {
        showGlobalError('Invalid file type. Only .csv, .xlsx, and .xls files are supported.');
        return;
    }

    selectedFile = file;
    document.getElementById('selectedFileName').textContent = file.name;
    document.getElementById('selectedFileSize').textContent = `${(file.size / 1024).toFixed(1)} KB`;
    document.getElementById('fileSelectedBar').classList.remove('d-none');
    document.getElementById('fileSelectedBar').classList.add('d-flex');

    hideGlobalAlerts();
    document.getElementById('previewCard').classList.add('d-none');
}

async function validateUploadedFile() {
    if (!selectedFile) return;

    const btn = document.getElementById('btnValidateFile');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Validating...';
    hideGlobalAlerts();

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
        const res = await fetch(`${API_URL}/api/students/import-preview`, {
            method: 'POST',
            credentials: 'include',
            body: formData
        });

        const data = await res.json();

        if (res.ok) {
            currentPreviewData = data;
            renderPreview(data);
        } else {
            showGlobalError(data.error || 'Failed to inspect file.');
        }
    } catch (err) {
        showGlobalError('Server connection error during file validation.');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-magnifying-glass me-1"></i> Inspect &amp; Validate File';
    }
}

function renderPreview(data) {
    const previewCard = document.getElementById('previewCard');
    previewCard.classList.remove('d-none');

    document.getElementById('previewFileName').textContent = data.filename;
    document.getElementById('summaryTotal').textContent = data.total_rows;
    document.getElementById('summaryValid').textContent = data.valid_count;
    document.getElementById('summaryInvalid').textContent = data.invalid_count;
    document.getElementById('btnValidCount').textContent = data.valid_count;

    // Render Invalid Rows Table if any
    const invalidAlert = document.getElementById('invalidRowsAlert');
    const invalidTbody = document.getElementById('invalidTableBody');
    invalidTbody.innerHTML = '';

    if (data.invalid_count > 0) {
        invalidAlert.classList.remove('d-none');
        data.invalid_rows.forEach(inv => {
            const tr = document.createElement('tr');
            tr.className = 'tr-invalid';
            tr.innerHTML = `
                <td class="fw-bold text-danger">Row ${inv.row}</td>
                <td><code>${inv.student_id}</code></td>
                <td>${inv.student_name}</td>
                <td class="text-danger small"><i class="fas fa-circle-exclamation me-1"></i> ${inv.reason}</td>
            `;
            invalidTbody.appendChild(tr);
        });
    } else {
        invalidAlert.classList.add('d-none');
    }

    // Render Valid Rows Preview Table
    const validTbody = document.getElementById('validTableBody');
    validTbody.innerHTML = '';

    const previewRows = data.valid_rows_preview || [];
    if (previewRows.length === 0) {
        validTbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted py-3">No valid records found to import.</td></tr>';
        document.getElementById('btnConfirmImport').disabled = true;
    } else {
        document.getElementById('btnConfirmImport').disabled = false;
        previewRows.forEach(row => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td class="fw-semibold"><code>${row.student_id}</code></td>
                <td>${row.name}</td>
                <td><span class="badge bg-light text-dark border">${row.attendance}%</span></td>
                <td>${row.internal_marks}</td>
                <td>${row.assignment_score}%</td>
                <td>${row.previous_marks}%</td>
                <td>${row.study_hours} hrs</td>
                <td><span class="small text-muted">${row.department}</span></td>
            `;
            validTbody.appendChild(tr);
        });
    }

    previewCard.scrollIntoView({ behavior: 'smooth' });
}

function cancelImport() {
    selectedFile = null;
    currentPreviewData = null;
    document.getElementById('fileInput').value = '';
    document.getElementById('fileSelectedBar').classList.remove('d-flex');
    document.getElementById('fileSelectedBar').classList.add('d-none');
    document.getElementById('previewCard').classList.add('d-none');
    hideGlobalAlerts();
}

async function confirmImport() {
    if (!currentPreviewData || !currentPreviewData.all_valid_rows || currentPreviewData.all_valid_rows.length === 0) {
        showGlobalError('No valid rows available to import.');
        return;
    }

    const btn = document.getElementById('btnConfirmImport');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Inserting...';

    try {
        const res = await fetch(`${API_URL}/api/students/import-confirm`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ students: currentPreviewData.all_valid_rows })
        });

        const data = await res.json();

        if (res.ok) {
            showGlobalSuccess(`Successfully imported ${data.imported_count} valid students!`);
            cancelImport();
        } else {
            showGlobalError(data.error || 'Failed to complete student import.');
        }
    } catch (err) {
        showGlobalError('Connection error during batch student import.');
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<i class="fas fa-file-import me-1"></i> Import Valid Students (${currentPreviewData ? currentPreviewData.valid_count : 0})`;
    }
}

// Download Sample CSV
function downloadTemplateCsv() {
    const csvContent = "data:text/csv;charset=utf-8," +
        "student_id,student_name,attendance,internal_marks,assignment_completion,previous_semester_performance,study_hours,department,semester\n" +
        "STU2001,Aarav Patel,88.5,82.0,90.0,78.5,14.0,Computer Science,5\n" +
        "STU2002,Pooja Sharma,62.0,54.0,58.0,60.0,7.5,Information Technology,5\n" +
        "STU2003,Rohan Verma,42.0,38.0,40.0,45.0,4.0,Electronics & Communication,5\n";

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "EduPredict_Student_Template.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}
