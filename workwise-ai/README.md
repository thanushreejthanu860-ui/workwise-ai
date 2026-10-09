# WorkWise AI 💼

An **AI-powered job and internship portal for Indian freshers and informal
workers**. Supports **UN SDG 8 — Decent Work and Economic Growth**.

WorkWise AI combines a Flask + SQLite backend, real scikit-learn models
(role classifier, fair-wage regressor, salary regressor), cosine-similarity
job matching, a resume builder, career roadmaps (SVG/PNG), interview prep
and an offline-first chatbot — with a modern, responsive, dark-mode UI in
vanilla HTML/CSS/JS (no frontend framework).

> ⚠️ All job listings are **SAMPLE DATA** (fictional). All ML models are
> trained on **SYNTHETIC** demonstration data. Estimates are general
> guidance, not legal, employment or financial advice.

---

## 📖 Table of contents

1. [Features](#features)
2. [Technology stack](#technology-stack)
3. [Architecture](#architecture)
4. [Folder structure](#folder-structure)
5. [Database architecture](#database-architecture)
6. [ML architecture](#ml-architecture)
7. [Datasets & synthetic data](#datasets--synthetic-data)
8. [Installation (Windows)](#installation-windows)
9. [Installation (Linux / macOS)](#installation-linux--macos)
10. [Train the models](#train-the-models)
11. [Run the application](#run-the-application)
12. [API documentation](#api-documentation)
13. [ML metrics explained](#ml-metrics-explained)
14. [Limitations](#limitations)
15. [Security notes](#security-notes)
16. [Future scope](#future-scope)

---

## Features

- **Landing page** — hero search (skills/designation/company, experience,
  location), category chips, featured jobs, top companies, how-it-works,
  AI-matching explainer, SDG 8 section, CTA.
- **Authentication** — register/login/logout with validated forms and
  Werkzeug password hashing (`generate_password_hash` / `check_password_hash`),
  Flask session cookies.
- **Jobs & internships** — search + filters (location, experience, job type,
  work mode, category, salary range), dedicated internships tab, job detail
  pages with reviews, perks and illustrative visuals.
- **AI job matching** — real **cosine similarity** between the user's skill
  vector and each job's required-skill vector → **AI Fit %** and **Skill Gap**
  (missing skills). `POST /api/match-jobs` returns jobs sorted by match score.
- **ML job role classifier** — multi-hot encoded skills → top-3 roles with
  probabilities. RandomForest vs DecisionTree vs LogisticRegression compared
  with 5-fold cross-validation; metrics (accuracy, precision, recall, F1),
  confusion matrix PNG and feature-importance CSV saved to `ml/reports/`.
- **Fair wage regressor** — trade + city type + experience → predicted daily
  wage with lower/upper range and verdict. RandomForestRegressor vs
  GradientBoostingRegressor; MAE / RMSE / R² reported.
- **Job salary regressor** — role + skills + experience + city → expected
  monthly salary (RandomForestRegressor).
- **Apply flow** — validated application form (email, phone, 10th %, 12th %,
  CGPA, summary, projects, certificates) with confirmation and status timeline.
- **User profile** — editable profile with skill proficiency
  (Beginner/Intermediate/Advanced) and a computed **Profile Strength %**.
- **Resume builder** — live A4 preview, **Download PDF** (`window.print()`),
  **Download Word (.doc)** generated in-browser.
- **Dashboard** — stat cards, notification bell + banner, four Chart.js
  charts (area, line, bar, donut), applied jobs/internships/saved jobs lists
  and a simulated application status timeline
  (Applied → Under Review → Shortlisted → Interview Scheduled → Offer).
- **Fair Wage page** — wage estimates for 6 informal trades with a clear
  legal disclaimer.
- **Career roadmaps** — 5-stage SVG roadmap with numbered stages, durations,
  skill chips (your skills are ticked), JOB-READY finish line, and
  **Download PNG / SVG** buttons.
- **Interview prep** — 8 roles, interview rounds, 6 questions each with
  "why they ask" and sample answers, YouTube search links, and a practice
  box with offline AI feedback (clarity, relevance, structure, missing points).
- **Chatbot** — floating assistant with quick buttons; works **100% offline**
  with a rule-based intent engine; optional external LLM via `.env`.
- **Design system** — CSS variables, light/dark theme toggle, responsive
  breakpoints, accessible semantic HTML.

## Technology stack

| Layer | Tech |
|---|---|
| Backend | Python 3, Flask, Flask-SQLAlchemy, Flask-CORS, python-dotenv |
| Auth | Werkzeug password hashing, Flask sessions |
| ML | scikit-learn, pandas, numpy, joblib, matplotlib, seaborn |
| DB | SQLite |
| Frontend | HTML5, CSS3, vanilla JS, Flexbox/Grid, Chart.js (local), SVG |
| Optional | OpenAI-compatible LLM via `.env` (never required) |

## Architecture

```
Browser (templates + static/js)
      │  fetch("/api/...")
      ▼
Flask app.py  ──► SQLAlchemy models ──► SQLite (workwise.db)
      │
      ├── ml/predict.py ──► joblib models (ml/saved_models/)
      │        ▲
      │        │ trained by
      └── ml/train_model.py ◄── data/*.csv (synthetic)
```

The app auto-trains models on first run if `ml/saved_models/` is empty.

## Folder structure

```
workwise-ai/
├── app.py                  # Flask app: routes, API, seeding, auth
├── models.py               # SQLAlchemy models (13 tables)
├── content.py              # Roadmaps, interview Q&A, chatbot intents
├── requirements.txt        # Pinned dependencies
├── README.md
├── .env.example            # Optional LLM config template
├── .gitignore
├── ml/
│   ├── __init__.py
│   ├── train_model.py      # Trains all 3 models + reports
│   ├── predict.py          # Prediction helpers (cosine match, etc.)
│   ├── saved_models/       # role_classifier.joblib, wage_regressor.joblib, ...
│   └── reports/            # role_confusion_matrix.png, role_metrics.json, ...
├── data/
│   ├── jobs.csv            # 24 fictional listings
│   ├── job_skills_training.csv
│   ├── wages.csv
│   ├── salaries.csv
│   ├── generate_synthetic_data.py
│   └── README_DATA.md
├── static/
│   ├── css/style.css       # Design system (light/dark, responsive)
│   ├── css/print.css       # A4 print stylesheet
│   ├── js/                 # main, jobs, dashboard, profile, resume,
│   │                       # wage, roadmap, interview, chatbot, chart.min.js
│   └── images/             # 36 original PNGs (tools/generate_images.py)
└── templates/              # 13 Jinja2 templates
```

All images are **original** and generated offline with Pillow — no external
or copyrighted assets. Regenerate them with:

```bash
python tools/generate_images.py
```

This creates the logo, hero illustration, 12 fictional company logos,
8 role illustrations, 5 category illustrations, 3 tool illustrations,
4 how-it-works steps, the SDG 8 graphic and a default avatar.

## Database architecture

SQLite via Flask-SQLAlchemy. Tables: `users`, `profiles`, `skills`,
`user_skills`, `education`, `jobs`, `applications`, `saved_jobs`,
`notifications`, `resumes`, `projects`, `certificates`, `experience`,
`interview_practice`.

Key relationships:

- `User` → 1:1 `Profile`, 1:N `Application`, `SavedJob`, `Notification`,
  `UserSkill`, `Education`, `Project`, `Certificate`, `Experience`,
  `Resume`, `InterviewPractice`
- `UserSkill` → N:1 `Skill` (canonical vocabulary of 55 skills)
- `Application` → N:1 `Job`; `SavedJob` → N:1 `Job` (unique per user)

Passwords are **never** stored in plaintext — only Werkzeug hashes.

Seed with one command:

```bash
python app.py init-db
```

This creates tables, seeds 55 canonical skills, 24 fictional jobs and a
demo user (`demo@workwise.ai` / `demo1234`) with profile, skills,
education, project, certificate, experience, applications, a saved job,
notifications and a resume.

## ML architecture

### 1. Job Role Classifier (`POST /api/predict-role`)
- Input: list of skills → **multi-hot encoding** (`MultiLabelBinarizer`)
- Models compared: **RandomForestClassifier, DecisionTreeClassifier,
  LogisticRegression** (5-fold cross-validation, best is saved)
- Output: top 3 roles with probabilities
- Reports: `role_confusion_matrix.png`, `role_metrics.json`,
  `role_feature_importance.csv`

### 2. Fair Wage Regressor (`POST /api/predict-wage`)
- Input: trade (one-hot), city_type (one-hot), experience (numeric)
- Models compared: **RandomForestRegressor, GradientBoostingRegressor**
- Output: predicted daily wage, lower/upper range (±1 residual std),
  verdict (Under typical / Fair / Above typical)
- Report: `wage_metrics.json` (MAE, RMSE, R²)

### 3. Job Salary Regressor (`POST /api/predict-salary`)
- Input: role (one-hot), city (one-hot), skills (multi-hot), experience
- Model: **RandomForestRegressor**
- Output: predicted monthly salary with ±10% range
- Report: `salary_metrics.json`

### 4. Skill matching (`POST /api/match-jobs`)
- Cosine similarity over the union vocabulary of user skills and job skills,
  scaled to 0–100 → **AI Fit %**; missing skills → **Skill Gap**.

All models are persisted with **joblib** in `ml/saved_models/` and loaded
at prediction time. No prediction is hard-coded.

## Datasets & synthetic data

Data lives in `data/` and is loaded from CSV at training time. The datasets
are **synthetic** (generated by `data/generate_synthetic_data.py`,
seeded RNG for reproducibility). At startup/training the app prints:

```
WARNING: Using SYNTHETIC training data. Results are for demonstration
only and are not real-world salary or employment statistics.
```

See **data/README_DATA.md** for exact CSV columns and pointers to real
open datasets (Kaggle, NSSO/PLFS, Ministry of Labour minimum-wage
notifications) if you want to replace the synthetic data.

## Installation (Windows)

```powershell
cd workwise-ai
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python ml/train_model.py
python app.py init-db
python app.py
```

## Installation (Linux / macOS)

```bash
cd workwise-ai
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 ml/train_model.py
python3 app.py init-db
python3 app.py
```

## Train the models

```bash
python ml/train_model.py     # Windows
python3 ml/train_model.py    # Linux/macOS
```

Trains all three models, saves them to `ml/saved_models/` and writes
metrics/reports to `ml/reports/`. Takes ~30–60 seconds on a typical laptop.

## Run the application

```bash
python app.py        # Windows
python3 app.py       # Linux/macOS
```

Then open **http://127.0.0.1:5000**

Demo login: **demo@workwise.ai** / **demo1234**

## API documentation

Base URL: `http://127.0.0.1:5000`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/api/jobs` | — | List jobs; filters: `q, location, experience, job_type, work_mode, category, min_salary, max_salary, type=internship, sort` |
| GET | `/api/jobs/<id>` | — | Job detail (+ AI Fit & skill gap if logged in) |
| POST | `/api/jobs/<id>/save` | ✅ | Save a job |
| DELETE | `/api/jobs/<id>/save` | ✅ | Unsave a job |
| POST | `/api/jobs/<id>/apply` | ✅ | Apply (JSON: email, phone, tenth_percent, twelfth_percent, cgpa, summary, projects, certificates) |
| POST | `/api/match-jobs` | — | `{"skills": ["Python","SQL"]}` → jobs sorted by cosine match |
| POST | `/api/predict-role` | — | `{"skills": [...]}` → top 3 roles + probabilities |
| POST | `/api/predict-wage` | — | `{"trade","city_type","experience"}` → wage + range + verdict |
| POST | `/api/predict-salary` | — | `{"role","skills","experience","city"}` → salary + range |
| POST | `/api/chat` | — | `{"message": "..."}` → offline rule-based reply (optional LLM) |
| POST | `/api/roadmap` | — | `{"role": "..."}` → 5 stages |
| POST | `/api/interview/questions` | — | `{"role": "..."}` → rounds + 6 questions |
| POST | `/api/practice` | ✅ | `{"role","question","answer"}` → feedback scores |
| GET | `/api/dashboard` | ✅ | Stats, charts data, applications, saved jobs, notifications |
| GET | `/api/profile` | ✅ | Full profile + profile_strength |
| PUT | `/api/profile` | ✅ | Update profile fields |
| POST | `/api/profile/skills` | ✅ | Add/update skill `{name, proficiency, years}` |
| DELETE | `/api/profile/skills/<id>` | ✅ | Remove a skill |
| GET | `/api/notifications` | ✅ | Notifications + unread count |
| POST | `/api/notifications/read` | ✅ | Mark all read |
| GET / POST / PUT | `/api/resume` | ✅ | Get / save resume JSON |
| GET | `/api/skills` | — | Skill autocomplete |
| GET | `/api/info` | — | App info, trades, city types, disclaimer |

### Example requests

```bash
# Match jobs by skills (curl)
curl -X POST http://127.0.0.1:5000/api/match-jobs ^
  -H "Content-Type: application/json" ^
  -d "{\"skills\": [\"Python\", \"SQL\", \"Power BI\"]}"

# Predict a role
curl -X POST http://127.0.0.1:5000/api/predict-role ^
  -H "Content-Type: application/json" ^
  -d "{\"skills\": [\"Python\", \"SQL\", \"Pandas\", \"Power BI\"]}"

# Fair wage estimate
curl -X POST http://127.0.0.1:5000/api/predict-wage ^
  -H "Content-Type: application/json" ^
  -d "{\"trade\": \"Electrician\", \"city_type\": \"Metro\", \"experience\": 5}"
```

(On Linux/macOS use `\` instead of `^` for line continuation.)

Error responses are JSON: `{"error": "...", "status": 400}` with the
correct HTTP status code (400 bad input, 401 auth required, 404 not
found, 409 duplicate application, 500 server error).

## ML metrics explained

- **Accuracy** — share of correct predictions.
- **Precision** — of all predicted positives, how many were correct.
- **Recall** — of all actual positives, how many were found.
- **F1-score** — harmonic mean of precision and recall.
- **Cross-validation (5-fold)** — train/evaluate 5 times on different
  splits to estimate generalisation.
- **Confusion matrix** — per-class correct vs incorrect predictions.
- **MAE / RMSE** — average absolute / root-mean-square prediction error (₹).
- **R²** — share of variance explained (1.0 = perfect).

Current model performance is stored in `ml/reports/*_metrics.json`
(synthetic data — demonstration only).

## Limitations

- All listings are fictional; models are trained on synthetic data —
  predictions are **not** real market wages or salaries.
- The status timeline is a demo simulation, not a real recruiter workflow.
- The chatbot is rule-based (regex intents); the optional LLM requires
  an API key and network access.
- SQLite is not suitable for production concurrency; use PostgreSQL there.
- PDF resume export uses the browser's print dialog (choose "Save as PDF").

## Security notes

- Passwords are hashed with Werkzeug (salted PBKDF2/scrypt); never plaintext.
- Flask sessions are signed cookies; set a strong `SECRET_KEY` in `.env`.
- All API inputs are validated; SQL goes through SQLAlchemy parameterisation.
- API keys (if any) are read from `.env` — never hard-coded.
- CORS is enabled for API consumption; tighten origins in production.

## Future scope

- Real datasets + periodic retraining; model versioning (MLflow).
- Resume parsing (PDF/DOCX upload) with NER for skills.
- Real-time interview mock calls (speech-to-text).
- Employer portal with verified job postings.
- Regional-language support and accessibility improvements.
- Deployment: Docker + Gunicorn + PostgreSQL on a cloud VM.

---

*WorkWise AI — educational demo project supporting UN SDG 8.*
