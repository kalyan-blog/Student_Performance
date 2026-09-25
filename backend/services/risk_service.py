"""
Academic Risk Classification and Risk Factor Identification Service.
Implements application-defined risk thresholds and parameter benchmark analysis.
"""

# Benchmark Targets for Academic Evaluation
BENCHMARKS = {
    "attendance": {"target": 75.0, "unit": "%", "label": "Attendance Percentage"},
    "assignment_score": {"target": 70.0, "unit": "%", "label": "Assignment Completion"},
    "internal_marks": {"target": 60.0, "unit": "/100", "label": "Internal Assessment Marks"},
    "study_hours": {"target": 10.0, "unit": " hrs/wk", "label": "Weekly Study Time"},
    "previous_marks": {"target": 60.0, "unit": "%", "label": "Previous Semester Score"},
}


def classify_risk(predicted_score):
    """
    Classifies academic risk based on application thresholds:
      - 75+        -> Low Risk (🟢)
      - 50 - 74.99 -> Moderate Risk (🟡)
      - Below 50   -> High Risk (🔴)
    """
    score = float(predicted_score)
    if score >= 75.0:
        return {
            "level": "Low Risk",
            "code": "low",
            "color": "#16A34A",
            "badge_class": "risk-low",
            "icon": "fa-shield-check",
            "description": "Student is on a stable academic track. Continued consistency recommended."
        }
    elif score >= 50.0:
        return {
            "level": "Moderate Risk",
            "code": "moderate",
            "color": "#F59E0B",
            "badge_class": "risk-moderate",
            "icon": "fa-exclamation-triangle",
            "description": "Student demonstrates vulnerability in one or more academic factors. Early intervention recommended."
        }
    else:
        return {
            "level": "High Risk",
            "code": "high",
            "color": "#DC2626",
            "badge_class": "risk-high",
            "icon": "fa-triangle-exclamation",
            "description": "Student is in critical danger of failing or severe underperformance. Immediate remedial action required."
        }


def identify_risk_factors(student_data):
    """
    Identifies why a student may be at risk based on their actual inputs vs academic benchmarks.
    Does NOT return generic risk factors that don't correspond to the student's actual values.
    """
    factors = []

    # 1. Attendance check
    att = float(student_data.get("attendance", 100))
    if att < BENCHMARKS["attendance"]["target"]:
        gap = round(BENCHMARKS["attendance"]["target"] - att, 1)
        severity = "critical" if att < 60 else "warning"
        factors.append({
            "key": "attendance",
            "title": "Low Attendance",
            "severity": severity,
            "current_value": f"{att:.1f}%",
            "target_value": f">= {BENCHMARKS['attendance']['target']:.0f}%",
            "deficit": f"{gap}% below benchmark",
            "description": f"Attendance is {att:.1f}%, which is below the mandatory {BENCHMARKS['attendance']['target']:.0f}% requirement, causing gaps in concept retention and missed laboratory/lecture participation.",
            "icon": "fa-calendar-xmark"
        })

    # 2. Assignment Completion check
    assign = float(student_data.get("assignment_score", 100))
    if assign < BENCHMARKS["assignment_score"]["target"]:
        gap = round(BENCHMARKS["assignment_score"]["target"] - assign, 1)
        severity = "critical" if assign < 50 else "warning"
        factors.append({
            "key": "assignment_score",
            "title": "Low Assignment Completion",
            "severity": severity,
            "current_value": f"{assign:.1f}%",
            "target_value": f">= {BENCHMARKS['assignment_score']['target']:.0f}%",
            "deficit": f"{gap}% below benchmark",
            "description": f"Assignment completion is at {assign:.1f}%, indicating incomplete continuous homework, missed submission deadlines, or lack of structured practice.",
            "icon": "fa-clipboard-question"
        })

    # 3. Internal Assessment Marks check
    internal = float(student_data.get("internal_marks", 100))
    if internal < BENCHMARKS["internal_marks"]["target"]:
        gap = round(BENCHMARKS["internal_marks"]["target"] - internal, 1)
        severity = "critical" if internal < 45 else "warning"
        factors.append({
            "key": "internal_marks",
            "title": "Low Internal Performance",
            "severity": severity,
            "current_value": f"{internal:.1f}/100",
            "target_value": f">= {BENCHMARKS['internal_marks']['target']:.0f}/100",
            "deficit": f"{gap} points below benchmark",
            "description": f"Internal assessment score is {internal:.1f}/100, reflecting struggle with midterm assessments, sectional tests, or foundational quizzes.",
            "icon": "fa-file-circle-exclamation"
        })

    # 4. Weekly Study Hours check
    study = float(student_data.get("study_hours", 15))
    if study < BENCHMARKS["study_hours"]["target"]:
        gap = round(BENCHMARKS["study_hours"]["target"] - study, 1)
        severity = "critical" if study < 5 else "warning"
        factors.append({
            "key": "study_hours",
            "title": "Limited Study Time",
            "severity": severity,
            "current_value": f"{study:.1f} hrs/week",
            "target_value": f">= {BENCHMARKS['study_hours']['target']:.0f} hrs/week",
            "deficit": f"{gap} hrs/week below recommended",
            "description": f"Self-study commitment is only {study:.1f} hours/week, which is below the minimum 10 hours required for course mastery and systematic revision.",
            "icon": "fa-clock-rotate-left"
        })

    # 5. Previous Semester Performance check
    prev = float(student_data.get("previous_marks", 100))
    if prev < BENCHMARKS["previous_marks"]["target"]:
        gap = round(BENCHMARKS["previous_marks"]["target"] - prev, 1)
        severity = "critical" if prev < 50 else "warning"
        factors.append({
            "key": "previous_marks",
            "title": "Weak Academic Foundation",
            "severity": severity,
            "current_value": f"{prev:.1f}%",
            "target_value": f">= {BENCHMARKS['previous_marks']['target']:.0f}%",
            "deficit": f"{gap}% below benchmark",
            "description": f"Previous semester score of {prev:.1f}% indicates historical learning backlogs in core prerequisites that directly compound current semester difficulty.",
            "icon": "fa-graduation-cap"
        })

    # Sort factors so critical risks appear first
    severity_order = {"critical": 0, "warning": 1}
    factors.sort(key=lambda x: severity_order.get(x["severity"], 2))

    return factors


def classify_performance(score):
    """
    Classifies performance level:
      - 85+       -> Excellent
      - 70 - 84.9 -> Good
      - 50 - 69.9 -> Average
      - Below 50  -> Poor
    """
    s = float(score)
    if s >= 85.0:
        return "Excellent"
    elif s >= 70.0:
        return "Good"
    elif s >= 50.0:
        return "Average"
    else:
        return "Poor"


def calculate_grade(score):
    """
    Calculates letter grade.
    """
    s = float(score)
    if s >= 90:
        return "A+"
    elif s >= 80:
        return "A"
    elif s >= 70:
        return "B+"
    elif s >= 60:
        return "B"
    elif s >= 50:
        return "C"
    elif s >= 40:
        return "D"
    else:
        return "F"
