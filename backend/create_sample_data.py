import pandas as pd
import numpy as np
import os


def create_dataset(n=250):
    """
    Creates a realistic synthetic student academic dataset for training
    and evaluating performance prediction and early-risk detection models.
    """
    np.random.seed(42)

    student_ids = [f"S{str(i+1).zfill(3)}" for i in range(n)]
    names = [
        "Aarav Sharma", "Aditi Patel", "Rohan Mehta", "Priya Nair", "Vikram Singh",
        "Ananya Rao", "Karthik Iyer", "Sneha Joshi", "Rahul Gupta", "Neha Verma",
        "Siddharth Verma", "Pooja Reddy", "Deepak Kumar", "Divya Menon", "Arjun Das",
        "Tanvi Shah", "Gaurav Malhotra", "Isha Deshmukh", "Naveen Choudhury", "Meera Kulkarni",
        "Aditya Bhat", "Riya Sen", "Manish Pandey", "Shruti Pillai", "Kunal Tiwari",
        "Swati Agarwal", "Varun Saxena", "Kavya Murthy", "Suresh Rathi", "Anjali Bose"
    ]
    # Expand names to length n
    full_names = [f"{names[i % len(names)]} {i//len(names) + 1}" if i >= len(names) else names[i] for i in range(n)]

    departments = [
        "Computer Science", "Information Technology", "Electronics", 
        "Mechanical", "Civil", "Electrical Engineering"
    ]

    data = {
        "student_id": student_ids,
        "name": full_names,
        "department": np.random.choice(departments, n),
        "semester": np.random.randint(1, 9, n),
        "age": np.random.randint(18, 25, n),
        "gender": np.random.choice(["Male", "Female", "Other"], n, p=[0.50, 0.46, 0.04]),
    }

    # Generate correlated academic features
    # Base academic capability latent variable (0.0 to 1.0)
    latent_ability = np.random.beta(5, 3, n)

    # Attendance Percentage (0-100)
    base_attendance = 40 + 55 * latent_ability + np.random.normal(0, 6, n)
    data["attendance"] = np.clip(np.round(base_attendance, 1), 35.0, 100.0)

    # Weekly Study Hours (0-40 hrs/week)
    base_study = 4 + 25 * latent_ability + np.random.normal(0, 3, n)
    data["study_hours"] = np.clip(np.round(base_study, 1), 1.0, 38.0)

    # Assignment Completion Percentage (0-100)
    base_assignment = 30 + 60 * latent_ability + 0.15 * (data["attendance"] - 70) + np.random.normal(0, 5, n)
    data["assignment_score"] = np.clip(np.round(base_assignment, 1), 20.0, 100.0)

    # Internal Assessment Marks (0-100)
    base_internal = 25 + 65 * latent_ability + 0.10 * (data["attendance"] - 70) + np.random.normal(0, 5, n)
    data["internal_marks"] = np.clip(np.round(base_internal, 1), 20.0, 100.0)

    # Previous Semester Performance / GPA (scaled 0-100)
    base_previous = 30 + 60 * latent_ability + np.random.normal(0, 6, n)
    data["previous_marks"] = np.clip(np.round(base_previous, 1), 25.0, 100.0)

    # Final Academic Performance Score (Target: 0-100)
    # Realistic weighted academic formulation
    final_score = (
        0.30 * data["internal_marks"] +
        0.25 * data["previous_marks"] +
        0.20 * data["assignment_score"] +
        0.15 * data["attendance"] +
        0.40 * data["study_hours"] +
        np.random.normal(0, 2.5, n)
    )
    data["final_score"] = np.clip(np.round(final_score, 1), 20.0, 100.0)

    df = pd.DataFrame(data)

    output_path = os.path.join(os.path.dirname(__file__), "datasets", "student_dataset.csv")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Sample dataset generated with {n} records at: {output_path}")
    return df


if __name__ == "__main__":
    df = create_dataset(250)
    print(f"\nColumns: {list(df.columns)}")
    print(f"\nSample data:\n{df.head(5)}")
    print(f"\nStats:\n{df.describe()}")