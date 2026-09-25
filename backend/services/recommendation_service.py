"""
Personalized Recommendation Engine.
Generates prioritized, actionable intervention recommendations based on the student's
actual academic parameters, deficit gaps, and risk severity.
"""

def generate_recommendations(student_data, risk_factors=None, predicted_score=None):
    """
    Generates tailored, prioritized recommendations based on the student's actual values.
    Prioritizes recommendations addressing the highest deficits and critical risk factors.
    """
    att = float(student_data.get("attendance", 100))
    assign = float(student_data.get("assignment_score", 100))
    internal = float(student_data.get("internal_marks", 100))
    study = float(student_data.get("study_hours", 15))
    prev = float(student_data.get("previous_marks", 100))
    score = float(predicted_score) if predicted_score is not None else 70.0

    candidates = []

    # 1. Attendance recommendation
    if att < 75.0:
        gap = round(75.0 - att, 1)
        severity = "critical" if att < 60 else "warning"
        weight = gap * 1.5  # priority weighting
        candidates.append({
            "key": "attendance",
            "weight": weight,
            "severity": severity,
            "title": "Improve Class Attendance & Engagement",
            "category": "Attendance",
            "current_value": f"{att:.1f}%",
            "target_value": ">= 75.0%",
            "deficit": f"{gap}% required to reach minimum benchmark",
            "action": f"Maintain strict attendance across upcoming lectures and lab practicals. Missing fewer classes will directly boost concept retention and internal attendance credits.",
            "impact": "+6 to +10 pts in overall performance",
            "icon": "fa-calendar-check"
        })

    # 2. Assignment completion recommendation
    if assign < 70.0:
        gap = round(70.0 - assign, 1)
        severity = "critical" if assign < 50 else "warning"
        weight = gap * 1.3
        candidates.append({
            "key": "assignment_score",
            "weight": weight,
            "severity": severity,
            "title": "Complete Pending Course Assignments",
            "category": "Coursework",
            "current_value": f"{assign:.1f}%",
            "target_value": ">= 70.0%",
            "deficit": f"{gap}% gap from target completion",
            "action": f"Clear all pending submissions within the next 10 days. Schedule bi-weekly checkpoint sessions with teaching assistants for difficult assignments.",
            "impact": "+5 to +8 pts through continuous evaluation",
            "icon": "fa-list-check"
        })

    # 3. Internal Assessment recommendation
    if internal < 60.0:
        gap = round(60.0 - internal, 1)
        severity = "critical" if internal < 45 else "warning"
        weight = gap * 1.4
        candidates.append({
            "key": "internal_marks",
            "weight": weight,
            "severity": severity,
            "title": "Targeted Internal Assessment Preparation",
            "category": "Assessments",
            "current_value": f"{internal:.1f}/100",
            "target_value": ">= 60.0/100",
            "deficit": f"{gap} marks below passing internal threshold",
            "action": f"Prioritize high-yield syllabus modules. Practice past semester mid-term papers and attend faculty doubt-clearing consultation hours.",
            "impact": "+8 to +14 pts on continuous internal assessment",
            "icon": "fa-pen-to-square"
        })

    # 4. Weekly study hours recommendation
    if study < 10.0:
        gap = round(10.0 - study, 1)
        severity = "critical" if study < 5 else "warning"
        weight = gap * 1.2
        target_hours = 12 if study < 6 else 14
        candidates.append({
            "key": "study_hours",
            "weight": weight,
            "severity": severity,
            "title": "Establish Structured Weekly Study Schedule",
            "category": "Time Management",
            "current_value": f"{study:.1f} hrs/week",
            "target_value": f">= {target_hours} hrs/week",
            "deficit": f"Need ~{(target_hours - study):.1f} additional self-study hrs/week",
            "action": f"Set aside a dedicated 2-hour daily study block during distraction-free hours. Adopt active recall and spaced repetition for technical subjects.",
            "impact": "+5 to +9 pts across all subjects",
            "icon": "fa-clock"
        })

    # 5. Previous semester foundation recommendation
    if prev < 60.0:
        gap = round(60.0 - prev, 1)
        severity = "critical" if prev < 50 else "warning"
        weight = gap * 1.1
        candidates.append({
            "key": "previous_marks",
            "weight": weight,
            "severity": severity,
            "title": "Bridge Prerequisite Concept Gaps",
            "category": "Foundations",
            "current_value": f"{prev:.1f}%",
            "target_value": ">= 60.0%",
            "deficit": f"Historical deficit of {gap}% in prerequisite coursework",
            "action": f"Identify root weak areas from previous semester coursework. Utilize curated video lectures and peer study circles to master foundational concepts.",
            "impact": "+6 to +10 pts by eliminating knowledge debt",
            "icon": "fa-book-open-reader"
        })

    # Sort recommendations by highest priority weight (biggest risk first)
    candidates.sort(key=lambda x: -x["weight"])

    # If the student is performing well and has no or few risks:
    if len(candidates) == 0:
        if score >= 85.0:
            candidates = [
                {
                    "key": "advanced_enrichment",
                    "weight": 10,
                    "severity": "positive",
                    "title": "Pursue Advanced Electives & Research",
                    "category": "Excellence",
                    "current_value": f"High Honor ({score:.1f})",
                    "target_value": "Top 5% Cohort",
                    "deficit": "None (Outstanding Performer)",
                    "action": "Consider enrolling in advanced research seminars, published paper writing, or competitive hackathons to further distinguish your academic portfolio.",
                    "impact": "Prepares for honors recognition and graduate admissions",
                    "icon": "fa-award"
                },
                {
                    "key": "peer_mentorship",
                    "weight": 8,
                    "severity": "positive",
                    "title": "Peer Tutoring & Academic Leadership",
                    "category": "Leadership",
                    "current_value": "Subject Mastery",
                    "target_value": "Department Mentor",
                    "deficit": "None",
                    "action": "Participate as a departmental peer tutor or study group lead to reinforce your foundational mastery while building leadership credentials.",
                    "impact": "Deepens long-term retention and institutional recognition",
                    "icon": "fa-users-gear"
                }
            ]
        else:
            candidates = [
                {
                    "key": "maintain_momentum",
                    "weight": 10,
                    "severity": "positive",
                    "title": "Maintain Steady Academic Consistency",
                    "category": "Maintenance",
                    "current_value": f"{score:.1f}/100",
                    "target_value": "≥ 80.0/100",
                    "deficit": "On Track",
                    "action": "Continue consistent attendance and timely assignment submissions while targeting incremental improvements in midterm test preparation.",
                    "impact": "+3 to +5 pts toward Distinction grade",
                    "icon": "fa-chart-line"
                }
            ]

    # Assign 1-based sequential priority rank
    for idx, rec in enumerate(candidates, start=1):
        rec["priority"] = idx

    return candidates
