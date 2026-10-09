"""WorkWise AI - AI-powered job and internship portal for Indian freshers.

Supports UN SDG 8 (Decent Work and Economic Growth).

This module wires up:
  - SQLite database (Flask-SQLAlchemy) with seeded sample jobs
  - Session-based authentication (Werkzeug password hashing)
  - REST API for jobs, AI matching, ML predictions and the chatbot
  - Server-rendered pages (Jinja2 templates + vanilla JS frontend)

Run:
    python app.py            # starts on http://127.0.0.1:5000
    python app.py init-db    # create tables + seed sample data
"""

import csv
import json
import os
import random
import sys
import urllib.request
from datetime import datetime, timedelta

from flask import (Flask, jsonify, redirect, render_template, request,
                   session, url_for)
from flask_cors import CORS

# Make the `ml` package importable (models, predictions)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "ml"))

from dotenv import load_dotenv

load_dotenv()  # optional .env file (LLM_API_KEY etc.)

import models
from models import (Application, Certificate, Education, Experience,
                    InterviewPractice, Job, Notification, Profile,
                    Project, Resume, SavedJob, Skill, User, UserSkill, db)

# ---------------------------------------------------------------------------
# App configuration
# ---------------------------------------------------------------------------
app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "workwise.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024  # 2 MB request cap

db.init_app(app)
CORS(app)  # enable CORS for the REST API

DATA_DIR = os.path.join(BASE_DIR, "data")
MODEL_DIR = os.path.join(BASE_DIR, "ml", "saved_models")

SYNTHETIC_WARNING = (
    "WARNING: Using SYNTHETIC training data. Results are for "
    "demonstration only and are not real-world salary or employment "
    "statistics."
)
DISCLAIMER = (
    "WorkWise AI uses sample job listings and indicative salary/wage "
    "estimates for demonstration and general guidance. Listings are "
    "fictional unless explicitly stated otherwise. Wage and salary "
    "estimates are not legal, employment, or financial advice."
)

# ---------------------------------------------------------------------------
# ML model loading (with automatic training fallback)
# ---------------------------------------------------------------------------
_models_loaded = None


def ensure_ml_models():
    """Load ML models lazily; train them automatically if missing."""
    global _models_loaded
    if _models_loaded is True:
        return True
    required = [
        "role_classifier.joblib", "role_encoder.joblib",
        "wage_regressor.joblib", "wage_encoder.joblib",
        "salary_regressor.joblib", "salary_encoder.joblib",
    ]
    missing = [f for f in required
               if not os.path.exists(os.path.join(MODEL_DIR, f))]
    if missing:
        print(SYNTHETIC_WARNING)
        print("ML models not found. Training now (first run only)...")
        try:
            import train_model  # noqa: PLC0415 (local import)
            train_model.main()
        except Exception as exc:  # pragma: no cover - diagnostic path
            print(f"Auto-training failed: {exc}")
            _models_loaded = False
            return False
    import predict  # noqa: PLC0415
    sys.modules.setdefault("predict", predict)
    _models_loaded = True
    return True


def ml_predict(function_name, *args):
    """Call a function from ml/predict.py with graceful error handling."""
    if not ensure_ml_models():
        raise RuntimeError(
            "ML models are not available. Run: python ml/train_model.py"
        )
    import predict  # noqa: PLC0415
    return getattr(predict, function_name)(*args)


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
def current_user():
    """Return the logged-in User or None."""
    user_id = session.get("user_id")
    if not user_id:
        return None
    return db.session.get(User, user_id)


def login_required(view):
    """Decorator: redirect anonymous users to /login."""
    from functools import wraps

    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            if request.path.startswith("/api/"):
                return jsonify({"error": "Authentication required"}), 401
            session["next"] = request.path
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


def error_response(message, status=400):
    """Standard JSON error body."""
    return jsonify({"error": message, "status": status}), status


def require_json():
    """Return parsed JSON body or an error response."""
    if not request.is_json:
        return None, error_response("Request must be JSON (Content-Type: application/json)", 400)
    data = request.get_json(silent=True)
    if data is None:
        return None, error_response("Invalid JSON body", 400)
    return data, None


def add_notification(user_id, message, kind="info"):
    """Create an in-app notification for a user."""
    n = Notification(user_id=user_id, message=message, kind=kind)
    db.session.add(n)


def user_skills_list(user):
    """Return the logged-in user's skill names."""
    return [us.skill.name for us in user.user_skills.all() if us.skill]


# Order matches tools/generate_images.py so each fictional
# company gets its own generated logo.
COMPANY_LOGO_ORDER = [
    "NovaByte Labs", "DataNest Analytics", "CloudOrbit Systems",
    "BrightBridge Technologies", "PixelForge Studio", "GreenGrid Mobility",
    "InsightLoop", "CodeVista", "SkillSpring", "NextWave Digital",
    "QuantLeaf Research", "UrbanPulse Ventures",
]


def company_image(company):
    """Return the generated logo filename for a company."""
    try:
        idx = COMPANY_LOGO_ORDER.index(company) + 1
    except ValueError:
        # stable fallback for unknown companies
        idx = (sum(ord(c) for c in company) % 12) + 1
    return f"company-{idx}.png"


def role_image(job):
    """Return a role illustration filename based on the job title."""
    title = (job.title or "").lower()
    if "data scientist" in title:
        return "role-2.png"
    if "web" in title:
        return "role-4.png"
    if any(k in title for k in ("software", "python", "full stack",
                                  "frontend", "ui/ux", "developer")):
        return "role-3.png"
    if "marketing" in title or "social" in title:
        return "role-5.png"
    if "hr" in title or "recruit" in title:
        return "role-6.png"
    if "business analyst" in title:
        return "role-8.png"
    if any(k in title for k in ("sales", "business development",
                                  "customer", "operations")):
        return "role-7.png"
    return "role-1.png"


