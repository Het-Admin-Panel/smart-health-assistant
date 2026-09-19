"""check_files.py — finds exactly which file is broken. Run: python check_files.py"""

import os
import re

issues = []

def ok(msg):  print("  OK   " + msg)
def bad(msg): issues.append(msg); print("  BAD  " + msg)
def warn(msg): print("  WARN " + msg)

print("=" * 60)
print("SMART HEALTH ASSISTANT - FILE CHECKER")
print("=" * 60)

# ---------- 1. Required root files ----------
print("\n[1] Required files")
for f in ["app.py", "train_model.py", "medical_data.py", "ai_doctor.py",
          "dataset.csv", "model.pkl", "requirements.txt", "static/style.css"]:
    (ok if os.path.exists(f) else bad)("file exists: " + f)

if os.path.exists("templates/templates"):
    bad("NESTED folder found: templates/templates - move files up one level!")

# ---------- 2. Templates ----------
MARKERS = {
    "base.html":       "app-nav",
    "index.html":      "AI Doctor",
    "login.html":      "Welcome Back",
    "register.html":   "Health Journey",
    "onboarding.html": "Health Profile",
    "dashboard.html":  "Health Score",
    "consult.html":    "Consultation",
    "result.html":     "Most Likely Condition",
    "history.html":    "History",
    "profile.html":    "MEDICAL BACKGROUND",
    "admin.html":      "Admin Dashboard",
    "report.html":     "Case Sheet",
}
NO_USER = {"index.html", "login.html", "register.html", "history.html", "admin.html"}

print("\n[2] Templates")
for name, marker in MARKERS.items():
    path = os.path.join("templates", name)
    if not os.path.exists(path):
        bad("templates/" + name + " MISSING")
        continue
    text = open(path, encoding="utf-8").read()
    lines = text.strip().splitlines()
    first = lines[0].strip() if lines else ""

    if name in ("base.html", "report.html"):
        if not first.lower().startswith("<!doctype"):
            bad(name + ": line 1 must be <!DOCTYPE html>, found: " + first[:50])
    else:
        if first != '{% extends "base.html" %}':
            bad(name + ': line 1 must be {% extends "base.html" %}, found: ' + first[:50])
        else:
            n_block = len(re.findall(r"{%-?\s*block", text))
            n_end = len(re.findall(r"{%-?\s*endblock", text))
            if n_block == 0 or n_block != n_end:
                bad(name + ": unbalanced blocks (" + str(n_block) + " block vs "
                    + str(n_end) + " endblock) - incomplete paste!")

    if marker and marker.lower() not in text.lower():
        bad(name + ": marker '" + marker + "' not found - WRONG VERSION pasted!")

    if name in NO_USER:
        for m in re.findall(r"{{\s*(user|m)\.", text):
            bad(name + ": uses '" + m + ".' variable - NOT allowed here (wrong file pasted!)")

    if name == "onboarding.html" and "Sedentary %}" in text:
        bad("onboarding.html: typo 'Sedentary %}' - missing quote, see my fix message")

# ---------- 3. app.py ----------
print("\n[3] app.py")
app_text = open("app.py", encoding="utf-8").read()
(ok if "Session expired" in app_text else warn)("stale-session guard present")
for route in ['"/onboarding"', '"/dashboard"', '"/consult"',
              '"/result/<int:prediction_id>"']:
    (ok if route in app_text else bad)("route " + route)
(ok if "onboarding_done" in app_text else bad)("onboarding_done logic present (v3 app.py)")

# ---------- 4. style.css ----------
print("\n[4] static/style.css")
css = open("static/style.css", encoding="utf-8").read()
(ok if ".auth-wrap" in css else warn)("v3 design present (auth-wrap)")

# ---------- Summary ----------
print("\n" + "=" * 60)
if issues:
    print("FOUND " + str(len(issues)) + " PROBLEM(S):")
    for i in issues:
        print("  -> " + i)
    print("\nFix ONLY the files listed above (re-paste them fully),")
    print("then RESTART: Ctrl+C  ->  python app.py  ->  Ctrl+F5 in browser")
else:
    print("ALL FILES LOOK GOOD!")
    print("If it still fails, paste the red traceback from the terminal.")
print("=" * 60)