# EduPredict AI — Intelligent Student Performance & Early Risk Detection

## Problem Statement

Develop an ML-based system that predicts a student's academic performance using parameters such as attendance, internal marks, assignment completion, previous semester performance, and study hours. The system identifies students who may be academically at risk and provides personalized recommendations.

## Team Members

**Team Lead**: Kalyana kumar M

**Members**:
- Dharun Raja VS
- Kamalesh S

**Collaborators**:
1. kamaleshshanmugam19-ui
2. dharunrajavs

---

## Deployment Architecture

```
                    ┌──────────────────┐
                    │      Vercel      │
                    │    Frontend      │
                    └────────┬─────────┘
                             │
                             │ HTTPS API
                             ↓
                    ┌──────────────────┐
                    │      Render      │
                    │ Flask Backend    │
                    │ ML Prediction    │
                    └────────┬─────────┘
                             │
                             │ PostgreSQL
                             ↓
                    ┌──────────────────┐
                    │     Supabase     │
                    │ PostgreSQL DB    │
                    └──────────────────┘
```

---

## Tech Stack

- **Frontend**: HTML5, CSS3, JavaScript (ES6+), Bootstrap 5, Chart.js, FontAwesome
- **Backend**: Python, Flask, Flask-CORS, Flask-Session, Gunicorn, Psycopg2-binary, SQLAlchemy
- **Machine Learning**: Scikit-learn (Linear Regression, Random Forest Regressor), Pandas, NumPy, Joblib
- **Database**: Supabase PostgreSQL / SQLite fallback
- **File Ingestion**: CSV, Excel (.xlsx, .xls) via OpenPyXL and Pandas

---

## Deployment Configuration

### 1. Render (Backend Deployment)

- **Environment**: Python
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn wsgi:app`
- **Environment Variables**:
  - `DATABASE_URL`: `postgresql://<user>:<password>@<host>:5432/postgres`
  - `SUPABASE_URL`: `https://<your-project>.supabase.co`
  - `SUPABASE_PUBLISHABLE_KEY`: `<your-supabase-publishable-key>`
  - `FRONTEND_URL`: `https://<your-vercel-frontend-url>`
  - `SECRET_KEY`: `<secure-random-private-secret-key>`
  - `FLASK_ENV`: `production`
  - `DEBUG`: `False`

### 2. Vercel (Frontend Deployment)

- **Root Directory**: `./` (or `frontend`)
- **Framework Preset**: Other (Static)
- **Environment Variables**:
  - `NEXT_PUBLIC_SUPABASE_URL`: `https://<your-project>.supabase.co`
  - `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`: `<your-supabase-publishable-key>`
  - `NEXT_PUBLIC_API_URL`: `https://<your-render-backend-url>`
  - `VITE_SUPABASE_URL`: `https://<your-project>.supabase.co`
  - `VITE_SUPABASE_PUBLISHABLE_KEY`: `<your-supabase-publishable-key>`
  - `VITE_API_URL`: `https://<your-render-backend-url>`

---

## Local Development

1. Create a Python virtual environment:
   ```bash
   python -m venv backend/venv
   source backend/venv/bin/activate  # On Windows: .\backend\venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy environment template:
   ```bash
   cp .env.example .env
   ```
4. Run the backend server:
   ```bash
   python wsgi.py
   # or
   python backend/app.py
   ```
5. Open `http://localhost:5000` in your web browser.