def job_to_dict(job, fit=None, gap=None, user_skills=None):
    """Serialize a Job for JSON responses and templates."""
    return {
        "id": job.id,
        "title": job.title,
        "company": job.company,
        "company_image": company_image(job.company),
        "role_image": role_image(job),
        "location": job.location,
        "job_type": job.job_type,
        "work_mode": job.work_mode,
        "category": job.category,
        "is_internship": bool(job.is_internship),
        "experience_min": job.experience_min,
        "experience_max": job.experience_max,
        "experience_text": job.experience_text(),
        "salary_min": job.salary_min,
        "salary_max": job.salary_max,
        "salary_text": job.salary_text(),
        "team_size": job.team_size,
        "duration": job.duration,
        "description": job.description,
        "responsibilities": job.responsibilities,
        "perks": job.perks,
        "skills": job.skill_list(),
        "is_sample": bool(job.is_sample),
        "ai_fit": fit,
        "skill_gap": gap,
        "applicants": 0,  # fictional listings do not track real applicants
    }


# Expose image helpers to all Jinja templates
app.jinja_env.globals.update(
    company_image=company_image,
    role_image=role_image,
)


# ---------------------------------------------------------------------------
# Database seeding
# ---------------------------------------------------------------------------
def seed_database():
    """Create tables and seed fictional sample jobs + a demo user."""
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("Database tables created.")

        # --- Seed canonical skills from the training CSV -------------
        skills_path = os.path.join(DATA_DIR, "job_skills_training.csv")
        skill_names = set()
        with open(skills_path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                for s in str(row["skills"]).split(";"):
                    s = s.strip()
                    if s:
                        skill_names.add(s)
        for name in sorted(skill_names):
            db.session.add(Skill(name=name))
        db.session.commit()
        print(f"Seeded {len(skill_names)} canonical skills.")

        # --- Seed fictional jobs -------------------------------------
        jobs_path = os.path.join(DATA_DIR, "jobs.csv")
        count = 0
        with open(jobs_path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                job = Job(
                    title=row["title"], company=row["company"],
                    location=row["location"], job_type=row["job_type"],
                    work_mode=row["work_mode"], category=row["category"],
                    is_internship=bool(int(row["is_internship"])),
                    experience_min=int(row["experience_min"]),
                    experience_max=int(row["experience_max"]),
                    salary_min=int(row["salary_min"]),
                    salary_max=int(row["salary_max"]),
                    salary_period=row["salary_period"],
                    team_size=int(row["team_size"]),
                    duration=row["duration"],
                    description=row["description"],
                    responsibilities=row["responsibilities"],
                    perks=row["perks"], skills=row["skills"],
                    is_sample=True,
                )
                db.session.add(job)
                count += 1
        db.session.commit()
        print(f"Seeded {count} SAMPLE fictional jobs/internships.")

        # --- Demo user (password: demo1234) -------------------------
        demo = User(name="Demo Student", email="demo@workwise.ai",
                    role="jobseeker")
        demo.set_password("demo1234")
        db.session.add(demo)
        db.session.commit()

        demo.profile = Profile(
            headline="Aspiring Data Analyst | Python + SQL",
            about="Final-year BCA student passionate about data, "
                  "analytics and building useful tools.",
            phone="9876543210", location="Bengaluru, Karnataka",
            preferred_role="Data Analyst", job_type="Full-time",
            work_mode="Hybrid", preferred_location="Bengaluru",
            expected_salary="25000-35000",
            links=json.dumps({"LinkedIn": "https://linkedin.example/demo",
                              "GitHub": "https://github.example/demo"}),
            languages=json.dumps(["English", "Hindi", "Kannada"]),
            hobbies=json.dumps(["Cricket", "Reading", "Chess"]),
        )
        # Demo skills
        skill_map = {s.name: s for s in Skill.query.all()}
        for skill_name, prof, years in [
            ("Python", "Intermediate", 1.0),
            ("SQL", "Intermediate", 0.5),
            ("Excel", "Advanced", 2.0),
            ("Statistics", "Beginner", 0.5),
        ]:
            if skill_name in skill_map:
                db.session.add(UserSkill(
                    user_id=demo.id, skill_id=skill_map[skill_name].id,
                    proficiency=prof, years=years))
        db.session.add(Education(user_id=demo.id, level="10th",
                                 institution="St. Mary's High School",
                                 percentage_or_cgpa="88%", year="2020"))
        db.session.add(Education(user_id=demo.id, level="12th",
                                 institution="City Junior College",
                                 percentage_or_cgpa="82%", year="2022"))
        db.session.add(Education(user_id=demo.id, level="Bachelor (BCA)",
                                 institution="State University",
                                 percentage_or_cgpa="8.1 CGPA", year="2025"))
        db.session.add(Project(user_id=demo.id,
                               title="Sales Dashboard (Power BI)",
                               description="Interactive dashboard analysing "
                                           "regional sales trends.",
                               technologies="Power BI, SQL, Excel",
                               link=""))
        db.session.add(Certificate(user_id=demo.id,
                                   title="Python for Data Science",
                                   issuer="Coursera (sample)", year="2024"))
        db.session.add(Experience(user_id=demo.id, title="Data Intern",
                                  company="Sample Startup",
                                  start_date="May 2024", end_date="Jul 2024",
                                  description="Cleaned sample datasets and "
                                              "built summary reports."))
        db.session.commit()

        # Demo application + saved job + notifications + resume
        job = Job.query.filter_by(title="Data Analyst (Fresher)").first()
        if job:
            timeline = [{"status": "Applied",
                         "date": datetime.utcnow().isoformat(timespec="seconds")}]
            appn = Application(user_id=demo.id, job_id=job.id,
                               email=demo.email, phone=demo.profile.phone,
                               tenth_percent="88%", twelfth_percent="82%",
                               cgpa="8.1", summary="Demo application.",
                               projects="Sales Dashboard",
                               certificates="Python for Data Science",
                               status="Applied", timeline=json.dumps(timeline))
            db.session.add(appn)
            db.session.add(SavedJob(user_id=demo.id, job_id=job.id))
        int_job = Job.query.filter_by(title="Data Analyst Intern").first()
        if int_job:
            tl = [{"status": "Applied",
                   "date": datetime.utcnow().isoformat(timespec="seconds")}]
            db.session.add(Application(
                user_id=demo.id, job_id=int_job.id, email=demo.email,
                phone=demo.profile.phone, tenth_percent="88%",
                twelfth_percent="82%", cgpa="8.1",
                summary="Demo internship application.",
                projects="Sales Dashboard",
                certificates="Python for Data Science",
                status="Applied", timeline=json.dumps(tl)))
        db.session.add(Resume(user_id=demo.id, data=json.dumps({
            "name": demo.name, "headline": demo.profile.headline,
            "email": demo.email, "phone": demo.profile.phone,
            "location": demo.profile.location,
        })))
        for msg, kind in [
            ("Welcome to WorkWise AI! Complete your profile to see your "
             "AI Fit scores.", "info"),
            ("Tip: add more skills to improve your job matches.", "tip"),
            ("Your application for Data Analyst (Fresher) is under "
             "review.", "application"),
        ]:
            db.session.add(Notification(user_id=demo.id, message=msg, kind=kind))
        db.session.commit()
        print("Seeded demo user: demo@workwise.ai / demo1234")


# ---------------------------------------------------------------------------
# Page routes
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    """Landing page with featured jobs and categories."""
    featured = Job.query.order_by(Job.id.desc()).limit(6).all()
    companies = sorted({j.company for j in Job.query.all()})
    user = current_user()
    fit_map = {}
    if user:
        my_skills = user_skills_list(user)
        for j in featured:
            fit_map[j.id] = ml_predict("skill_match_score", my_skills,
                                       j.skill_list())
    return render_template("index.html", featured=featured,
                           companies=companies, user=user,
                           fit_map=fit_map, disclaimer=DISCLAIMER)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Login page and form handler."""
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        if not email or not password:
            return render_template("login.html",
                                   error="Email and password are required.")
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            return render_template("login.html",
                                   error="Invalid email or password.")
        if not user.is_active:
            return render_template("login.html",
                                   error="This account is deactivated.")
        session.clear()
        session["user_id"] = user.id
        add_notification(user.id, "You logged in to WorkWise AI.", "info")
        db.session.commit()
        nxt = session.pop("next", None)
        return redirect(nxt or url_for("dashboard"))
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Registration page and form handler."""
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        confirm = request.form.get("confirm_password") or ""

        errors = []
        if not name:
            errors.append("Name is required.")
        if not email or "@" not in email or "." not in email.split("@")[-1]:
            errors.append("Please enter a valid email address.")
        if len(password) < 8:
            errors.append("Password must be at least 8 characters.")
        if password != confirm:
            errors.append("Passwords do not match.")
        if User.query.filter_by(email=email).first():
            errors.append("An account with this email already exists.")
        if errors:
            return render_template("register.html", errors=errors,
                                   name=name, email=email)

        user = User(name=name, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        session.clear()
        session["user_id"] = user.id
        add_notification(user.id,
                         "Welcome to WorkWise AI! Complete your profile.",
                         "info")
        db.session.commit()
        return redirect(url_for("dashboard"))
    return render_template("register.html")


@app.route("/logout")
def logout():
    """Log the user out."""
    session.clear()
    return redirect(url_for("index"))


@app.route("/jobs")
def jobs():
    """Jobs & internships listing page."""
    return render_template("jobs.html", user=current_user(),
                           disclaimer=DISCLAIMER)


@app.route("/job/<int:job_id>")
def job_details(job_id):
    """Single job details page."""
    job = db.session.get(Job, job_id)
    if not job:
        return render_template("404.html", message="Job not found."), 404
    user = current_user()
    fit, gap = None, None
    if user:
        my_skills = user_skills_list(user)
        fit = ml_predict("skill_match_score", my_skills, job.skill_list())
        gap = ml_predict("compute_skill_gap", my_skills, job.skill_list())
    saved = bool(user and SavedJob.query.filter_by(
        user_id=user.id, job_id=job.id).first())
    return render_template("job_details.html", job=job, user=user,
                           fit=fit, gap=gap, saved=saved,
                           disclaimer=DISCLAIMER)


@app.route("/job/<int:job_id>/apply")
@login_required
def apply_page(job_id):
    """Application form page."""
    job = db.session.get(Job, job_id)
    if not job:
        return render_template("404.html", message="Job not found."), 404
    return render_template("apply.html", job=job, user=current_user())


@app.route("/dashboard")
@login_required
def dashboard():
    """User dashboard page."""
    return render_template("dashboard.html", user=current_user(),
                           disclaimer=DISCLAIMER)


@app.route("/profile")
@login_required
def profile_page():
    """Editable user profile page."""
    return render_template("profile.html", user=current_user())


@app.route("/resume")
@login_required
def resume_page():
    """Resume builder page."""
    return render_template("resume_builder.html", user=current_user())


@app.route("/fair-wage")
def fair_wage():
    """Fair wage check page."""
    return render_template("fair_wage.html", user=current_user(),
                           disclaimer=DISCLAIMER)


@app.route("/roadmaps")
def roadmaps():
    """Career roadmap generator page."""
    return render_template("roadmaps.html", user=current_user())


@app.route("/interview-prep")
def interview_prep():
    """Interview preparation page."""
    return render_template("interview_prep.html", user=current_user())


# ---------------------------------------------------------------------------
# REST API - jobs
# ---------------------------------------------------------------------------
EXPERIENCE_FILTERS = {
    "fresher": (0, 0),
    "1-2": (1, 2),
    "3-5": (3, 5),
    "5plus": (5, 99),
}


def filter_jobs(query, only_internships=None):
    """Apply query-string filters to a Job query."""
    if only_internships is None:
        type_param = request.args.get("type", "").lower()
        only_internships = type_param == "internship"
    if only_internships:
        query = query.filter(Job.is_internship.is_(True))

    q = (request.args.get("q") or "").strip()
    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(Job.title.ilike(like), Job.company.ilike(like),
                   Job.skills.ilike(like), Job.location.ilike(like),
                   Job.description.ilike(like),
                   Job.responsibilities.ilike(like)))

    location = (request.args.get("location") or "").strip()
    if location:
        query = query.filter(Job.location.ilike(f"%{location}%"))

    category = (request.args.get("category") or "").strip()
    if category:
        query = query.filter(Job.category.ilike(f"%{category}%"))

    work_mode = (request.args.get("work_mode") or "").strip()
    if work_mode:
        query = query.filter(Job.work_mode.ilike(f"%{work_mode}%"))

    job_type = (request.args.get("job_type") or "").strip()
    if job_type:
        query = query.filter(Job.job_type.ilike(f"%{job_type}%"))

    exp = (request.args.get("experience") or "").strip().lower()
    if exp in EXPERIENCE_FILTERS:
        lo, hi = EXPERIENCE_FILTERS[exp]
        query = query.filter(Job.experience_min >= lo,
                             Job.experience_max <= hi)

    try:
        min_sal = int(request.args.get("min_salary") or 0)
        max_sal = int(request.args.get("max_salary") or 0)
    except ValueError:
        min_sal = max_sal = 0
    if min_sal > 0:
        query = query.filter(Job.salary_max >= min_sal)
    if max_sal > 0:
        query = query.filter(Job.salary_min <= max_sal)

    return query


@app.route("/api/jobs", methods=["GET"])
def api_jobs():
    """List jobs with search + filters. Adds AI Fit % for logged-in users."""
    user = current_user()
    query = Job.query
    query = filter_jobs(query)
    sort = request.args.get("sort", "").lower()
    jobs_list = query.order_by(Job.id.desc()).all()

    my_skills = user_skills_list(user) if user else []
    results = []
    for job in jobs_list:
        fit, gap = None, None
        if my_skills:
            fit = ml_predict("skill_match_score", my_skills, job.skill_list())
            gap = ml_predict("compute_skill_gap", my_skills, job.skill_list())
        d = job_to_dict(job, fit=fit, gap=gap)
        d["applicants"] = job.applications.count()
        results.append(d)

    if sort == "fit" and results:
        results.sort(key=lambda j: j["ai_fit"] or 0, reverse=True)
    elif sort == "salary":
        results.sort(key=lambda j: j["salary_max"] or 0, reverse=True)

    return jsonify({
        "jobs": results,
        "count": len(results),
        "user_skills": my_skills,
        "disclaimer": DISCLAIMER,
    })


@app.route("/api/jobs/<int:job_id>", methods=["GET"])
def api_job_detail(job_id):
    """Get a single job with AI Fit and skill gap."""
    job = db.session.get(Job, job_id)
    if not job:
        return error_response("Job not found", 404)
    user = current_user()
    fit, gap = None, None
    if user:
        my_skills = user_skills_list(user)
        fit = ml_predict("skill_match_score", my_skills, job.skill_list())
        gap = ml_predict("compute_skill_gap", my_skills, job.skill_list())
    return jsonify(job_to_dict(job, fit=fit, gap=gap,
                               user_skills=user_skills_list(user) if user else []))


@app.route("/api/jobs/<int:job_id>/save", methods=["POST", "DELETE"])
@login_required
def api_job_save(job_id):
    """Save or unsave a job for the logged-in user."""
    job = db.session.get(Job, job_id)
    if not job:
        return error_response("Job not found", 404)
    user = current_user()
    existing = SavedJob.query.filter_by(user_id=user.id, job_id=job.id).first()
    if request.method == "POST":
        if existing:
            return jsonify({"saved": True, "message": "Already saved."})
        db.session.add(SavedJob(user_id=user.id, job_id=job.id))
        add_notification(user.id, f"You saved '{job.title}' at {job.company}.",
                         "job")
        db.session.commit()
        return jsonify({"saved": True, "message": "Job saved."})
    if existing:
        db.session.delete(existing)
        db.session.commit()
    return jsonify({"saved": False, "message": "Job removed from saved list."})


@app.route("/api/jobs/<int:job_id>/apply", methods=["POST"])
@login_required
def api_job_apply(job_id):
    """Submit an application for a job."""
    job = db.session.get(Job, job_id)
    if not job:
        return error_response("Job not found", 404)
    user = current_user()
    if Application.query.filter_by(user_id=user.id, job_id=job.id).first():
        return error_response("You have already applied to this job.", 409)

    data, err = require_json()
    if err:
        return err

    errors = []
    email = str(data.get("email") or "").strip()
    phone = str(data.get("phone") or "").strip()
    tenth = str(data.get("tenth_percent") or "").strip()
    twelfth = str(data.get("twelfth_percent") or "").strip()
    cgpa = str(data.get("cgpa") or "").strip()
    summary = str(data.get("summary") or "").strip()

    if not email or "@" not in email:
        errors.append("A valid email is required.")
    if not phone or not phone.replace("+", "").replace(" ", "").isdigit():
        errors.append("A valid phone number is required.")
    if not tenth or not twelfth:
        errors.append("10th and 12th percentages are required.")
    if not cgpa:
        errors.append("Degree CGPA is required.")
    if len(summary) < 20:
        errors.append("Summary must be at least 20 characters.")
    if errors:
        return error_response("; ".join(errors), 400)

    timeline = [{"status": "Applied",
                 "date": datetime.utcnow().isoformat(timespec="seconds")}]
    appn = Application(
        user_id=user.id, job_id=job.id, email=email, phone=phone,
        tenth_percent=tenth, twelfth_percent=twelfth, cgpa=cgpa,
        summary=summary,
        projects=str(data.get("projects") or ""),
        certificates=str(data.get("certificates") or ""),
        status="Applied", timeline=json.dumps(timeline))
    db.session.add(appn)
    add_notification(user.id,
                     f"Application submitted for {job.title} at {job.company}.",
                     "application")
    db.session.commit()
    return jsonify({"message": "Application submitted successfully.",
                    "application_id": appn.id}), 201


# ---------------------------------------------------------------------------
# REST API - AI matching and ML predictions
# ---------------------------------------------------------------------------
def parse_skill_list(data):
    """Extract a list of skills from a JSON payload."""
    skills = data.get("skills")
    if not skills:
        return None, error_response("'skills' is required (non-empty list).", 400)
    if isinstance(skills, str):
        skills = [s.strip() for s in skills.split(",") if s.strip()]
    if not isinstance(skills, list) or not any(str(s).strip() for s in skills):
        return None, error_response("'skills' must be a non-empty list.", 400)
    return [str(s).strip() for s in skills if str(s).strip()], None


@app.route("/api/match-jobs", methods=["POST"])
def api_match_jobs():
    """Match jobs against a supplied skill list using cosine similarity."""
    data, err = require_json()
    if err:
        return err
    skills, err = parse_skill_list(data)
    if err:
        return err

    results = []
    for job in Job.query.all():
        fit = ml_predict("skill_match_score", skills, job.skill_list())
        gap = ml_predict("compute_skill_gap", skills, job.skill_list())
        results.append(job_to_dict(job, fit=fit, gap=gap))
    results.sort(key=lambda j: j["ai_fit"], reverse=True)
    return jsonify({"skills": skills, "jobs": results[:20],
                    "count": len(results)})


@app.route("/api/predict-role", methods=["POST"])
def api_predict_role():
    """Predict the top 3 job roles for a skill list."""
    data, err = require_json()
    if err:
        return err
    skills, err = parse_skill_list(data)
    if err:
        return err
    try:
        roles = ml_predict("predict_roles", skills)
    except RuntimeError as exc:
        return error_response(str(exc), 503)
    return jsonify({"skills": skills, "top_roles": roles,
                    "synthetic_data": True})


@app.route("/api/predict-wage", methods=["POST"])
def api_predict_wage():
    """Predict a fair daily wage for an informal worker."""
    data, err = require_json()
    if err:
        return err
    trade = str(data.get("trade") or "").strip()
    city_type = str(data.get("city_type") or "").strip()
    experience = data.get("experience")
    errors = []
    if not trade:
        errors.append("'trade' is required.")
    if not city_type:
        errors.append("'city_type' is required.")
    if experience is None or not str(experience).lstrip("-").isdigit():
        errors.append("'experience' must be a whole number.")
    if errors:
        return error_response("; ".join(errors), 400)
    try:
        result = ml_predict("predict_wage", trade, city_type, int(experience))
    except ValueError as exc:
        return error_response(str(exc), 400)
    except RuntimeError as exc:
        return error_response(str(exc), 503)
    result["disclaimer"] = (
        "Minimum wages vary by Indian state, occupation, experience, "
        "employment type and applicable regulations. This is general "
        "guidance, not legal or wage-law advice."
    )
    return jsonify(result)


@app.route("/api/predict-salary", methods=["POST"])
def api_predict_salary():
    """Predict an expected monthly salary for a formal role."""
    data, err = require_json()
    if err:
        return err
    role = str(data.get("role") or "").strip()
    city = str(data.get("city") or "").strip()
    experience = data.get("experience")
    skills = data.get("skills") or []
    errors = []
    if not role:
        errors.append("'role' is required.")
    if not city:
        errors.append("'city' is required.")
    if experience is None or not str(experience).lstrip("-").isdigit():
        errors.append("'experience' must be a whole number.")
    if not isinstance(skills, list):
        errors.append("'skills' must be a list.")
    if errors:
        return error_response("; ".join(errors), 400)
    try:
        result = ml_predict("predict_salary", role, skills,
                            int(experience), city)
    except ValueError as exc:
        return error_response(str(exc), 400)
    except RuntimeError as exc:
        return error_response(str(exc), 503)
    return jsonify(result)


# ---------------------------------------------------------------------------
# REST API - profile, dashboard, notifications
# ---------------------------------------------------------------------------
def profile_strength(user):
    """Compute profile strength % from completed sections (not hard-coded)."""
    sections = {
        "headline": bool(user.profile and user.profile.headline),
        "about": bool(user.profile and user.profile.about),
        "phone": bool(user.profile and user.profile.phone),
        "location": bool(user.profile and user.profile.location),
        "skills": user.user_skills.count() > 0,
        "education": user.education.count() > 0,
        "projects": user.projects.count() > 0,
        "certificates": user.certificates.count() > 0,
        "experience": user.experience.count() > 0,
        "preferred_role": bool(user.profile and user.profile.preferred_role),
        "job_preferences": bool(user.profile and user.profile.job_type
                                and user.profile.work_mode),
        "links": bool(user.profile and user.profile.links),
    }
    filled = sum(1 for v in sections.values() if v)
    return round(filled / len(sections) * 100), sections


@app.route("/api/profile", methods=["GET"])
@login_required
def api_profile_get():
    """Get the logged-in user's profile."""
    user = current_user()
    strength, sections = profile_strength(user)
    links = {}
    if user.profile and user.profile.links:
        try:
            links = json.loads(user.profile.links)
        except json.JSONDecodeError:
            links = {}
    return jsonify({
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "headline": user.profile.headline if user.profile else "",
        "about": user.profile.about if user.profile else "",
        "avatar": (user.profile.avatar if user.profile else None),
        "phone": user.profile.phone if user.profile else "",
        "location": user.profile.location if user.profile else "",
        "preferred_role": user.profile.preferred_role if user.profile else "",
        "job_type": user.profile.job_type if user.profile else "",
        "work_mode": user.profile.work_mode if user.profile else "",
        "preferred_location": user.profile.preferred_location if user.profile else "",
        "expected_salary": user.profile.expected_salary if user.profile else "",
        "links": links,
        "languages": json.loads(user.profile.languages or "[]") if user.profile else [],
        "hobbies": json.loads(user.profile.hobbies or "[]") if user.profile else [],
        "skills": [
            {"id": us.id, "name": us.skill.name, "category": us.skill.category,
             "proficiency": us.proficiency, "years": us.years}
            for us in user.user_skills.all() if us.skill
        ],
        "education": [
            {"id": e.id, "level": e.level, "institution": e.institution,
             "percentage_or_cgpa": e.percentage_or_cgpa, "year": e.year,
             "field_of_study": e.field_of_study}
            for e in user.education.all()
        ],
        "projects": [
            {"id": p.id, "title": p.title, "description": p.description,
             "technologies": p.technologies, "link": p.link}
            for p in user.projects.all()
        ],
        "certificates": [
            {"id": c.id, "title": c.title, "issuer": c.issuer,
             "year": c.year, "link": c.link}
            for c in user.certificates.all()
        ],
        "experience": [
            {"id": x.id, "title": x.title, "company": x.company,
             "start_date": x.start_date, "end_date": x.end_date,
             "description": x.description}
            for x in user.experience.all()
        ],
        "profile_strength": strength,
        "profile_sections": sections,
    })


@app.route("/api/profile", methods=["PUT"])
@login_required
def api_profile_put():
    """Update profile fields."""
    user = current_user()
    data, err = require_json()
    if err:
        return err

    if not user.profile:
        user.profile = Profile(user_id=user.id)

    text_fields = ["headline", "about", "phone", "location",
                   "preferred_role", "job_type", "work_mode",
                   "preferred_location", "expected_salary"]
    for field in text_fields:
        if field in data:
            value = str(data[field]).strip()[:500]
            setattr(user.profile, field, value)

    if "links" in data and isinstance(data["links"], dict):
        user.profile.links = json.dumps(
            {str(k): str(v) for k, v in list(data["links"].items())[:10]})
    if "languages" in data and isinstance(data["languages"], list):
        user.profile.languages = json.dumps(
            [str(x)[:40] for x in data["languages"][:15]])
    if "hobbies" in data and isinstance(data["hobbies"], list):
        user.profile.hobbies = json.dumps(
            [str(x)[:40] for x in data["hobbies"][:15]])

    db.session.commit()
    strength, _ = profile_strength(user)
    return jsonify({"message": "Profile updated.", "profile_strength": strength})


@app.route("/api/profile/skills", methods=["POST"])
@login_required
def api_profile_skills():
    """Add or update a user skill with proficiency."""
    user = current_user()
    data, err = require_json()
    if err:
        return err
    name = str(data.get("name") or "").strip()
    proficiency = str(data.get("proficiency") or "Intermediate").strip()
    if not name:
        return error_response("'name' is required.", 400)
    if proficiency not in ("Beginner", "Intermediate", "Advanced"):
        return error_response(
            "proficiency must be Beginner, Intermediate or Advanced.", 400)

    skill = Skill.query.filter(db.func.lower(Skill.name) == name.lower()).first()
    if not skill:
        skill = Skill(name=name.title(), category="General")
        db.session.add(skill)
        db.session.commit()

    existing = UserSkill.query.filter_by(user_id=user.id,
                                         skill_id=skill.id).first()
    if existing:
        existing.proficiency = proficiency
        try:
            existing.years = float(data.get("years") or existing.years)
        except (TypeError, ValueError):
            pass
    else:
        years = 0.0
        try:
            years = float(data.get("years") or 0)
        except (TypeError, ValueError):
            years = 0.0
        db.session.add(UserSkill(user_id=user.id, skill_id=skill.id,
                                 proficiency=proficiency, years=years))
    db.session.commit()
    return jsonify({"message": "Skill saved.",
                    "skills": user_skills_list(user)})


@app.route("/api/profile/skills/<int:skill_ref_id>", methods=["DELETE"])
@login_required
def api_profile_skill_delete(skill_ref_id):
    """Remove a user skill by user_skills row id."""
    user = current_user()
    row = UserSkill.query.filter_by(id=skill_ref_id, user_id=user.id).first()
    if not row:
        return error_response("Skill not found.", 404)
    db.session.delete(row)
    db.session.commit()
    return jsonify({"message": "Skill removed."})


@app.route("/api/dashboard", methods=["GET"])
@login_required
def api_dashboard():
    """Dashboard summary data for the logged-in user."""
    user = current_user()
    my_skills = user_skills_list(user)

    def application_view(a):
        # Simulate realistic status progression for demo purposes
        stages = ["Applied", "Under Review", "Shortlisted",
                  "Interview Scheduled", "Offer"]
        days = (datetime.utcnow() - a.applied_at).days
        stage_idx = min(days, len(stages) - 1)
        timeline = a.timeline_list()
        current = stages[stage_idx]
        return {
            "id": a.id,
            "job_id": a.job_id,
            "job_title": a.job.title,
            "company": a.job.company,
            "location": a.job.location,
            "is_internship": bool(a.job.is_internship),
            "applied_at": a.applied_at.isoformat(),
            "status": current,
            "timeline": timeline,
            "resume_sent": bool(a.summary),
            "skill_gap": (ml_predict("compute_skill_gap", my_skills,
                                     a.job.skill_list()) if my_skills else []),
            "next_steps": _next_steps(current),
        }

    applications = [application_view(a) for a in
                    user.applications.order_by(Application.applied_at.desc()).all()]
    saved = []
    for sj in user.saved_jobs.order_by(SavedJob.created_at.desc()).all():
        job = sj.job
        fit = (ml_predict("skill_match_score", my_skills, job.skill_list())
               if my_skills else None)
        saved.append(job_to_dict(job, fit=fit))

    strength, sections = profile_strength(user)

    # Skill growth over time: estimate from when skills were added
    # (we use created order as a proxy for a growth curve)
    skill_growth = []
    total_years = sum(us.years or 0 for us in user.user_skills.all())
    for i, us in enumerate(user.user_skills.order_by(UserSkill.id).all(), start=1):
        skill_growth.append({"label": us.skill.name,
                             "value": round(total_years / i + i, 1)})

    # Skills in demand (from all jobs) vs user's skills
    demand = {}
    for job in Job.query.all():
        for s in job.skill_list():
            demand[s] = demand.get(s, 0) + 1
    top_demand = sorted(demand.items(), key=lambda kv: kv[1], reverse=True)[:8]

    # Skills by category for donut chart
    categories = {}
    for us in user.user_skills.all():
        if us.skill:
            cat = us.skill.category or "General"
            categories[cat] = categories.get(cat, 0) + 1

    unread = user.notifications.filter_by(is_read=False).count()

    return jsonify({
        "total_applications": len(applications),
        "jobs_applied": len([a for a in applications if not a["is_internship"]]),
        "internships_applied": len([a for a in applications if a["is_internship"]]),
        "saved_jobs": len(saved),
        "skills_count": len(my_skills),
        "profile_strength": strength,
        "profile_sections": sections,
        "skill_growth": skill_growth,
        "skills_in_demand": [{"skill": k, "count": v} for k, v in top_demand],
        "skills_by_category": categories,
        "applications": applications,
        "saved": saved,
        "my_skills": my_skills,
        "unread_notifications": unread,
        "notifications": [
            {"id": n.id, "message": n.message, "kind": n.kind,
             "is_read": bool(n.is_read),
             "created_at": n.created_at.isoformat()}
            for n in user.notifications.order_by(
                Notification.created_at.desc()).limit(10)
        ],
    })


def _next_steps(status):
    """Suggested next steps per application status."""
    steps = {
        "Applied": ["Follow up with the recruiter in 3-5 days.",
                    "Prepare a tailored resume for similar roles.",
                    "Keep applying to matching jobs."],
        "Under Review": ["Review your skill gap and strengthen weak areas.",
                         "Prepare answers for common interview questions."],
        "Shortlisted": ["Revise your projects and be ready to discuss them.",
                        "Research the company and role."],
        "Interview Scheduled": ["Practice with the Interview Prep tool.",
                                "Prepare questions to ask the interviewer."],
        "Offer": ["Compare the offer with fair wage estimates.",
                  "Negotiate politely with data."],
    }
    return steps.get(status, [])


@app.route("/api/notifications", methods=["GET"])
@login_required
def api_notifications():
    """List recent notifications."""
    user = current_user()
    return jsonify({
        "notifications": [
            {"id": n.id, "message": n.message, "kind": n.kind,
             "is_read": bool(n.is_read),
             "created_at": n.created_at.isoformat()}
            for n in user.notifications.order_by(
                Notification.created_at.desc()).limit(20)
        ],
        "unread": user.notifications.filter_by(is_read=False).count(),
    })


@app.route("/api/notifications/read", methods=["POST"])
@login_required
def api_notifications_read():
    """Mark all notifications as read."""
    user = current_user()
    for n in user.notifications.filter_by(is_read=False):
        n.is_read = True
    db.session.commit()
    return jsonify({"message": "All notifications marked as read."})


# ---------------------------------------------------------------------------
# REST API - resume
# ---------------------------------------------------------------------------
@app.route("/api/resume", methods=["GET"])
@login_required
def api_resume_get():
    """Get the saved resume content."""
    user = current_user()
    resume = user.resumes.order_by(Resume.updated_at.desc()).first()
    data = {}
    if resume and resume.data:
        try:
            data = json.loads(resume.data)
        except json.JSONDecodeError:
            data = {}
    return jsonify(data)


@app.route("/api/resume", methods=["POST", "PUT"])
@login_required
def api_resume_save():
    """Save resume content."""
    user = current_user()
    data, err = require_json()
    if err:
        return err
    if not isinstance(data, dict):
        return error_response("Resume data must be a JSON object.", 400)

    resume = user.resumes.order_by(Resume.updated_at.desc()).first()
    if not resume:
        resume = Resume(user_id=user.id)
        db.session.add(resume)
    resume.data = json.dumps(data)
    db.session.commit()
    return jsonify({"message": "Resume saved.", "sections": len(data)})


# ---------------------------------------------------------------------------
# REST API - roadmaps and interview prep
# ---------------------------------------------------------------------------
import content  # noqa: E402  (import after app setup is fine)


@app.route("/api/roadmap", methods=["POST"])
def api_roadmap():
    """Generate a 5-stage roadmap for a role."""
    data, err = require_json()
    if err:
        return err
    role = str(data.get("role") or "").strip()
    if not role:
        return error_response("'role' is required.", 400)

    template = content.ROADMAPS.get(role)
    source = "template"
    if not template:
        # Custom role: build a generic 5-stage path naming the role
        source = "generic"
        template = [
            dict(stage, skills=[s if s != " basics" else f"{role} basics"
                                for s in stage["skills"]])
            for stage in content.GENERIC_ROADMAP
        ]
        for stage in template:
            if stage["title"] == "Interview Preparation":
                stage["title"] = f"{role} Interview Preparation"

    stages = []
    for i, stage in enumerate(template, start=1):
        stages.append({
            "number": i,
            "title": stage["title"],
            "duration": stage["duration"],
            "skills": stage["skills"],
        })
    return jsonify({"role": role, "stages": stages, "source": source,
                    "total_duration": "approx. 5 months"})


@app.route("/api/interview/questions", methods=["POST"])
def api_interview_questions():
    """Get interview rounds and sample questions for a role."""
    data, err = require_json()
    if err:
        return err
    role = str(data.get("role") or "").strip()
    if not role:
        return error_response("'role' is required.", 400)
    prep = content.INTERVIEW_PREP.get(role)
    if not prep:
        return error_response(
            f"No prep data for '{role}'. Supported roles: "
            f"{', '.join(content.INTERVIEW_PREP)}", 404)
    return jsonify({"role": role, "rounds": prep["rounds"],
                    "questions": prep["questions"]})


@app.route("/api/practice", methods=["POST"])
@login_required
def api_practice():
    """Save an interview practice answer with chatbot feedback."""
    user = current_user()
    data, err = require_json()
    if err:
        return err
    role = str(data.get("role") or "").strip()
    question = str(data.get("question") or "").strip()
    answer = str(data.get("answer") or "").strip()
    if not all([role, question, answer]):
        return error_response("role, question and answer are required.", 400)
    if len(answer) < 10:
        return error_response("Your answer must be at least 10 characters.", 400)

    feedback = _evaluate_answer(answer)
    record = InterviewPractice(user_id=user.id, role=role,
                               question=question, answer=answer,
                               feedback=json.dumps(feedback))
    db.session.add(record)
    db.session.commit()
    return jsonify({"feedback": feedback})


def _evaluate_answer(answer):
    """Rule-based scoring of a practice interview answer."""
    words = answer.split()
    word_count = len(words)
    sentences = max(1, answer.count(".") + answer.count("!") + answer.count("?"))

    scores = {}
    scores["clarity"] = min(100, 40 + word_count)  # longer = more complete
    scores["structure"] = min(100, 30 + sentences * 25)
    relevance_keywords = ["because", "for example", "project", "team",
                          "learned", "result", "goal", "skill", "experience"]
    hits = sum(1 for k in relevance_keywords if k in answer.lower())
    scores["relevance"] = min(100, 30 + hits * 15)

    missing = []
    if word_count < 30:
        missing.append("Add more detail - aim for 30+ words.")
    if "because" not in answer.lower():
        missing.append("Explain WHY with 'because'.")
    if "example" not in answer.lower():
        missing.append("Include a concrete example.")
    if sentences < 2:
        missing.append("Break your answer into short paragraphs.")

    overall = round(sum(scores.values()) / len(scores))
    if not missing:
        missing.append("No major gaps found - keep practising!")
    return {"scores": scores, "overall": overall, "missing_points": missing}


# ---------------------------------------------------------------------------
# REST API - chatbot
# ---------------------------------------------------------------------------
def chatbot_response(message, user=None):
    """Rule-based intent matching with optional external LLM fallback."""
    text = str(message or "").strip().lower()
    if not text:
        return {"reply": "Please type a question first.",
                "intent": "help"}

    # 1. Try offline intents first (works fully offline)
    best_intent = None
    best_hits = 0
    for intent in content.INTENTS:
        hits = sum(1 for p in intent["patterns"] if p in text)
        if hits > best_hits:
            best_hits = hits
            best_intent = intent

    if best_intent and best_hits >= 1:
        reply = random.choice(best_intent["replies"])
        job_count = Job.query.count()
        reply = reply.replace("{job_count}", str(job_count))
        response = {"reply": reply, "intent": best_intent["name"]}
        if best_intent.get("include_roadmap"):
            response["roadmap_role"] = "Data Analyst"
        return response

    # 2. Optional external LLM (only if configured in .env)
    api_key = os.environ.get("LLM_API_KEY", "").strip()
    provider = os.environ.get("LLM_PROVIDER", "").strip().lower()
    if api_key and provider:
        try:
            llm_reply = _call_llm(provider, api_key, message, user)
            if llm_reply:
                return {"reply": llm_reply, "intent": "llm"}
        except Exception as exc:  # noqa: BLE001 - LLM is optional
            print(f"LLM call failed, using fallback: {exc}")

    return {
        "reply": ("I'm not sure about that yet. I can help with jobs, "
                  "resumes, fair wages, roadmaps and interview prep. "
                  "Try one of the quick buttons below."),
        "intent": "fallback",
    }


def _call_llm(provider, api_key, message, user=None):
    """Call an OpenAI-compatible LLM API using only the standard library."""
    base_url = os.environ.get("LLM_BASE_URL",
                              "https://api.openai.com/v1").rstrip("/")
    model = os.environ.get("LLM_MODEL", "gpt-4o-mini")
    system = ("You are WorkWise AI, a helpful career assistant for Indian "
                  "job seekers. Give concise, practical advice. Mention that "
                  "WorkWise uses sample data for demonstration.")
    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": message},
        ],
        "max_tokens": 300,
    }).encode("utf-8")

    req = urllib.request.Request(
        base_url + "/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {api_key}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    return result["choices"][0]["message"]["content"]


@app.route("/api/chat", methods=["POST"])
def api_chat():
    """Chatbot endpoint. Offline rule-based first, optional LLM."""
    data, err = require_json()
    if err:
        return err
    message = str(data.get("message") or "").strip()
    if not message:
        return error_response("'message' is required.", 400)

    # Wage-related questions can be answered with the live model
    reply_data = chatbot_response(message, user=current_user())

    # Detect a direct wage question pattern for an instant estimate
    lower = message.lower()
    if any(w in lower for w in ["wage", "salary for", "earn"]) and \
            any(w in lower for w in ["electrician", "mason", "painter",
                                     "driver", "delivery", "domestic"]):
        for trade in ["Electrician", "Mason", "Painter", "Driver",
                      "Delivery Partner", "Domestic Worker"]:
            if trade.lower() in lower:
                city = "Metro" if "metro" in lower else (
                    "Tier-2" if "tier" in lower or "tier 2" in lower
                    or "tier-2" in lower else "Rural" if "rural" in lower
                    else "Metro")
                try:
                    wage = ml_predict("predict_wage", trade, city, 5)
                    reply_data["reply"] += (
                        f" For example, a {trade} in a {city} with 5 years "
                        f"experience typically earns about "
                        f"₹{wage['predicted_daily_wage']:.0f} per day "
                        f"(range ₹{wage['lower_range']:.0f}-"
                        f"₹{wage['upper_range']:.0f}). Check the Fair Wage "
                        f"page for your exact inputs.")
                except Exception:  # noqa: BLE001 - non-critical enhancement
                    pass
                break

    return jsonify(reply_data)


@app.route("/api/skills", methods=["GET"])
def api_skills():
    """Autocomplete list of canonical skills."""
    q = (request.args.get("q") or "").strip().lower()
    query = Skill.query
    if q:
        query = query.filter(Skill.name.ilike(f"%{q}%"))
    return jsonify({"skills": [s.name for s in query.limit(30).all()]})


@app.route("/api/info", methods=["GET"])
def api_info():
    """General app info for the frontend."""
    return jsonify({
        "app": "WorkWise AI",
        "sdg": "UN SDG 8 - Decent Work and Economic Growth",
        "disclaimer": DISCLAIMER,
        "job_count": Job.query.count(),
        "wage_trades": ["Mason", "Painter", "Electrician",
                        "Domestic Worker", "Driver", "Delivery Partner"],
        "city_types": ["Metro", "Tier-2", "Rural"],
    })


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------
@app.errorhandler(404)
def page_not_found(e):
    if request.path.startswith("/api/"):
        return error_response("Endpoint not found", 404)
    return render_template("404.html", message="Page not found."), 404


@app.errorhandler(400)
def bad_request(e):
    if request.path.startswith("/api/"):
        return error_response("Bad request", 400)
    return render_template("404.html", message="Bad request."), 400


@app.errorhandler(401)
def unauthorized(e):
    if request.path.startswith("/api/"):
        return error_response("Authentication required", 401)
    return redirect(url_for("login"))


@app.errorhandler(403)
def forbidden(e):
    if request.path.startswith("/api/"):
        return error_response("Forbidden", 403)
    return render_template("404.html", message="Access forbidden."), 403


@app.errorhandler(500)
def server_error(e):
    db.session.rollback()
    if request.path.startswith("/api/"):
        return error_response("Internal server error", 500)
    return render_template("404.html",
                           message="Something went wrong. Please try again."), 500


# ---------------------------------------------------------------------------
# CLI: python app.py init-db
# ---------------------------------------------------------------------------
def main():
    """Entry point: optional init-db command, otherwise run the server."""
    if len(sys.argv) > 1 and sys.argv[1] == "init-db":
        seed_database()
        print("Done. Start the app with: python app.py")
        return
    print(SYNTHETIC_WARNING)
    print("WorkWise AI starting on http://127.0.0.1:5000")
    app.run(debug=os.environ.get("FLASK_DEBUG", "0") == "1",
            host="0.0.0.0", port=5000)


if __name__ == "__main__":
    main()
