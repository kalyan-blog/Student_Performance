let studentPage = 1;

async function loadStudents(page = studentPage) {
    studentPage = page;
    const search = document.getElementById('studentSearch')?.value || '';
    try {
        const res = await fetch(`${API_URL}/api/students?page=${page}&per_page=10&search=${search}`, { credentials: 'include' });
        const data = await res.json();
        const tbody = document.getElementById('studentsTableBody');
        const pagination = document.getElementById('studentsPagination');
        if (!tbody) return;
        if (!data.students || data.students.length === 0) {
            tbody.innerHTML = '<tr><td colspan="10" class="text-center text-muted py-4">No students found</td></tr>';
            if (pagination) pagination.innerHTML = '';
            return;
        }
        tbody.innerHTML = data.students.map(s => `
            <tr>
                <td><strong>${s.student_id}</strong></td>
                <td>${s.name}</td>
                <td>${s.department}</td>
                <td>Sem ${s.semester}</td>
                <td>${s.attendance || 0}%</td>
                <td>${s.study_hours || 0}</td>
                <td>${s.assignment_score || 0}</td>
                <td>${s.internal_marks || 0}</td>
                <td>${s.previous_marks || 0}%</td>
                <td>
                    <div class="d-flex gap-1">
                        <a href="prediction.html?student_id=${s.student_id}" class="btn btn-sm btn-outline-primary py-1 px-2" title="Run Performance Prediction">
                            <i class="fas fa-wand-magic-sparkles"></i>
                        </a>
                        <button class="btn btn-sm btn-outline-secondary py-1 px-2" onclick="editStudent('${s.student_id}')" title="Edit Student">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-danger py-1 px-2" onclick="deleteStudent('${s.student_id}')" title="Delete Student">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
        if (pagination) {
            paginate(data.total_pages || 1, data.page, 'studentsPagination', 'loadStudents');
        }
    } catch (e) {
        showToast('Failed to load students', 'error');
    }
}

function showAddStudentModal() {
    document.getElementById('editStudentId').value = '';
    document.getElementById('studentModalTitle').textContent = 'Add Student';
    document.getElementById('studentForm').reset();
    const modal = new bootstrap.Modal(document.getElementById('studentModal'));
    modal.show();
}

async function editStudent(studentId) {
    try {
        const res = await fetch(`${API_URL}/api/students/${studentId}`, { credentials: 'include' });
        const data = await res.json();
        if (!res.ok) { showToast(data.error, 'error'); return; }
        const s = data.student;
        document.getElementById('editStudentId').value = s.student_id;
        document.getElementById('studentModalTitle').textContent = 'Edit Student';
        document.getElementById('sId').value = s.student_id;
        document.getElementById('sName').value = s.name;
        document.getElementById('sDept').value = s.department;
        document.getElementById('sSem').value = s.semester;
        document.getElementById('sAge').value = s.age;
        document.getElementById('sGender').value = s.gender;
        document.getElementById('sAttendance').value = s.attendance || 0;
        document.getElementById('sStudy').value = s.study_hours || 0;
        document.getElementById('sAssignment').value = s.assignment_score || 0;
        document.getElementById('sInternal').value = s.internal_marks || 0;
        document.getElementById('sPrevious').value = s.previous_marks || 0;
        const modal = new bootstrap.Modal(document.getElementById('studentModal'));
        modal.show();
    } catch { showToast('Failed to load student', 'error'); }
}

async function saveStudent() {
    const data = {
        student_id: document.getElementById('sId').value.trim(),
        name: document.getElementById('sName').value.trim(),
        department: document.getElementById('sDept').value,
        semester: parseInt(document.getElementById('sSem').value),
        age: parseInt(document.getElementById('sAge').value),
        gender: document.getElementById('sGender').value,
        attendance: parseFloat(document.getElementById('sAttendance').value) || 0,
        study_hours: parseFloat(document.getElementById('sStudy').value) || 0,
        assignment_score: parseFloat(document.getElementById('sAssignment').value) || 0,
        internal_marks: parseFloat(document.getElementById('sInternal').value) || 0,
        previous_marks: parseFloat(document.getElementById('sPrevious').value) || 0,
    };
    const editId = document.getElementById('editStudentId').value;
    try {
        const url = editId ? `${API_URL}/api/students/${editId}` : `${API_URL}/api/students`;
        const method = editId ? 'PUT' : 'POST';
        const res = await fetch(url, { method, headers: { 'Content-Type': 'application/json' }, credentials: 'include', body: JSON.stringify(data) });
        const result = await res.json();
        if (res.ok) {
            showToast(editId ? 'Student updated' : 'Student added', 'success');
            bootstrap.Modal.getInstance(document.getElementById('studentModal')).hide();
            loadStudents();
        } else {
            showToast(result.error, 'error');
        }
    } catch { showToast('Failed to save student', 'error'); }
}

async function deleteStudent(studentId) {
    if (!confirm(`Delete student ${studentId}?`)) return;
    try {
        const res = await fetch(`${API_URL}/api/students/${studentId}`, { method: 'DELETE', credentials: 'include' });
        if (res.ok) { showToast('Student deleted', 'success'); loadStudents(); }
        else { const d = await res.json(); showToast(d.error, 'error'); }
    } catch { showToast('Failed to delete student', 'error'); }
}

document.addEventListener('DOMContentLoaded', () => {
    if (window.location.pathname.includes('students.html')) loadStudents();
});