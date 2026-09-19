"""fix_files.py — auto-fixes the 2 problems found by check_files.py
Run:  python fix_files.py
"""

import os

# ============ FIX 1: rewrite register.html (correct version) ============
REGISTER_HTML = """{% extends "base.html" %}
{% block title %}Register | Smart Health Assistant{% endblock %}
{% block content %}
<div class="auth-wrap">
  <div class="auth-left text-white">
    <div class="brand-badge brand-light"><i class="bi bi-heart-pulse-fill"></i> Smart<span>Health</span> AI</div>
    <h2 class="fw-bold mt-4 mb-3">Start Your Health Journey 🚀</h2>
    <p class="opacity-75 mb-4">Create an account, complete your health profile once,
    and every future consultation becomes smarter and more personal.</p>
    <div class="auth-points">
      <div><i class="bi bi-clipboard2-check"></i> 2-minute guided profile setup</div>
      <div><i class="bi bi-calculator"></i> Free BMI &amp; health score tracking</div>
      <div><i class="bi bi-robot"></i> Gemini AI doctor trained on your context</div>
      <div><i class="bi bi-shield-check"></i> Passwords securely hashed</div>
    </div>
  </div>
  <div class="auth-right">
    <div class="card-soft p-4 p-md-5">
      <h4 class="fw-bold text-center mb-1">Create Account</h4>
      <p class="text-center text-muted small mb-4">Step 1 of 2 — your details come next</p>
      <form method="POST">
        <div class="mb-3">
          <label class="form-label fw-semibold small">Full Name</label>
          <div class="input-group">
            <span class="input-group-text bg-light"><i class="bi bi-person"></i></span>
            <input type="text" name="name" class="form-control form-control-lg" required>
          </div>
        </div>
        <div class="mb-3">
          <label class="form-label fw-semibold small">Email</label>
          <div class="input-group">
            <span class="input-group-text bg-light"><i class="bi bi-envelope"></i></span>
            <input type="email" name="email" class="form-control form-control-lg" required>
          </div>
        </div>
        <div class="mb-3">
          <label class="form-label fw-semibold small">Password <small class="text-muted">(min 6 chars)</small></label>
          <div class="input-group">
            <span class="input-group-text bg-light"><i class="bi bi-lock"></i></span>
            <input type="password" name="password" class="form-control form-control-lg" required>
          </div>
        </div>
        <div class="mb-4">
          <label class="form-label fw-semibold small">Confirm Password</label>
          <div class="input-group">
            <span class="input-group-text bg-light"><i class="bi bi-lock-fill"></i></span>
            <input type="password" name="confirm" class="form-control form-control-lg" required>
          </div>
        </div>
        <button class="btn btn-grad w-100 py-3 fw-bold">Create Account <i class="bi bi-arrow-right"></i></button>
      </form>
      <p class="text-center mt-4 mb-0 small">
        Already registered? <a href="{{ url_for('login') }}" class="fw-bold">Login</a>
      </p>
    </div>
  </div>
</div>
{% endblock %}
"""

with open(os.path.join("templates", "register.html"), "w", encoding="utf-8") as f:
    f.write(REGISTER_HTML)
print("FIXED  : templates/register.html rewritten with the correct version")

# ============ FIX 2: repair the onboarding.html typo ============
path = os.path.join("templates", "onboarding.html")
text = open(path, encoding="utf-8").read()
if "'Sedentary %}" in text:
    text = text.replace("'Sedentary %}", "'Sedentary' %}")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print("FIXED  : onboarding.html — missing quote after 'Sedentary' added")
elif "'Sedentary' %}" in text:
    print("OK     : onboarding.html typo already fixed")
else:
    print("WARN   : onboarding.html — expected text not found, check manually")

print()
print("DONE! Now:  1) Ctrl+C in the app terminal   2) python app.py   3) Ctrl+F5 in browser")