"""Static educational content for WorkWise AI.

Contains career roadmap templates, interview preparation material
and rule-based chatbot responses. All content is original and
written for demonstration/learning purposes.
"""

# ---------------------------------------------------------------------------
# Career roadmaps: 5 numbered stages, each with duration and skills
# ---------------------------------------------------------------------------
ROADMAPS = {
    "Data Analyst": [
        {"title": "Excel + Statistics Foundations", "duration": "4 weeks",
         "skills": ["Excel", "Statistics", "Math"]},
        {"title": "SQL for Data Analysis", "duration": "4 weeks",
         "skills": ["SQL", "Databases"]},
        {"title": "Python + Pandas", "duration": "5 weeks",
         "skills": ["Python", "Pandas", "NumPy"]},
        {"title": "Data Visualization (Power BI / Tableau)", "duration": "4 weeks",
         "skills": ["Power BI", "Tableau", "Data Visualization"]},
        {"title": "Projects + Interview Preparation", "duration": "4 weeks",
         "skills": ["Projects", "Communication", "Portfolio"]},
    ],
    "Data Scientist": [
        {"title": "Math + Statistics Refresher", "duration": "4 weeks",
         "skills": ["Statistics", "Math", "Probability"]},
        {"title": "Python for Data Science", "duration": "5 weeks",
         "skills": ["Python", "Pandas", "NumPy"]},
        {"title": "Machine Learning Fundamentals", "duration": "6 weeks",
         "skills": ["Machine Learning", "Scikit-learn", "Statistics"]},
        {"title": "SQL + Data Wrangling", "duration": "4 weeks",
         "skills": ["SQL", "Data Cleaning", "ETL"]},
        {"title": "Capstone Projects + Interviews", "duration": "5 weeks",
         "skills": ["Deep Learning", "Projects", "Communication"]},
    ],
    "Software Developer": [
        {"title": "Programming Fundamentals", "duration": "5 weeks",
         "skills": ["Python", "Data Structures", "Algorithms"]},
        {"title": "Object-Oriented Programming", "duration": "4 weeks",
         "skills": ["Java", "C++", "OOP"]},
        {"title": "Databases + Git", "duration": "4 weeks",
         "skills": ["SQL", "Git", "Databases"]},
        {"title": "Building a Full Project", "duration": "6 weeks",
         "skills": ["Testing", "Frameworks", "Debugging"]},
        {"title": "DSA Practice + Interviews", "duration": "5 weeks",
         "skills": ["Algorithms", "Problem Solving", "Communication"]},
    ],
    "Web Developer": [
        {"title": "HTML, CSS + JavaScript Basics", "duration": "4 weeks",
         "skills": ["HTML", "CSS", "JavaScript"]},
        {"title": "Responsive Design + Git", "duration": "3 weeks",
         "skills": ["CSS", "Git", "Responsive Design"]},
        {"title": "Frontend Framework (React)", "duration": "5 weeks",
         "skills": ["React", "JavaScript", "APIs"]},
        {"title": "Backend Basics (Node.js / PHP)", "duration": "5 weeks",
         "skills": ["Node.js", "PHP", "MySQL"]},
        {"title": "Portfolio Projects + Interviews", "duration": "4 weeks",
         "skills": ["MongoDB", "Projects", "Communication"]},
    ],
    "Digital Marketing Specialist": [
        {"title": "Marketing Foundations", "duration": "3 weeks",
         "skills": ["Marketing", "Communication", "Writing"]},
        {"title": "SEO + Content Writing", "duration": "4 weeks",
         "skills": ["SEO", "Content Writing"]},
        {"title": "Social Media Marketing", "duration": "4 weeks",
         "skills": ["Social Media", "Canva", "Copywriting"]},
        {"title": "Analytics + Paid Ads", "duration": "4 weeks",
         "skills": ["Google Analytics", "PPC", "SEM"]},
        {"title": "Live Campaigns + Interviews", "duration": "3 weeks",
         "skills": ["Email Marketing", "Projects", "Communication"]},
    ],
    "HR Specialist": [
        {"title": "HR Fundamentals", "duration": "3 weeks",
         "skills": ["HR Policies", "Communication"]},
        {"title": "Recruitment + Sourcing", "duration": "4 weeks",
         "skills": ["Recruitment", "Screening", "Interviewing"]},
        {"title": "Payroll + Compliance", "duration": "4 weeks",
         "skills": ["Payroll", "Labour Laws", "MS Office"]},
        {"title": "Employee Relations", "duration": "3 weeks",
         "skills": ["Employee Relations", "Onboarding", "Training"]},
        {"title": "HR Projects + Interviews", "duration": "3 weeks",
         "skills": ["Documentation", "Projects", "Communication"]},
    ],
    "Sales Executive": [
        {"title": "Sales Fundamentals", "duration": "3 weeks",
         "skills": ["Sales", "Communication"]},
        {"title": "Customer Understanding", "duration": "3 weeks",
         "skills": ["Customer Service", "Negotiation"]},
        {"title": "CRM + Pipeline Management", "duration": "4 weeks",
         "skills": ["CRM", "Excel", "Lead Generation"]},
        {"title": "Pitching + Objection Handling", "duration": "4 weeks",
         "skills": ["Presentation", "Negotiation", "Persuasion"]},
        {"title": "Live Sales Practice", "duration": "3 weeks",
         "skills": ["Closing", "Networking", "Communication"]},
    ],
    "Business Analyst": [
        {"title": "Business + Excel Foundations", "duration": "4 weeks",
         "skills": ["Excel", "Business Analysis", "Math"]},
        {"title": "SQL + Data Analysis", "duration": "4 weeks",
         "skills": ["SQL", "Data Analysis"]},
        {"title": "Requirements + Process Mapping", "duration": "4 weeks",
         "skills": ["Requirements Gathering", "Process Mapping", "Documentation"]},
        {"title": "Visualization (Power BI)", "duration": "4 weeks",
         "skills": ["Power BI", "Data Visualization"]},
        {"title": "Case Studies + Interviews", "duration": "3 weeks",
         "skills": ["Communication", "Problem Solving", "Projects"]},
    ],
}

