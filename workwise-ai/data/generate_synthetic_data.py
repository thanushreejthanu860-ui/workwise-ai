"""Generate clearly-labelled SYNTHETIC training datasets for WorkWise AI.

The generated files are stored in ../data/:
  - jobs.csv               : fictional job/internship listings (also used to seed the DB)
  - job_skills_training.csv: skill sets -> job role (for the role classifier)
  - wages.csv              : trade, city type, experience -> daily wage (fair wage regressor)
  - salaries.csv           : role, skills, experience, city -> monthly salary (salary regressor)

All values are synthetic and created for demonstration only.
Run: python data/generate_synthetic_data.py
"""

import csv
import os
import random

random.seed(42)

DATA_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# 1. Fictional job listings (24 sample jobs / internships)
# ---------------------------------------------------------------------------
COMPANIES = [
    "NovaByte Labs", "DataNest Analytics", "CloudOrbit Systems",
    "BrightBridge Technologies", "PixelForge Studio", "GreenGrid Mobility",
    "InsightLoop", "CodeVista", "SkillSpring", "NextWave Digital",
    "QuantLeaf Research", "UrbanPulse Ventures",
]

# (title, category, is_internship, job_type, work_mode, exp_min, exp_max,
#  salary_min, salary_max, salary_period, team_size, duration, location, skills)
JOB_ROWS = [
    ("Data Analyst (Fresher)", "Analytics", False, "Full-time", "On-site", 0, 2, 18000, 32000, "month", 8, "Permanent", "Bengaluru, Karnataka", "Python;SQL;Excel;Power BI"),
    ("Junior Data Scientist", "Analytics", False, "Full-time", "Hybrid", 1, 3, 35000, 55000, "month", 12, "Permanent", "Hyderabad, Telangana", "Python;Machine Learning;Statistics;SQL"),
    ("Data Analyst Intern", "Analytics", True, "Internship", "Remote", 0, 0, 8000, 12000, "month", 5, "6 months", "Pune, Maharashtra", "Excel;SQL;Statistics"),
    ("Software Developer", "Software", False, "Full-time", "On-site", 1, 4, 30000, 60000, "month", 15, "Permanent", "Bengaluru, Karnataka", "Python;Java;Git;SQL"),
    ("Frontend Developer Intern", "Software", True, "Internship", "Remote", 0, 0, 6000, 10000, "month", 6, "3 months", "Remote, India", "HTML;CSS;JavaScript;React"),
    ("Web Developer (PHP)", "Software", False, "Full-time", "Hybrid", 1, 3, 22000, 40000, "month", 10, "Permanent", "Jaipur, Rajasthan", "PHP;MySQL;JavaScript;HTML"),
    ("Digital Marketing Executive", "Marketing", False, "Full-time", "On-site", 0, 2, 15000, 28000, "month", 7, "Permanent", "Mumbai, Maharashtra", "SEO;Social Media;Google Analytics"),
    ("Marketing Intern", "Marketing", True, "Internship", "Remote", 0, 0, 5000, 9000, "month", 4, "4 months", "Remote, India", "Social Media;Content Writing;SEO"),
    ("HR Recruiter", "HR", False, "Full-time", "On-site", 1, 3, 18000, 30000, "month", 6, "Permanent", "Chennai, Tamil Nadu", "Recruitment;Communication;HR Policies"),
    ("HR Intern", "HR", True, "Internship", "Hybrid", 0, 0, 5000, 8000, "month", 5, "3 months", "Kochi, Kerala", "Communication;Recruitment;MS Office"),
    ("Sales Executive", "Sales", False, "Full-time", "On-site", 0, 2, 14000, 26000, "month", 9, "Permanent", "Lucknow, Uttar Pradesh", "Sales;Communication;Negotiation"),
    ("Business Development Intern", "Sales", True, "Internship", "Remote", 0, 0, 6000, 10000, "month", 6, "6 months", "Remote, India", "Sales;Communication;Excel"),
    ("Business Analyst", "Analytics", False, "Full-time", "Hybrid", 1, 4, 30000, 50000, "month", 11, "Permanent", "Bengaluru, Karnataka", "SQL;Excel;Power BI;Communication"),
    ("Python Developer Intern", "Software", True, "Internship", "Remote", 0, 1, 7000, 12000, "month", 7, "6 months", "Remote, India", "Python;Django;Git"),
    ("Machine Learning Engineer", "Analytics", False, "Full-time", "Remote", 2, 5, 55000, 90000, "month", 14, "Permanent", "Remote, India", "Python;Machine Learning;Deep Learning;SQL"),
    ("Power BI Developer", "Analytics", False, "Full-time", "On-site", 1, 3, 25000, 42000, "month", 8, "Permanent", "Delhi, Delhi", "Power BI;SQL;Excel;DAX"),
    ("Social Media Manager", "Marketing", False, "Full-time", "Remote", 1, 3, 20000, 35000, "month", 6, "Permanent", "Remote, India", "Social Media;Content Writing;Canva"),
    ("Full Stack Developer", "Software", False, "Full-time", "Hybrid", 2, 5, 45000, 80000, "month", 16, "Permanent", "Bengaluru, Karnataka", "JavaScript;React;Node.js;MongoDB"),
    ("Customer Support Executive", "Sales", False, "Full-time", "On-site", 0, 1, 12000, 20000, "month", 12, "Permanent", "Kolkata, West Bengal", "Communication;MS Office;Problem Solving"),
    ("Data Engineering Intern", "Analytics", True, "Internship", "Remote", 0, 1, 8000, 13000, "month", 6, "6 months", "Remote, India", "Python;SQL;ETL;Cloud"),
    ("UI/UX Design Intern", "Software", True, "Internship", "Hybrid", 0, 0, 6000, 10000, "month", 5, "4 months", "Pune, Maharashtra", "Figma;Design Thinking;HTML;CSS"),
    ("Recruitment Lead", "HR", False, "Full-time", "On-site", 3, 6, 40000, 65000, "month", 10, "Permanent", "Mumbai, Maharashtra", "Recruitment;Leadership;HR Policies"),
    ("Operations Executive", "Sales", False, "Full-time", "On-site", 0, 2, 15000, 25000, "month", 8, "Permanent", "Ahmedabad, Gujarat", "Excel;Communication;Logistics"),
    ("Analytics Intern (Fresher)", "Analytics", True, "Internship", "On-site", 0, 0, 6000, 10000, "month", 6, "3 months", "Chennai, Tamil Nadu", "Excel;Statistics;SQL"),
]

