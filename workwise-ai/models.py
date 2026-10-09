"""SQLAlchemy database models for WorkWise AI.

All tables for the application live here. Relationships connect a
User to their Profile, Education, Skills, Applications, SavedJobs,
Notifications, Resume, Projects, Certificates, Experience and
InterviewPractice sessions.

Passwords are stored as Werkzeug password hashes (never plaintext).
"""

from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


class User(db.Model):
    """Registered user (job seeker)."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(30), default="jobseeker")
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    profile = db.relationship("Profile", backref="user", uselist=False,
                              cascade="all, delete-orphan")
    applications = db.relationship("Application", backref="user",
                                   lazy="dynamic",
                                   cascade="all, delete-orphan")
    saved_jobs = db.relationship("SavedJob", backref="user", lazy="dynamic",
                                 cascade="all, delete-orphan")
    notifications = db.relationship("Notification", backref="user",
                                    lazy="dynamic",
                                    cascade="all, delete-orphan")
    user_skills = db.relationship("UserSkill", backref="user", lazy="dynamic",
                                  cascade="all, delete-orphan")
    education = db.relationship("Education", backref="user", lazy="dynamic",
                                cascade="all, delete-orphan")
    projects = db.relationship("Project", backref="user", lazy="dynamic",
                               cascade="all, delete-orphan")
    certificates = db.relationship("Certificate", backref="user",
                                   lazy="dynamic",
                                   cascade="all, delete-orphan")
    experience = db.relationship("Experience", backref="user", lazy="dynamic",
                                 cascade="all, delete-orphan")
    resumes = db.relationship("Resume", backref="user", lazy="dynamic",
                              cascade="all, delete-orphan")
    interview_practices = db.relationship("InterviewPractice", backref="user",
                                          lazy="dynamic",
                                          cascade="all, delete-orphan")

    def set_password(self, password):
        """Hash and store a password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify a password against the stored hash."""
        return check_password_hash(self.password_hash, password)


class Profile(db.Model):
    """Extended profile information for a user."""

    __tablename__ = "profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"),
                        unique=True, nullable=False)
    headline = db.Column(db.String(160))
    about = db.Column(db.Text)
    avatar = db.Column(db.String(255))
    phone = db.Column(db.String(20))
    location = db.Column(db.String(120))
    preferred_role = db.Column(db.String(120))
    job_type = db.Column(db.String(40))
    work_mode = db.Column(db.String(40))
    preferred_location = db.Column(db.String(120))
    expected_salary = db.Column(db.String(40))
    links = db.Column(db.Text)          # JSON string of {label: url}
    languages = db.Column(db.Text)      # JSON string of list
    hobbies = db.Column(db.Text)        # JSON string of list

    def completed_fields(self):
        """Return names of the profile sections that are filled in."""
        filled = []
        for field in ("headline", "about", "phone", "location",
                      "preferred_role", "job_type", "work_mode",
                      "preferred_location", "expected_salary", "links",
                      "languages", "hobbies"):
            if getattr(self, field):
                filled.append(field)
        return filled


class Skill(db.Model):
    """Canonical skill in the platform vocabulary."""

    __tablename__ = "skills"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    category = db.Column(db.String(60), default="General")

    def to_dict(self):
        return {"id": self.id, "name": self.name, "category": self.category}


class UserSkill(db.Model):
    """Skill owned by a user, with self-assessed proficiency."""

    __tablename__ = "user_skills"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey("skills.id"), nullable=False)
    proficiency = db.Column(db.String(20), default="Intermediate")
    years = db.Column(db.Float, default=0.0)

    skill = db.relationship("Skill", backref="user_skills")


class Education(db.Model):
    """An education entry (10th, 12th, degree, etc.)."""

    __tablename__ = "education"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    level = db.Column(db.String(40))          # e.g. "10th", "12th", "Bachelor"
    institution = db.Column(db.String(200))
    percentage_or_cgpa = db.Column(db.String(30))
    year = db.Column(db.String(20))
    field_of_study = db.Column(db.String(120))


class Job(db.Model):
    """A (fictional, sample) job or internship listing."""

    __tablename__ = "jobs"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    company = db.Column(db.String(120), nullable=False)
    location = db.Column(db.String(160))
    job_type = db.Column(db.String(40))       # Full-time / Internship
    work_mode = db.Column(db.String(40))      # On-site / Remote / Hybrid
    category = db.Column(db.String(60))
    is_internship = db.Column(db.Boolean, default=False)
    experience_min = db.Column(db.Integer, default=0)
    experience_max = db.Column(db.Integer, default=0)
    salary_min = db.Column(db.Integer)
    salary_max = db.Column(db.Integer)
    salary_period = db.Column(db.String(20), default="month")
    team_size = db.Column(db.Integer)
    duration = db.Column(db.String(40))
    description = db.Column(db.Text)
    responsibilities = db.Column(db.Text)
    perks = db.Column(db.Text)
    skills = db.Column(db.Text)               # semicolon separated
    is_sample = db.Column(db.Boolean, default=True)

    applications = db.relationship("Application", backref="job",
                                   lazy="dynamic",
                                   cascade="all, delete-orphan")

    def skill_list(self):
        return [s.strip() for s in (self.skills or "").split(";") if s.strip()]

    def salary_text(self):
        if self.salary_min is None:
            return "Not disclosed"
        if self.salary_min == self.salary_max:
            return f"₹{self.salary_min:,} / {self.salary_period}"
        return f"₹{self.salary_min:,} - ₹{self.salary_max:,} / {self.salary_period}"

    def experience_text(self):
        if self.is_internship:
            return self.duration or "Internship"
        if self.experience_min == self.experience_max:
            return f"{self.experience_min} yr"
        return f"{self.experience_min}-{self.experience_max} yrs"


class Application(db.Model):
    """A job application submitted by a user."""

    __tablename__ = "applications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id"), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    tenth_percent = db.Column(db.String(20))
    twelfth_percent = db.Column(db.String(20))
    cgpa = db.Column(db.String(20))
    summary = db.Column(db.Text)
    projects = db.Column(db.Text)
    certificates = db.Column(db.Text)
    status = db.Column(db.String(30), default="Applied")
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    timeline = db.Column(db.Text)  # JSON list of {status, date}

    def timeline_list(self):
        import json
        try:
            return json.loads(self.timeline or "[]")
        except json.JSONDecodeError:
            return []


class SavedJob(db.Model):
    """A job bookmarked by a user."""

    __tablename__ = "saved_jobs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    job = db.relationship("Job", backref="saved_by")

    __table_args__ = (db.UniqueConstraint("user_id", "job_id"),)


class Notification(db.Model):
    """An in-app notification for a user."""

    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    message = db.Column(db.String(300), nullable=False)
    kind = db.Column(db.String(30), default="info")
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Resume(db.Model):
    """Saved resume content (JSON blob) for a user."""

    __tablename__ = "resumes"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    data = db.Column(db.Text)  # JSON string with all resume sections
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow)


class Project(db.Model):
    """A project listed on a user's profile/resume."""

    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(160))
    description = db.Column(db.Text)
    technologies = db.Column(db.String(200))
    link = db.Column(db.String(255))


class Certificate(db.Model):
    """A certificate listed on a user's profile/resume."""

    __tablename__ = "certificates"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(160))
    issuer = db.Column(db.String(120))
    year = db.Column(db.String(20))
    link = db.Column(db.String(255))


class Experience(db.Model):
    """A work/internship experience entry."""

    __tablename__ = "experience"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(120))
    company = db.Column(db.String(120))
    start_date = db.Column(db.String(30))
    end_date = db.Column(db.String(30))
    description = db.Column(db.Text)


class InterviewPractice(db.Model):
    """A saved interview practice Q&A with chatbot feedback."""

    __tablename__ = "interview_practice"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    role = db.Column(db.String(80))
    question = db.Column(db.Text)
    answer = db.Column(db.Text)
    feedback = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