GENERIC_ROADMAP = [
    {"title": "Learn the Fundamentals", "duration": "4 weeks",
     "skills": [" basics", "Communication", "Math"]},
    {"title": "Core Tools + Techniques", "duration": "4 weeks",
     "skills": ["MS Office", "Research", "Documentation"]},
    {"title": "Hands-on Practice", "duration": "5 weeks",
     "skills": ["Projects", "Problem Solving"]},
    {"title": "Build a Portfolio", "duration": "4 weeks",
     "skills": ["Portfolio", "GitHub", "Presentation"]},
    {"title": "Interview Preparation", "duration": "3 weeks",
     "skills": ["Mock Interviews", "Communication", "Aptitude"]},
]

# ---------------------------------------------------------------------------
# Interview preparation: rounds, 6 questions each with why + sample answer
# ---------------------------------------------------------------------------
def _q(q, why, ans):
    return {"question": q, "why": why, "sample_answer": ans}


INTERVIEW_PREP = {
    "Data Analyst": {
        "rounds": ["Aptitude + SQL Online Test", "Technical Interview",
                   "HR / Fit Interview"],
        "questions": [
            _q("Explain the difference between INNER JOIN and LEFT JOIN.",
               "Tests core SQL knowledge used in every analyst role.",
               "An INNER JOIN returns only matching rows from both tables. "
               "A LEFT JOIN returns all rows from the left table plus matches "
               "from the right table, with NULLs where there is no match."),
            _q("How do you handle missing values in a dataset?",
               "Real datasets are messy; analysts must clean data.",
               "First I check how much data is missing and why. For small "
               "gaps I impute with mean/median or forward-fill; for large "
               "gaps I drop the column or flag it for the stakeholder."),
            _q("What is the difference between mean and median?",
               "Checks basic statistical literacy.",
               "The mean is the arithmetic average and is affected by "
               "outliers. The median is the middle value and is robust to "
               "outliers, so I prefer it for skewed data like salaries."),
            _q("How would you find duplicate records in SQL?",
               "Data quality is a daily analyst task.",
               "I use GROUP BY on the key columns with HAVING COUNT(*) > 1 "
               "to find duplicates, or ROW_NUMBER() OVER (PARTITION BY ...) "
               "to identify and remove them."),
            _q("Explain a pivot table and when you would use one.",
               "Excel skills are still essential for analysts.",
               "A pivot table aggregates data by categories — for example "
               "total sales by region and month. I use it for quick "
               "exploration before building dashboards."),
            _q("How do you decide which chart to use?",
               "Visualization choice affects decisions.",
               "I match the chart to the question: trend over time → line "
               "chart, comparison → bar chart, part-to-whole → stacked bar "
               "or pie (sparingly), relationship → scatter plot."),
        ],
    },
    "Data Scientist": {
        "rounds": ["Online Coding + Statistics Test", "ML Technical Interview",
                   "Case Study", "HR Round"],
        "questions": [
            _q("Explain bias-variance tradeoff.",
               "Core ML concept that guides model selection.",
               "Bias is error from oversimplified assumptions; variance is "
               "error from sensitivity to training data. Simple models have "
               "high bias, complex ones high variance. Regularization and "
               "cross-validation help balance them."),
            _q("How do you evaluate a classification model?",
               "Evaluation is central to every ML project.",
               "I use accuracy for balanced data, and precision, recall and "
               "F1 for imbalanced data. I also look at the ROC-AUC curve "
               "and confusion matrix to understand error types."),
            _q("What is overfitting and how do you prevent it?",
               "A common real-world failure mode.",
               "Overfitting means the model memorizes training noise. I "
               "prevent it with train/test splits, cross-validation, "
               "regularization, pruning, and simpler models."),
            _q("Explain how a Random Forest works.",
               "Tests understanding of ensemble methods.",
               "A Random Forest trains many decision trees on random "
               "subsets of data and features, then averages (or votes) "
               "their predictions, which reduces variance and overfitting."),
            _q("How do you handle imbalanced datasets?",
               "Very common in fraud, churn and medical data.",
               "I use class weights, SMOTE or undersampling, choose "
               "precision/recall over accuracy, and validate with "
               "stratified splits and PR curves."),
            _q("Describe a project where you deployed a model.",
               "Checks end-to-end experience.",
               "In my capstone I trained a churn predictor, wrapped it in a "
               "Flask API, and deployed it with Docker so the business team "
               "could score new customers daily."),
        ],
    },
    "Software Developer": {
        "rounds": ["Aptitude + Coding Test", "DSA Interview",
                   "System Design (Fresher: Basics)", "HR Round"],
        "questions": [
            _q("Reverse a linked list. Explain your approach.",
               "Classic DSA question for developers.",
               "I iterate with three pointers: previous, current, next. "
               "At each step I point current.next to previous, then move "
               "all three forward. Time O(n), space O(1)."),
            _q("What is the difference between a stack and a queue?",
               "Fundamental data structures.",
               "A stack is LIFO (last in, first out) — used for undo and "
               "recursion. A queue is FIFO (first in, first out) — used for "
               "task scheduling and BFS."),
            _q("Explain time complexity of binary search.",
               "Tests algorithmic thinking.",
               "Binary search halves the search space each step, so it runs "
               "in O(log n) time on sorted data, compared to O(n) for a "
               "linear scan."),
            _q("What is the difference between SQL and NoSQL databases?",
               "Backend fundamentals.",
               "SQL databases are relational with fixed schemas and ACID "
               "guarantees. NoSQL databases are flexible (document, key-"
               "value) and scale horizontally for high-volume use cases."),
            _q("How does version control with Git help a team?",
               "Every developer uses Git daily.",
               "Git tracks history, lets developers branch and merge "
               "safely, review code with pull requests, and roll back "
               "mistakes without losing work."),
            _q("Explain OOP concepts: encapsulation, inheritance, polymorphism.",
               "Core language design knowledge.",
               "Encapsulation hides internal state behind methods. "
               "Inheritance lets classes reuse behaviour. Polymorphism lets "
               "one interface work with many underlying forms, e.g. method "
               "overriding."),
        ],
    },
    "Web Developer": {
        "rounds": ["Online Coding Test", "Frontend/Backend Technical",
                   "Project Discussion", "HR Round"],
        "questions": [
            _q("Explain the box model in CSS.",
               "Fundamental CSS layout concept.",
               "Every element has content, padding, border and margin. "
               "With box-sizing: border-box, width includes padding and "
               "border, which makes layouts easier to reason about."),
            _q("What is the difference between == and === in JavaScript?",
               "Common JS gotcha.",
               "== coerces types before comparing, so '5' == 5 is true. "
               "=== checks type and value, so '5' === 5 is false. I "
               "recommend === to avoid surprises."),
            _q("How does the DOM work?",
               "Core frontend concept.",
               "The browser parses HTML into a Document Object Model tree. "
               "JavaScript can query and update DOM nodes, and changes "
               "re-render on the page. Frameworks like React use a virtual "
               "DOM for efficient updates."),
            _q("What is an API and how do you call one?",
               "Modern web apps are API-driven.",
               "An API is a contract between client and server. In the "
               "browser I use fetch('url') with async/await, handle errors, "
               "and render the JSON response."),
            _q("How do you make a website responsive?",
               "Mobile traffic dominates.",
               "I use fluid grids, flexible images, and media queries with "
               "breakpoints for mobile, tablet and desktop. Flexbox and "
               "CSS Grid handle most layouts."),
            _q("Explain HTTP methods GET vs POST.",
               "Web fundamentals.",
               "GET requests data and is visible in the URL; POST submits "
               "data (like a form) in the request body and should not be "
               "cached or bookmarked."),
        ],
    },
    "Digital Marketing Specialist": {
        "rounds": ["Aptitude Test", "Marketing Knowledge Interview",
                   "Portfolio Review", "HR Round"],
        "questions": [
            _q("What is SEO and how do you improve it?",
               "Core digital marketing skill.",
               "SEO is ranking higher in search engines. I improve it with "
               "keyword research, quality content, meta tags, fast page "
               "speed, mobile-friendliness and good backlinks."),
            _q("How do you measure campaign success?",
               "Marketing must be measurable.",
               "I track KPIs like CTR, conversion rate, CPA and ROI in "
               "Google Analytics and platform dashboards, then A/B test "
               "creatives and audiences."),
            _q("What is the difference between organic and paid social?",
               "Basic channel knowledge.",
               "Organic reach is free but slow and limited; paid social "
               "gives targeted reach quickly. A healthy strategy combines "
               "both."),
            _q("How do you choose marketing channels?",
               "Strategic thinking.",
               "I match channels to where the target audience spends time "
               "and to the budget — for example LinkedIn for B2B, Instagram "
               "for Gen-Z consumers."),
            _q("Explain A/B testing.",
               "Experimentation is key in growth marketing.",
               "A/B testing shows two variants to similar audiences and "
               "measures which performs better on a goal, so decisions are "
               "data-driven instead of guesswork."),
            _q("How do you write a good social media post?",
               "Everyday execution skill.",
               "I keep it short, lead with value or a hook, add a clear "
               "call to action, relevant hashtags and a strong visual, then "
               "post at peak engagement times."),
        ],
    },
    "HR Specialist": {
        "rounds": ["Aptitude Test", "HR Knowledge Interview",
                   "Situational Judgment Round", "HR Final"],
        "questions": [
            _q("What is the full recruitment lifecycle?",
               "Core HR process knowledge.",
               "It runs from manpower planning, job posting and sourcing, "
               "through screening and interviews, to offers, onboarding and "
               "follow-up during the probation period."),
            _q("How do you handle an employee grievance?",
               "Tests employee relations skills.",
               "I listen empathetically, document the issue, follow company "
               "policy and law, involve the right stakeholders, and close "
               "the loop with the employee."),
            _q("Why is confidentiality important in HR?",
               "HR handles sensitive data.",
               "HR manages salaries, performance and personal data. "
               "Breaching trust harms employees and exposes the company to "
               "legal risk, so access is limited on a need-to-know basis."),
            _q("What are KPIs in HR?",
               "Measuring HR effectiveness.",
               "Common KPIs are time-to-hire, cost-per-hire, attrition rate, "
               "employee engagement scores and training hours per employee."),
            _q("How do you onboard a new joiner?",
               "Day-one experience matters.",
               "I prepare documents and access before day one, run an "
               "orientation, assign a buddy, clarify goals for the first 30 "
               "days and schedule check-ins."),
            _q("How do you stay updated on labour law changes?",
               "Compliance awareness.",
               "I follow official government portals, industry newsletters "
               "and HR forums, and verify changes with legal counsel before "
               "updating policies."),
        ],
    },
    "Sales Executive": {
        "rounds": ["Aptitude + Communication Test", "Sales Role Play",
                   "Product Knowledge Interview", "HR Round"],
        "questions": [
            _q("How do you handle a customer who says the price is too high?",
               "Classic objection-handling test.",
               "I acknowledge the concern, explore what they value, "
               "re-frame around ROI and results, and offer options instead "
               "of immediately discounting."),
            _q("Describe your ideal sales process.",
               "Checks process discipline.",
               "Prospect and qualify, discover needs, present the solution, "
               "handle objections, close, and follow up for referrals and "
               "repeat business."),
            _q("How do you generate leads?",
               "Pipeline building.",
               "I mix outbound calling and emails, referrals, social "
               "selling on LinkedIn, events and content, then qualify with "
               "BANT (budget, authority, need, timeline)."),
            _q("What motivates you in sales?",
               "Understanding drive and resilience.",
               "I am motivated by solving customer problems and hitting "
               "targets. I track my pipeline weekly and treat rejections as "
               "feedback that improves the next pitch."),
            _q("How do you manage your sales pipeline?",
               "CRM discipline.",
               "I keep every lead in a CRM with stage, next action and date, "
               "prioritise hot leads, and review conversion rates weekly to "
               "fix bottlenecks."),
            _q("Sell me this pen (role play).",
               "Classic live selling test.",
               "I ask about their current habits, uncover the pain (losing "
               "notes, signing on the go), then connect the pen's reliability "
               "to that need and ask for a trial commitment."),
        ],
    },
    "Business Analyst": {
        "rounds": ["Aptitude + Excel Test", "Case Study Interview",
                   "Technical (SQL) Round", "HR Round"],
        "questions": [
            _q("How do you gather requirements from stakeholders?",
               "Core BA skill.",
               "I run structured interviews and workshops, ask open "
               "questions, document requirements, and validate them with "
               "sign-offs so everyone agrees before build starts."),
            _q("What is a use case diagram?",
               "Modelling knowledge.",
               "A use case diagram shows actors and the actions they perform "
               "with the system. It helps stakeholders align on scope early "
               "without diving into technical detail."),
            _q("How would you analyse a drop in revenue?",
               "Analytical case framing.",
               "I break revenue into price × volume × mix, segment by "
               "region/product/channel, compare against last period, and "
               "hypothesise causes before proposing fixes."),
            _q("Explain SQL joins you used in a project.",
               "Practical SQL for BAs.",
               "In a sales report I joined orders to customers with a LEFT "
               "JOIN to keep orders without a linked customer, and to a "
               "products table to enrich category-level analysis."),
            _q("What is the difference between a report and a dashboard?",
               "Delivery format knowledge.",
               "A report is a static snapshot for a point in time; a "
               "dashboard is interactive, shows live KPIs and lets users "
               "filter and drill down."),
            _q("How do you handle changing requirements?",
               "Real-world agility.",
               "I log the change, assess impact on scope, timeline and "
               "cost, get stakeholder approval, version the requirements, "
               "and re-baseline the plan."),
        ],
    },
}

