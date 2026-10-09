# WorkWise AI — Training Data Guide

All datasets in `data/` are **SYTHETIC** (clearly labelled) and created for
demonstration. **Never** present the model outputs as real-world statistics.

> ⚠️ WARNING: Using SYNTHETIC training data. Results are for demonstration
> only and are not real-world salary or employment statistics.

## Files

| File | Columns | Purpose | Rows |
|---|---|---|---|
| `jobs.csv` | `id, title, company, location, job_type, work_mode, category, is_internship, experience_min, experience_max, salary_min, salary_max, salary_period, team_size, duration, description, responsibilities, perks, skills` | Seed DB (24 fictional listings) + demo content | 24 |
| `job_skills_training.csv` | `skills` (semicolon-separated), `role` | Train the **Job Role Classifier** (multi-hot encoding) | 800 |
| `wages.csv` | `trade, city_type, experience, daily_wage` | Train the **Fair Wage Regressor** | 1080 |
| `salaries.csv` | `role, skills, experience, city, salary` | Train the **Job Salary Regressor** | 640 |

## Regenerating the synthetic data

```bash
python data/generate_synthetic_data.py
```

## Where to find real open datasets (to replace synthetic data)

- **Kaggle search suggestions**
  - "job postings dataset", "resume skills dataset",
    "data science job salaries", "india salary dataset"
  - Notable Kaggle datasets (search these titles):
    - *Data Science Job Salaries* (real-world DS/ML salaries)
    - *Jobs Data from LinkedIn / Naukri scrapes* (check licence!)
    - *Skill demand from job postings*
- **Job skills / job description datasets**
  - Kaggle: `job-skills`, `job-descriptions`, `indeed job postings`
  - GitHub: awesome-public-datasets → `business` → employment
- **Indian salary datasets**
  - Kaggle: `India Salary Dataset`, `Salary Prediction` (Glassdoor/AmbitionBox clones)
  - PayScale / Glassdoor public reports (read their terms before scraping)
- **Indian wage datasets (informal workers)**
  - **Official source:** Ministry of Labour & Employment —
    *Minimum Wages* notifications (indiacode.nic.in, labour.gov.in)
  - **ILO** wage statistics, **NSSO** employment surveys (MOSPI)
  - PLFS (Periodic Labour Force Survey) reports

## CSV column requirements (exact)

If you bring your own data, keep these exact headers:

```
job_skills_training.csv → skills, role
wages.csv               → trade, city_type, experience, daily_wage
salaries.csv            → role, skills, experience, city, salary
```

- `skills`: semicolon-separated (`Python;SQL;Excel`)
- `role`: one of the 8 supported roles
- `trade`: Mason | Painter | Electrician | Domestic Worker | Driver | Delivery Partner
- `city_type`: Metro | Tier-2 | Rural
- `experience`: integer years
- `daily_wage` / `salary`: numeric (INR)

After replacing the data, retrain:

```bash
python ml/train_model.py
python app.py init-db
```