JOBS_HEADER = [
    "id", "title", "company", "location", "job_type", "work_mode", "category",
    "is_internship", "experience_min", "experience_max", "salary_min", "salary_max",
    "salary_period", "team_size", "duration", "description", "responsibilities",
    "perks", "skills",
]


def build_jobs():
    rows = []
    # Demo keywords so the home-page category chips (MNC, Startup,
    # Engineering) return matching listings in text search
    demo_keywords = ["MNC", "Startup", "Engineering"]
    for i, (title, category, is_int, jtype, wmode, emin, emax, smin, smax,
            period, team, duration, loc, skills) in enumerate(JOB_ROWS, start=1):
        company = COMPANIES[(i - 1) % len(COMPANIES)]
        keyword = demo_keywords[(i - 1) % len(demo_keywords)]
        description = (
            f"SAMPLE DATA - Fictional listing. {company} is hiring a {title} to support "
            f"day-to-day deliverables in the {category.lower()} function. "
            f"This is a {keyword} opportunity. This listing is "
            f"created for demonstration purposes only and is not a real opening."
        )
        responsibilities = (
            "Work on assigned team projects; document daily progress; collaborate with "
            "mentors and peers; present weekly updates; learn domain tools and processes."
        )
        perks = "Certificate of completion; flexible hours; mentorship; learning resources; SAMPLE perk."
        rows.append({
            "id": i, "title": title, "company": company, "location": loc,
            "job_type": jtype, "work_mode": wmode, "category": category,
            "is_internship": int(is_int), "experience_min": emin, "experience_max": emax,
            "salary_min": smin, "salary_max": smax, "salary_period": period,
            "team_size": team, "duration": duration, "description": description,
            "responsibilities": responsibilities, "perks": perks, "skills": skills,
        })
    return rows


# ---------------------------------------------------------------------------
# 2. Role classifier training data (skills -> role)
# ---------------------------------------------------------------------------
ROLE_SKILLS = {
    "Data Analyst": ["Excel", "SQL", "Python", "Power BI", "Statistics", "Tableau", "Data Visualization", "DAX", "R"],
    "Data Scientist": ["Python", "Machine Learning", "Statistics", "Pandas", "NumPy", "Deep Learning", "SQL", "NLP", "TensorFlow"],
    "Software Developer": ["Python", "Java", "Git", "SQL", "Data Structures", "Algorithms", "C++", "Spring", "Testing"],
    "Web Developer": ["HTML", "CSS", "JavaScript", "React", "Node.js", "PHP", "MySQL", "MongoDB", "Git"],
    "Digital Marketing Specialist": ["SEO", "Social Media", "Google Analytics", "Content Writing", "PPC", "Email Marketing", "Canva", "SEM"],
    "HR Specialist": ["Recruitment", "Communication", "HR Policies", "Payroll", "Employee Relations", "MS Office", "Onboarding", "Training"],
    "Sales Executive": ["Sales", "Communication", "Negotiation", "CRM", "Lead Generation", "Excel", "Customer Service", "Presentation"],
    "Business Analyst": ["SQL", "Excel", "Power BI", "Communication", "Requirements Gathering", "Process Mapping", "Python", "Documentation"],
}