# ---------------------------------------------------------------------------
# Rule-based chatbot intents (offline fallback)
# ---------------------------------------------------------------------------
INTENTS = [
    {
        "name": "jobs",
        "patterns": ["job", "hiring", "openings", "vacancy", "work",
                     "internship", "intern", "apply"],
        "replies": [
            "You can explore {job_count} sample jobs and internships on our "
            "Jobs page. Use the search bar and filters for location, "
            "experience, category and salary.",
            "All listings on WorkWise AI are SAMPLE DATA for demonstration. "
            "Browse Jobs to see roles like Data Analyst, Web Developer and "
            "Digital Marketing Executive.",
        ],
    },
    {
        "name": "resume",
        "patterns": ["resume", "cv", "build resume", "download resume"],
        "replies": [
            "Open the Resume Builder to create a professional resume. Fill "
            "your education, skills, projects and certificates, preview it "
            "live, then download via Print (PDF) or the Word (.doc) button.",
        ],
    },
    {
        "name": "wage",
        "patterns": ["wage", "salary", "pay", "earn", "daily wage",
                     "fair wage", "income"],
        "replies": [
            "The Fair Wage tool estimates a typical daily wage for masons, "
            "painters, electricians, domestic workers, drivers and delivery "
            "partners based on city type and experience. Minimum wages vary "
            "by state, so treat it as general guidance, not legal advice.",
        ],
    },
    {
        "name": "roadmap",
        "patterns": ["roadmap", "career path", "learning path", "plan",
                     "road map", "how to become"],
        "replies": [
            "Pick a role on the Roadmaps page (or type your own) and I will "
            "generate a 5-stage learning roadmap with skills to learn, "
            "durations, and a JOB-READY finish line. You can download it as "
            "an image.",
        ],
        "include_roadmap": True,
    },
    {
        "name": "interview",
        "patterns": ["interview", "questions", "prepare", "practice",
                     "interview questions"],
        "replies": [
            "The Interview Prep page covers Data Analyst, Data Scientist, "
            "Software Developer, Web Developer, Digital Marketing, HR, Sales "
            "and Business Analyst — with rounds, 6 sample questions, sample "
            "answers and a practice box.",
        ],
    },
    {
        "name": "profile",
        "patterns": ["profile", "account", "signup", "register", "login"],
        "replies": [
            "Create a free account to save jobs, track applications, get AI "
            "fit scores and build your profile strength. Register with your "
            "name, email and password.",
        ],
    },
    {
        "name": "skills",
        "patterns": ["skill", "learn", "course", "improve", "skill gap"],
        "replies": [
            "Add your skills to your profile with proficiency levels. "
            "WorkWise AI compares them with job requirements using cosine "
            "similarity and shows your AI Fit % and missing skills.",
        ],
    },
    {
        "name": "application",
        "patterns": ["application", "applied", "status", "tracking"],
        "replies": [
            "Your Dashboard shows all applications with a status timeline: "
            "Applied → Under Review → Shortlisted → Interview Scheduled → "
            "Offer. Saved jobs and notifications are also there.",
        ],
    },
    {
        "name": "sdg",
        "patterns": ["sdg", "sustainable", "decent work", "goal 8"],
        "replies": [
            "WorkWise AI supports UN SDG 8 — Decent Work and Economic "
            "Growth — by helping freshers and informal workers find fair "
            "opportunities and understand fair wages.",
        ],
    },
    {
        "name": "help",
        "patterns": ["help", "what can you do", "features", "hello", "hi"],
        "replies": [
            "Hi! I'm WorkWise AI. I can help you explore jobs, improve your "
            "resume, check fair wages, build career roadmaps, and prepare "
            "for interviews.",
        ],
    },
]

GREETING = ("Hi! I'm WorkWise AI. I can help you explore jobs, improve "
            "your resume, check fair wages, build career roadmaps, and "
            "prepare for interviews.")
