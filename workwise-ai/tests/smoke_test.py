"""Smoke tests for WorkWise AI API and page routes.

Run while the Flask server is running: python tests/smoke_test.py
Exercises every major endpoint and reports PASS/FAIL.
"""

import http.cookiejar
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = "http://127.0.0.1:5000"
results = []

# Cookie jar so the session cookie persists across requests
JAR = http.cookiejar.CookieJar()
OPENER = urllib.request.build_opener(
    urllib.request.HTTPCookieProcessor(JAR))


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # do not follow redirects


NO_REDIRECT = urllib.request.build_opener(
    urllib.request.HTTPCookieProcessor(JAR),
    NoRedirectHandler(),
)


def call(method, path, data=None, follow=True):
    """Make an HTTP request and return (status, parsed-or-text, headers)."""
    url = BASE + path
    body = None
    hdrs = {}
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        hdrs["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=hdrs,
                                   method=method)
    opener = OPENER if follow else NO_REDIRECT
    try:
        with opener.open(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            out_headers = dict(resp.headers)
            try:
                return resp.status, json.loads(raw), out_headers
            except json.JSONDecodeError:
                return resp.status, raw, out_headers
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
        try:
            return e.code, json.loads(raw), dict(e.headers)
        except json.JSONDecodeError:
            return e.code, raw, dict(e.headers)
    except urllib.error.URLError as e:
        return 0, str(e.reason), {}


def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))
    print(("PASS" if cond else "FAIL"), "-", name,
          ("" if cond else f"  -> {detail}"))


def has_session_cookie():
    return any(c.name == "session" for c in JAR)


