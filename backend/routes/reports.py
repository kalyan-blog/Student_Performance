from flask import Blueprint, request, jsonify, Response
from database.db import _all, _find, _insert, _delete
from routes.auth import login_required
from datetime import datetime
import pandas as pd
from fpdf import FPDF
import tempfile
import os
import json

reports_bp = Blueprint("reports", __name__, url_prefix="/api/reports")


class ReportPDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, "Student Performance Prediction - Report", 0, 1, "C")
        self.ln(5)
    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", 0, 0, "C")


@reports_bp.route("/generate", methods=["POST"])
@login_required
def generate_report():
    try:
        data = request.get_json()
        report_type = data.get("type", "student")
        department = data.get("department", "")
        student_id = data.get("student_id", "")
        report_data = {}
        if report_type == "student" and student_id:
            student = _find("students", "student_id", student_id)
            predictions = _find("predictions", "student_id", student_id)
            report_data = {"student": student.data[0] if student.data else {}, "predictions": predictions.data}
        elif report_type == "department" and department:
            students = _all("students")
            dept_students = [s for s in students.data if s.get("department") == department]
            all_preds = _all("predictions")
            dept_preds = [p for p in all_preds.data if p.get("department") == department]
            report_data = {"department": department, "students": dept_students, "predictions": dept_preds}
        elif report_type == "monthly":
            predictions = _all("predictions")
            report_data = {"predictions": predictions.data, "type": "monthly"}
        else:
            predictions = _all("predictions")
            students = _all("students")
            report_data = {"predictions": predictions.data, "students": students.data, "type": "summary"}
        pdf = ReportPDF()
        pdf.alias_nb_pages()
        pdf.add_page()
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 10, f"Report Type: {report_type.title()}", 0, 1)
        pdf.cell(0, 10, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", 0, 1)
        pdf.ln(10)
        if report_data.get("student"):
            s = report_data["student"]
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, "Student Details", 0, 1)
            pdf.set_font("Arial", "", 10)
            for key, val in s.items():
                if key not in ["password"]:
                    pdf.cell(0, 8, f"{key.replace('_', ' ').title()}: {val}", 0, 1)
        if report_data.get("students"):
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, f"Students ({len(report_data['students'])})", 0, 1)
        if report_data.get("predictions"):
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, f"Predictions ({len(report_data['predictions'])})", 0, 1)
            pdf.set_font("Arial", "", 10)
            for p in report_data["predictions"][:20]:
                pdf.cell(0, 8, f"{p.get('student_name', 'N/A')} - Predicted: {p.get('predicted_marks', 0)} - Grade: {p.get('grade', 'N/A')}", 0, 1)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        pdf.output(tmp.name)
        tmp.close()
        name = f"{report_type}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        _insert("reports", {"report_name": name, "report_type": report_type, "data": json.dumps(str(report_data)[:1000])})
        with open(tmp.name, "rb") as f:
            pdf_bytes = f.read()
        os.unlink(tmp.name)
        return Response(pdf_bytes, mimetype="application/pdf", headers={"Content-Disposition": f"attachment; filename={report_type}_report.pdf", "Content-Type": "application/pdf"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@reports_bp.route("/history", methods=["GET"])
@login_required
def get_reports():
    try:
        result = _all("reports", order="created_at")
        return jsonify({"reports": result.data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@reports_bp.route("/<report_id>", methods=["DELETE"])
@login_required
def delete_report(report_id):
    try:
        _delete("reports", "id", report_id)
        return jsonify({"message": "Report deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500