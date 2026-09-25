from flask import Blueprint, request, jsonify
from database.db import _find, _insert, _update, _delete, _all, _search
from routes.auth import login_required
import json

students_bp = Blueprint("students", __name__, url_prefix="/api/students")


@students_bp.route("", methods=["GET"])
@login_required
def get_students():
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        search = request.args.get("search", "").strip()
        result = _search("students", search, ["name", "student_id", "department"], page=page, per_page=per_page)
        return jsonify({
            "students": result.data,
            "total": result.count,
            "page": page,
            "per_page": per_page,
            "total_pages": max(1, -(-result.count // per_page))
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@students_bp.route("/at-risk", methods=["GET"])
@login_required
def get_at_risk_students():
    """
    Dedicated endpoint for retrieving at-risk students (High Risk & Moderate Risk)
    with their predicted score, risk level, and main risk factors.
    """
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 25, type=int)
        search = request.args.get("search", "").strip().lower()
        dept = request.args.get("department", "").strip()
        risk_filter = request.args.get("risk", "").strip().lower()
        sort_by = request.args.get("sort", "score_asc")

        # Get all predictions
        preds_res = _all("predictions", order="created_at", desc=True)
        # Deduplicate to latest prediction per student_id
        latest_preds = {}
        for p in preds_res.data:
            sid = p.get("student_id")
            if sid and sid not in latest_preds:
                latest_preds[sid] = p

        at_risk_list = []
        for sid, p in latest_preds.items():
            risk_level = p.get("risk_level", "")
            is_at_risk = "High" in risk_level or "Moderate" in risk_level

            if not is_at_risk:
                continue

            if risk_filter:
                if risk_filter == "high" and "High" not in risk_level:
                    continue
                elif risk_filter in ["moderate", "medium"] and "Moderate" not in risk_level and "Medium" not in risk_level:
                    continue

            if dept and p.get("department") != dept:
                continue

            name = (p.get("student_name") or "").lower()
            sid_str = str(sid).lower()
            if search and search not in name and search not in sid_str:
                continue

            # Extract main risk factor
            main_risk = "Multiple academic factors"
            raw_factors = p.get("risk_factors")
            if raw_factors:
                try:
                    factors_list = json.loads(raw_factors) if isinstance(raw_factors, str) else raw_factors
                    if factors_list and len(factors_list) > 0:
                        main_risk = factors_list[0].get("title", "Underperforming")
                except Exception:
                    pass

            at_risk_list.append({
                "student_id": sid,
                "student_name": p.get("student_name", "Unknown"),
                "department": p.get("department", "-"),
                "semester": p.get("semester", 1),
                "predicted_score": p.get("predicted_score") or p.get("predicted_marks", 0),
                "predicted_marks": p.get("predicted_score") or p.get("predicted_marks", 0),
                "risk_level": risk_level,
                "performance_level": p.get("performance_level") or p.get("performance", "Average"),
                "main_risk_factor": main_risk,
                "attendance": p.get("attendance", 0),
                "internal_marks": p.get("internal_marks", 0),
                "assignment_score": p.get("assignment_score", 0),
                "study_hours": p.get("study_hours", 0),
                "previous_marks": p.get("previous_marks", 0),
                "date": p.get("created_at", "")
            })

        # Sorting
        if sort_by == "score_asc":
            at_risk_list.sort(key=lambda x: float(x.get("predicted_score", 0)))
        elif sort_by == "score_desc":
            at_risk_list.sort(key=lambda x: -float(x.get("predicted_score", 0)))
        elif sort_by == "name":
            at_risk_list.sort(key=lambda x: x.get("student_name", ""))

        total = len(at_risk_list)
        total_pages = max(1, -(-total // per_page))
        offset = (page - 1) * per_page
        paged_items = at_risk_list[offset:offset + per_page]

        high_risk_count = sum(1 for item in at_risk_list if "High" in item["risk_level"])
        moderate_risk_count = sum(1 for item in at_risk_list if "Moderate" in item["risk_level"])

        return jsonify({
            "students": paged_items,
            "total": total,
            "high_risk_count": high_risk_count,
            "moderate_risk_count": moderate_risk_count,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@students_bp.route("/<student_id>", methods=["GET"])
@login_required
def get_student(student_id):
    try:
        result = _find("students", "student_id", student_id)
        if not result.data:
            return jsonify({"error": "Student not found"}), 404

        student = dict(result.data[0])

        # Fetch predictions for this student
        preds = _find("predictions", "student_id", student_id)
        parsed_preds = []
        for p in preds.data:
            p_dict = dict(p)
            for jf in ["risk_factors", "recommendations"]:
                if p_dict.get(jf) and isinstance(p_dict[jf], str):
                    try:
                        p_dict[jf] = json.loads(p_dict[jf])
                    except Exception:
                        p_dict[jf] = []
            parsed_preds.append(p_dict)

        # Sort latest first
        parsed_preds.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        latest = parsed_preds[0] if parsed_preds else None

        return jsonify({
            "student": student,
            "latest_prediction": latest,
            "prediction_history": parsed_preds
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@students_bp.route("", methods=["POST"])
@login_required
def add_student():
    try:
        data = request.get_json() or {}
        
        student_id = str(data.get("student_id", "")).strip()
        student_name = str(data.get("student_name") or data.get("name") or "").strip()
        
        errors = {}
        if not student_id:
            errors["student_id"] = "Student ID is required."
        if not student_name:
            errors["student_name"] = "Student Name is required."
            
        # Attendance: 0 - 100
        try:
            attendance = float(data.get("attendance", 0))
            if attendance < 0 or attendance > 100:
                errors["attendance"] = "Attendance must be between 0 and 100%."
        except (ValueError, TypeError):
            errors["attendance"] = "Attendance must be a valid number."
            attendance = 0

        # Internal Marks: 0 - 100
        try:
            internal_marks = float(data.get("internal_marks", 0))
            if internal_marks < 0 or internal_marks > 100:
                errors["internal_marks"] = "Internal marks must be between 0 and 100."
        except (ValueError, TypeError):
            errors["internal_marks"] = "Internal marks must be a valid number."
            internal_marks = 0

        # Assignment Completion: 0 - 100
        raw_assignment = data.get("assignment_completion") if data.get("assignment_completion") is not None else data.get("assignment_score", 0)
        try:
            assignment_score = float(raw_assignment)
            if assignment_score < 0 or assignment_score > 100:
                errors["assignment_completion"] = "Assignment completion must be between 0 and 100%."
        except (ValueError, TypeError):
            errors["assignment_completion"] = "Assignment completion must be a valid number."
            assignment_score = 0

        # Previous Semester Performance / GPA
        raw_prev = data.get("previous_semester_performance") if data.get("previous_semester_performance") is not None else data.get("previous_marks", 0)
        try:
            previous_marks = float(raw_prev)
            if previous_marks < 0:
                errors["previous_semester_performance"] = "Previous semester performance cannot be negative."
            elif previous_marks <= 10.0 and previous_marks > 0:
                # 10-point GPA scale converted to percentage
                previous_marks = min(100.0, round(previous_marks * 10.0, 1))
            elif previous_marks > 100:
                errors["previous_semester_performance"] = "Previous semester performance cannot exceed 100."
        except (ValueError, TypeError):
            errors["previous_semester_performance"] = "Previous performance must be a valid number."
            previous_marks = 0

        # Study Hours: non-negative
        try:
            study_hours = float(data.get("study_hours", 0))
            if study_hours < 0:
                errors["study_hours"] = "Study hours per week must be non-negative."
            elif study_hours > 100:
                errors["study_hours"] = "Study hours per week exceeds realistic maximum (100 hrs/wk)."
        except (ValueError, TypeError):
            errors["study_hours"] = "Study hours must be a valid number."
            study_hours = 0

        if errors:
            return jsonify({"error": "Validation failed", "errors": errors}), 400

        existing = _find("students", "student_id", student_id)
        if existing.data:
            return jsonify({"error": f"Student ID '{student_id}' already exists in database.", "errors": {"student_id": "Student ID already exists."}}), 409

        department = str(data.get("department", "Computer Science")).strip() or "General"
        semester = int(data.get("semester", 1))
        age = int(data.get("age", 20))
        gender = str(data.get("gender", "Other"))

        rec = _insert("students", {
            "student_id": student_id,
            "name": student_name,
            "department": department,
            "semester": semester,
            "age": age,
            "gender": gender,
            "attendance": round(attendance, 1),
            "study_hours": round(study_hours, 1),
            "assignment_score": round(assignment_score, 1),
            "internal_marks": round(internal_marks, 1),
            "previous_marks": round(previous_marks, 1)
        })
        return jsonify({"message": "Student added successfully", "student": rec.data[0]}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@students_bp.route("/import-preview", methods=["POST"])
@login_required
def preview_import():
    """
    Validates CSV or Excel file rows, reports valid vs invalid count,
    with clear error messages per invalid row.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded. Please select a .csv or .xlsx file."}), 400

    file = request.files["file"]
    if not file or not file.filename:
        return jsonify({"error": "Empty filename."}), 400

    filename = file.filename
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ["csv", "xlsx", "xls"]:
        return jsonify({"error": "Invalid file format. Please upload a .csv, .xlsx, or .xls file."}), 400

    try:
        import io
        import pandas as pd

        file_bytes = file.read()
        if ext == "csv":
            df = pd.read_csv(io.BytesIO(file_bytes))
        else:
            df = pd.read_excel(io.BytesIO(file_bytes))

        # Standardize column headers
        col_map = {}
        for col in df.columns:
            cleaned_col = str(col).strip().lower().replace(" ", "_").replace("-", "_").replace("%", "").rstrip("_")
            if cleaned_col in ["student_id", "id", "roll_no", "roll_number", "rollno", "reg_no", "studentid"]:
                col_map[col] = "student_id"
            elif cleaned_col in ["student_name", "name", "full_name", "studentname"]:
                col_map[col] = "student_name"
            elif cleaned_col in ["attendance", "attendance_percentage", "attendance_percent", "att"]:
                col_map[col] = "attendance"
            elif cleaned_col in ["internal_marks", "internal", "internal_score", "internals", "cia"]:
                col_map[col] = "internal_marks"
            elif cleaned_col in ["assignment_completion", "assignment_score", "assignment", "assignments"]:
                col_map[col] = "assignment_completion"
            elif cleaned_col in ["previous_semester_performance", "previous_marks", "previous_performance", "gpa", "prev_marks", "cgpa"]:
                col_map[col] = "previous_semester_performance"
            elif cleaned_col in ["study_hours", "study_hours_per_week", "hours", "study_time", "studyhours"]:
                col_map[col] = "study_hours"
            elif cleaned_col in ["department", "dept", "branch"]:
                col_map[col] = "department"
            elif cleaned_col in ["semester", "sem"]:
                col_map[col] = "semester"

        df = df.rename(columns=col_map)

        valid_rows = []
        invalid_rows = []
        seen_ids = set()

        # Query existing IDs in database to flag duplicates
        existing_res = _all("students")
        existing_ids = {str(r.get("student_id", "")).strip() for r in existing_res.data}

        for idx, row in df.iterrows():
            row_num = idx + 2  # 1-indexed header + row
            reasons = []

            # 1. Student ID
            sid = str(row.get("student_id", "")).strip()
            if not sid or sid.lower() == "nan":
                reasons.append("Missing Student ID.")
            elif sid in seen_ids:
                reasons.append(f"Duplicate Student ID '{sid}' within uploaded file.")
            elif sid in existing_ids:
                reasons.append(f"Student ID '{sid}' already exists in database.")
            else:
                seen_ids.add(sid)

            # 2. Student Name
            sname = str(row.get("student_name", "")).strip()
            if not sname or sname.lower() == "nan":
                reasons.append("Missing Student Name.")

            # 3. Attendance
            att_val = row.get("attendance")
            attendance = 0.0
            try:
                attendance = float(att_val)
                if attendance < 0 or attendance > 100:
                    reasons.append(f"Attendance must be between 0 and 100 (got {attendance}).")
            except (ValueError, TypeError):
                reasons.append(f"Invalid attendance numeric value '{att_val}'.")

            # 4. Internal Marks
            im_val = row.get("internal_marks")
            internal_marks = 0.0
            try:
                internal_marks = float(im_val)
                if internal_marks < 0 or internal_marks > 100:
                    reasons.append(f"Internal marks must be between 0 and 100 (got {internal_marks}).")
            except (ValueError, TypeError):
                reasons.append(f"Invalid internal marks numeric value '{im_val}'.")

            # 5. Assignment Completion
            ac_val = row.get("assignment_completion")
            assignment_score = 0.0
            try:
                assignment_score = float(ac_val)
                if assignment_score < 0 or assignment_score > 100:
                    reasons.append(f"Assignment completion must be between 0 and 100 (got {assignment_score}).")
            except (ValueError, TypeError):
                reasons.append(f"Invalid assignment completion numeric value '{ac_val}'.")

            # 6. Previous Semester Performance
            prev_val = row.get("previous_semester_performance")
            previous_marks = 0.0
            try:
                previous_marks = float(prev_val)
                if previous_marks < 0:
                    reasons.append(f"Previous semester performance cannot be negative (got {previous_marks}).")
                elif previous_marks <= 10.0 and previous_marks > 0:
                    previous_marks = min(100.0, round(previous_marks * 10.0, 1))
                elif previous_marks > 100:
                    reasons.append(f"Previous semester performance cannot exceed 100 (got {previous_marks}).")
            except (ValueError, TypeError):
                reasons.append(f"Invalid previous performance numeric value '{prev_val}'.")

            # 7. Study Hours
            sh_val = row.get("study_hours")
            study_hours = 0.0
            try:
                study_hours = float(sh_val)
                if study_hours < 0:
                    reasons.append(f"Study hours per week cannot be negative (got {study_hours}).")
                elif study_hours > 100:
                    reasons.append(f"Study hours per week exceeds realistic maximum (got {study_hours}).")
            except (ValueError, TypeError):
                reasons.append(f"Invalid study hours numeric value '{sh_val}'.")

            department = str(row.get("department", "Computer Science")).strip()
            if not department or department.lower() == "nan":
                department = "Computer Science"

            try:
                semester = int(row.get("semester", 1))
            except (ValueError, TypeError):
                semester = 1

            if reasons:
                invalid_rows.append({
                    "row": row_num,
                    "student_id": sid if sid != "nan" else "N/A",
                    "student_name": sname if sname != "nan" else "N/A",
                    "reason": "; ".join(reasons)
                })
            else:
                valid_rows.append({
                    "student_id": sid,
                    "name": sname,
                    "department": department,
                    "semester": semester,
                    "attendance": round(attendance, 1),
                    "internal_marks": round(internal_marks, 1),
                    "assignment_score": round(assignment_score, 1),
                    "previous_marks": round(previous_marks, 1),
                    "study_hours": round(study_hours, 1),
                    "age": 20,
                    "gender": "Other"
                })

        return jsonify({
            "filename": filename,
            "total_rows": len(df),
            "valid_count": len(valid_rows),
            "invalid_count": len(invalid_rows),
            "valid_rows_preview": valid_rows[:15],
            "all_valid_rows": valid_rows,
            "invalid_rows": invalid_rows
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to process file: {str(e)}"}), 500


@students_bp.route("/import-confirm", methods=["POST"])
@login_required
def confirm_import():
    """
    Inserts confirmed valid students into database and Supabase.
    """
    try:
        payload = request.get_json() or {}
        students_to_import = payload.get("students", [])

        if not students_to_import or not isinstance(students_to_import, list):
            return jsonify({"error": "No students provided for import."}), 400

        imported_count = 0
        skipped_count = 0

        for s in students_to_import:
            sid = str(s.get("student_id", "")).strip()
            if not sid:
                continue

            existing = _find("students", "student_id", sid)
            if existing.data:
                skipped_count += 1
                continue

            _insert("students", {
                "student_id": sid,
                "name": str(s.get("name") or s.get("student_name", "")).strip(),
                "department": str(s.get("department", "Computer Science")).strip(),
                "semester": int(s.get("semester", 1)),
                "age": int(s.get("age", 20)),
                "gender": str(s.get("gender", "Other")),
                "attendance": float(s.get("attendance", 0)),
                "study_hours": float(s.get("study_hours", 0)),
                "assignment_score": float(s.get("assignment_score", 0)),
                "internal_marks": float(s.get("internal_marks", 0)),
                "previous_marks": float(s.get("previous_marks", 0))
            })
            imported_count += 1

        return jsonify({
            "message": f"Successfully imported {imported_count} valid students.",
            "imported_count": imported_count,
            "skipped_count": skipped_count
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@students_bp.route("/<student_id>", methods=["PUT"])
@login_required
def update_student(student_id):
    try:
        data = request.get_json()
        update_data = {}
        fields = [
            "name", "department", "semester", "age", "gender",
            "attendance", "study_hours", "assignment_score",
            "internal_marks", "previous_marks"
        ]
        for field in fields:
            if field in data:
                val = data[field]
                if field in ["semester", "age"]:
                    val = int(val)
                elif field in ["attendance", "study_hours", "assignment_score", "internal_marks", "previous_marks"]:
                    val = float(val)
                update_data[field] = val

        if not update_data:
            return jsonify({"error": "No fields to update"}), 400

        _update("students", "student_id", student_id, update_data)
        return jsonify({"message": "Student updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@students_bp.route("/<student_id>", methods=["DELETE"])
@login_required
def delete_student(student_id):
    try:
        _delete("students", "student_id", student_id)
        return jsonify({"message": "Student deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@students_bp.route("/all", methods=["GET"])
@login_required
def get_all_students():
    try:
        result = _all("students")
        return jsonify({"students": result.data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500