def build_skill_training():
    """Create ~800 synthetic skill-set / role rows with realistic overlap."""
    rows = []
    roles = list(ROLE_SKILLS.keys())
    for role in roles:
        core = ROLE_SKILLS[role]
        for _ in range(100):
            # Always include 3-6 core skills of the role
            n_core = random.randint(3, min(6, len(core)))
            chosen = random.sample(core, n_core)
            # Sometimes sprinkle in 0-2 skills from other roles (realistic overlap)
            other = [s for r in roles if r != role for s in ROLE_SKILLS[r]]
            if random.random() < 0.6:
                chosen += random.sample(other, random.randint(0, 2))
            random.shuffle(chosen)
            rows.append({"skills": ";".join(chosen), "role": role})
    random.shuffle(rows)
    return rows


# ---------------------------------------------------------------------------
# 3. Fair wage training data (informal workers, synthetic)
# ---------------------------------------------------------------------------
TRADES = {
    "Mason":            {"Metro": 1000, "Tier-2": 650, "Rural": 380},
    "Painter":          {"Metro": 900,  "Tier-2": 600, "Rural": 350},
    "Electrician":      {"Metro": 1050, "Tier-2": 700, "Rural": 400},
    "Domestic Worker":  {"Metro": 700,  "Tier-2": 500, "Rural": 300},
    "Driver":           {"Metro": 1100, "Tier-2": 750, "Rural": 450},
    "Delivery Partner": {"Metro": 950,  "Tier-2": 650, "Rural": 380},
}
CITY_TYPES = ["Metro", "Tier-2", "Rural"]


def build_wages():
    rows = []
    for trade, cities in TRADES.items():
        for city in CITY_TYPES:
            base = cities[city]
            for _ in range(60):
                exp = random.randint(0, 20)
                # Wage grows with experience, with diminishing returns and noise
                wage = base + exp * (base * 0.022) + random.gauss(0, base * 0.06)
                wage = max(200, round(wage))
                rows.append({"trade": trade, "city_type": city,
                             "experience": exp, "daily_wage": wage})
    random.shuffle(rows)
    return rows


# ---------------------------------------------------------------------------
# 4. Job salary training data (formal roles, synthetic)
# ---------------------------------------------------------------------------
ROLE_BASE_SALARY = {  # monthly INR (LPA-ish ranges), synthetic
    "Data Analyst": 24000, "Data Scientist": 42000, "Software Developer": 34000,
    "Web Developer": 24000, "Digital Marketing Specialist": 20000,
    "HR Specialist": 18000, "Sales Executive": 16000, "Business Analyst": 30000,
}
CITY_MULTIPLIER = {"Metro": 1.35, "Tier-2": 1.0, "Rural": 0.72}


def build_salaries():
    rows = []
    for role, base in ROLE_BASE_SALARY.items():
        core = ROLE_SKILLS[role]
        for _ in range(80):
            exp = random.randint(0, 12)
            city = random.choice(CITY_TYPES)
            n_skills = random.randint(2, 5)
            skills = ";".join(random.sample(core, min(n_skills, len(core))))
            skill_bonus = 1 + 0.04 * n_skills
            salary = base * CITY_MULTIPLIER[city] * (1 + exp * 0.055) * skill_bonus
            salary = max(10000, round(salary + random.gauss(0, base * 0.08)))
            rows.append({"role": role, "skills": skills, "experience": exp,
                         "city": city, "salary": salary})
    random.shuffle(rows)
    return rows


def write_csv(filename, header, rows):
    path = os.path.join(DATA_DIR, filename)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Created {path} ({len(rows)} rows)")


def main():
    print("WARNING: Generating SYNTHETIC training data. Results are for "
          "demonstration only and are not real-world salary or employment statistics.")
    write_csv("jobs.csv", JOBS_HEADER, build_jobs())
    write_csv("job_skills_training.csv", ["skills", "role"], build_skill_training())
    write_csv("wages.csv", ["trade", "city_type", "experience", "daily_wage"], build_wages())
    write_csv("salaries.csv", ["role", "skills", "experience", "city", "salary"], build_salaries())
    print("Synthetic dataset generation complete.")


if __name__ == "__main__":
    main()