def main():
    print("=" * 60)
    print("WorkWise AI smoke tests")
    print("=" * 60)

    # ---- Pages ----
    for path in ["/", "/login", "/register", "/jobs", "/job/1",
                 "/fair-wage", "/roadmaps", "/interview-prep"]:
        status, body, _ = call("GET", path)
        check(f"GET {path} == 200", status == 200, str(status))

    status, body, _ = call("GET", "/nonexistent-page")
    check("GET unknown page == 404", status == 404, str(status))

    # ---- API: jobs list ----
    status, data, _ = call("GET", "/api/jobs")
    check("GET /api/jobs == 200", status == 200, str(status))
    check("jobs count >= 20", data.get("count", 0) >= 20,
          str(data.get("count")))
    check("job has required fields",
          all(k in data["jobs"][0] for k in
              ["id", "title", "company", "skills", "salary_text"]),
          "missing fields")

    status, data, _ = call("GET", "/api/jobs?type=internship")
    check("internship filter works",
          status == 200 and all(j["is_internship"] for j in data["jobs"]),
          "non-internship leaked")
    status, data, _ = call("GET", "/api/jobs?q=Python")
    check("search q=Python returns results", data.get("count", 0) > 0,
          str(data.get("count")))
    status, data, _ = call("GET", "/api/jobs?location=Bengaluru")
    check("location filter works",
          status == 200 and data.get("count", 0) > 0, str(status))
    status, data, _ = call("GET", "/api/jobs?min_salary=30000")
    check("salary filter works",
          status == 200 and all(j["salary_max"] >= 30000
                                for j in data["jobs"]),
          "salary filter broken")

    status, data, _ = call("GET", "/api/jobs/1")
    check("GET /api/jobs/1 == 200", status == 200, str(status))
    status, data, _ = call("GET", "/api/jobs/9999")
    check("GET missing job == 404", status == 404, str(status))

    # ---- API: validation errors ----
    status, data, _ = call("POST", "/api/match-jobs", {})
    check("match-jobs without skills == 400", status == 400, str(status))
    status, data, _ = call("POST", "/api/predict-role", {"skills": []})
    check("predict-role empty skills == 400", status == 400, str(status))
    status, data, _ = call("POST", "/api/predict-wage",
                           {"trade": "Electrician"})
    check("predict-wage missing fields == 400", status == 400, str(status))
    status, data, _ = call("POST", "/api/predict-wage",
                           {"trade": "Ninja", "city_type": "Metro",
                            "experience": 5})
    check("predict-wage bad trade == 400", status == 400, str(status))
    status, data, _ = call("POST", "/api/predict-role",
                           {"skills": ["Python", "SQL", "Pandas",
                                       "Power BI"]})
    check("predict-role valid == 200 with 3 roles",
          status == 200 and len(data.get("top_roles", [])) == 3,
          str(status))

    # ---- ML predictions are model-driven ----
    status, data, _ = call("POST", "/api/predict-wage",
                           {"trade": "Electrician", "city_type": "Metro",
                            "experience": 5})
    check("predict-wage valid == 200", status == 200, str(status))
    check("wage has prediction + range + verdict",
          all(k in data for k in
              ["predicted_daily_wage", "lower_range", "upper_range",
               "verdict"]),
          str(data))
    check("wage verdict is one of the allowed values",
          data.get("verdict") in
          ["Under typical range", "Fair / typical", "Above typical range"],
          str(data.get("verdict")))

    status, data, _ = call("POST", "/api/predict-salary",
                           {"role": "Data Analyst", "skills": ["Python"],
                            "experience": 2, "city": "Metro"})
    check("predict-salary valid == 200", status == 200, str(status))

    # ---- match-jobs sorts by cosine similarity ----
    status, data, _ = call("POST", "/api/match-jobs",
                           {"skills": ["Python", "SQL", "Power BI"]})
    check("match-jobs == 200", status == 200, str(status))
    fits = [j["ai_fit"] for j in data.get("jobs", [])]
    check("match-jobs sorted descending",
          fits == sorted(fits, reverse=True), "not sorted")
    check("AI Fit values are 0-100",
          all(0 <= f <= 100 for f in fits), "out of range")

    # ---- chatbot ----
    status, data, _ = call("POST", "/api/chat", {"message": "hello"})
    check("chat greeting works", status == 200 and data.get("reply"),
          str(status))
    status, data, _ = call("POST", "/api/chat",
                           {"message": "roadmap for data analyst"})
    check("chat roadmap intent", status == 200
          and data.get("intent") == "roadmap", str(data))
    status, data, _ = call("POST", "/api/chat",
                           {"message": "what is the daily wage of an "
                                       "electrician in a metro city"})
    check("chat wage intent with live estimate",
          status == 200 and "₹" in data.get("reply", ""), str(data))
    status, data, _ = call("POST", "/api/chat", {"message": ""})
    check("chat empty message == 400", status == 400, str(status))

    # ---- auth guards (GET, not POST) ----
    status, data, _ = call("GET", "/api/dashboard")
    check("dashboard requires auth == 401", status == 401, str(status))
    status, data, _ = call("GET", "/api/profile")
    check("profile requires auth == 401", status == 401, str(status))

    # ---- register a test user (form POST) ----
    test_email = f"test{int(time.time())}@example.com"
    form = urllib.parse.urlencode({
        "name": "Test User", "email": test_email,
        "password": "password123", "confirm_password": "password123",
    }).encode()
    req = urllib.request.Request(BASE + "/register", data=form,
                                 method="POST")
    with OPENER.open(req, timeout=30) as resp:
        check("register creates session cookie",
              resp.status in (200, 302) and has_session_cookie(),
              f"status={resp.status} cookie={has_session_cookie()}")

    # duplicate email
    req = urllib.request.Request(BASE + "/register", data=form,
                                 method="POST")
    with OPENER.open(req, timeout=30) as resp:
        check("duplicate email rejected",
              "already exists" in resp.read().decode(), "no error shown")

    # ---- authenticated API ----
    status, data, _ = call("GET", "/api/dashboard")
    check("GET /api/dashboard authed == 200", status == 200, str(status))
    check("dashboard has stats",
          all(k in data for k in ["total_applications", "profile_strength",
                                  "skills_count"]),
          "missing keys")

    status, data, _ = call("GET", "/api/profile")
    check("GET /api/profile authed == 200", status == 200, str(status))

    status, data, _ = call("PUT", "/api/profile",
                           {"headline": "Test headline"})
    check("PUT /api/profile == 200", status == 200, str(status))

    status, data, _ = call("POST", "/api/profile/skills",
                           {"name": "Python", "proficiency": "Advanced",
                            "years": 2})
    check("add skill == 200", status == 200, str(status))
    status, data, _ = call("POST", "/api/profile/skills",
                           {"name": "", "proficiency": "Advanced"})
    check("add empty skill == 400", status == 400, str(status))
    status, data, _ = call("POST", "/api/profile/skills",
                           {"name": "SQL", "proficiency": "Expert"})
    check("bad proficiency == 400", status == 400, str(status))

    # save a job
    status, data, _ = call("POST", "/api/jobs/2/save", {})
    check("save job == 200", status == 200, str(status))
    status, data, _ = call("GET", "/api/dashboard")
    check("saved job appears on dashboard",
          (data.get("saved_jobs") or 0) >= 1, str(data.get("saved_jobs")))
    status, data, _ = call("DELETE", "/api/jobs/2/save")
    check("unsave job == 200", status == 200, str(status))

    # apply flow
    status, data, _ = call("POST", "/api/jobs/3/apply",
                           {"email": "x", "phone": "123",
                            "tenth_percent": "80", "twelfth_percent": "75",
                            "cgpa": "7.5", "summary": "short"})
    check("apply with invalid data == 400", status == 400, str(status))

    status, data, _ = call("POST", "/api/jobs/3/apply",
                           {"email": test_email, "phone": "9876543210",
                            "tenth_percent": "88%", "twelfth_percent": "82%",
                            "cgpa": "8.1", "summary": "I love data analysis.",
                            "projects": "Dashboard",
                            "certificates": "Python"})
    check("valid apply == 201", status == 201, str(status))
    status, data, _ = call("POST", "/api/jobs/3/apply",
                           {"email": test_email, "phone": "9876543210",
                            "tenth_percent": "88%", "twelfth_percent": "82%",
                            "cgpa": "8.1", "summary": "I love data analysis."})
    check("duplicate application == 409", status == 409, str(status))

    status, data, _ = call("GET", "/api/dashboard")
    check("application shows on dashboard",
          (data.get("total_applications") or 0) >= 1, str(status))

    # resume
    status, data, _ = call("POST", "/api/resume",
                           {"name": "Test User", "skills": ["Python"]})
    check("save resume == 200", status == 200, str(status))
    status, data, _ = call("GET", "/api/resume")
    check("get resume == 200", status == 200
          and data.get("name") == "Test User", str(status))

    # roadmap + interview
    status, data, _ = call("POST", "/api/roadmap",
                           {"role": "Data Analyst"})
    check("roadmap == 200 with 5 stages",
          status == 200 and len(data.get("stages", [])) == 5, str(status))
    check("roadmap has numbered stages",
          all(s.get("number") == i + 1
              for i, s in enumerate(data.get("stages", []))),
          "numbering wrong")
    status, data, _ = call("POST", "/api/roadmap", {"role": "Astronaut"})
    check("custom role roadmap == 200 (generic)", status == 200, str(status))
    status, data, _ = call("POST", "/api/roadmap", {})
    check("roadmap missing role == 400", status == 400, str(status))

    status, data, _ = call("POST", "/api/interview/questions",
                           {"role": "Data Analyst"})
    check("interview questions == 200 with 6 questions",
          status == 200 and len(data.get("questions", [])) == 6, str(status))
    status, data, _ = call("POST", "/api/interview/questions",
                           {"role": "Unknown Role"})
    check("interview unknown role == 404", status == 404, str(status))

    # practice (authed)
    status, data, _ = call("POST", "/api/practice",
                           {"role": "Data Analyst",
                            "question": "Tell me about yourself",
                            "answer": "I am a data analyst because I love "
                                      "finding patterns in data. For example, "
                                      "my project improved sales reports. "
                                      "My team learned a lot from it."})
    check("practice == 200 with feedback",
          status == 200 and "scores" in data.get("feedback", {}), str(status))

    # notifications
    status, data, _ = call("GET", "/api/notifications")
    check("notifications == 200", status == 200, str(status))
    status, data, _ = call("POST", "/api/notifications/read")
    check("mark notifications read == 200", status == 200, str(status))

    # protected page redirects (no redirect follow) — log out first
    call("GET", "/logout")
    status, body, headers = call("GET", "/dashboard", follow=False)
    check("GET /dashboard unauth redirects to login",
          status in (301, 302) and "login" in
          str(headers.get("Location", "")), f"{status}")

    status, body, headers = call("GET", "/logout")
    check("logout works", status in (200, 301, 302), str(status))

    # after logout, dashboard is protected again
    status, data, _ = call("GET", "/api/dashboard")
    check("after logout, dashboard == 401", status == 401, str(status))

    # ---- summary ----
    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print("=" * 60)
    print(f"RESULTS: {passed}/{total} passed")
    print("=" * 60)
    if passed != total:
        for name, ok, detail in results:
            if not ok:
                print(f"  FAILED: {name} -> {detail}")
        sys.exit(1)


if __name__ == "__main__":
    main()
