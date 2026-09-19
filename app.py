"""
app.py — Smart Health Assistant v3.0
First-time onboarding → Health dashboard → AI consultation using full profile.
Admin: admin@health.com / admin123
"""

import json
import os
import pickle
import time
from datetime import datetime
from functools import wraps
from urllib.parse import quote_plus

from flask import (Flask, abort, flash, redirect, render_template, request,
                   send_from_directory, session, url_for)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from ai_doctor import format_ai_text, gemini_enabled, get_ai_analysis
from medical_data import RECOMMENDATIONS, URGENT_DISEASES, get_specialists

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
ALLOWED_EXT = {"png", "jpg", "jpeg", "pdf"}

db = SQLAlchemy(app)
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

DURATIONS = ["Less than 1 day", "1-3 days", "4-7 days", "1-4 weeks", "More than 1 month"]
ACTIVITIES = ["Sedentary", "Light", "Moderate", "Active"]
SMOKING = ["Never", "Occasionally", "Quit", "Daily"]
ALCOHOL = ["Never", "Occasionally", "Regular"]
DIETS = ["Vegetarian", "Non-Vegetarian", "Eggetarian", "Vegan"]
STRESS = ["Low", "Medium", "High"]

with open("model.pkl", "rb") as f:
    _b = pickle.load(f)
MODEL = _b["model"]
SYMPTOMS = list(_b["symptoms"])


# ---------------- DATABASE ---------------- #
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    blood_group = db.Column(db.String(5))
    height_cm = db.Column(db.Integer)
    weight_kg = db.Column(db.Integer)
    city = db.Column(db.String(80))
    occupation = db.Column(db.String(60))
    physical_activity = db.Column(db.String(20))
    sleep_hours = db.Column(db.Float)
    diet_type = db.Column(db.String(20))
    smoking = db.Column(db.String(20))
    alcohol = db.Column(db.String(20))
    stress_level = db.Column(db.String(20))
    past_history = db.Column(db.Text)
    family_history = db.Column(db.Text)
    allergies = db.Column(db.Text)
    medications = db.Column(db.Text)
    onboarding_done = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    predictions = db.relationship("Prediction", backref="user", lazy=True)


class Prediction(db.Model):
    __tablename__ = "predictions"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    symptoms = db.Column(db.Text, nullable=False)
    custom_symptoms = db.Column(db.Text)
    duration = db.Column(db.String(30))
    severity = db.Column(db.String(20))
    disease = db.Column(db.String(100), nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    top3 = db.Column(db.Text)
    ai_analysis = db.Column(db.Text)
    ai_engine = db.Column(db.String(40))
    report_filename = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ---------------- HEALTH METRICS ENGINE ---------------- #
def health_metrics(user):
    """BMI, health score, water, BMR + lifestyle insights from profile."""
    h, w = user.height_cm, user.weight_kg
    bmi = round(w / ((h / 100) ** 2), 1) if h and w else None

    if bmi is None:
        category = None
    elif bmi < 18.5:
        category = "Underweight"
    elif bmi < 25:
        category = "Normal"
    elif bmi < 30:
        category = "Overweight"
    else:
        category = "Obese"

    ideal = None
    if h:
        lo = round(18.5 * (h / 100) ** 2, 1)
        hi = round(24.9 * (h / 100) ** 2, 1)
        ideal = f"{lo}–{hi} kg"

    water = round(w * 0.033, 1) if w else None          # litres/day

    bmr = None
    if h and w and user.age and user.gender:
        base = 10 * w + 6.25 * h - 5 * user.age
        bmr = int(base + (5 if user.gender == "Male" else -161))

    # ---- Health Score (0-100) ----
    score = 40
    if bmi:
        score += {"Normal": 25, "Underweight": 13, "Overweight": 13,
                  "Obese": 5}.get(category, 10)
    score += {"Active": 20, "Moderate": 15, "Light": 10,
              "Sedentary": 5}.get(user.physical_activity or "", 10)
    score += {"Never": 15, "Quit": 12, "Occasionally": 7,
              "Daily": 0}.get(user.smoking or "", 8)
    score += {"Never": 10, "Occasionally": 6, "Regular": 0}.get(user.alcohol or "", 5)
    if user.sleep_hours:
        score += 15 if 7 <= user.sleep_hours <= 9 else 6
    score += {"Low": 10, "Medium": 5, "High": 0}.get(user.stress_level or "", 5)
    score = max(0, min(100, score))

    label = ("Excellent" if score >= 80 else "Good" if score >= 65 else
             "Fair" if score >= 45 else "Needs Attention")

    # ---- Personalised lifestyle insights ----
    tips = []
    if category == "Overweight" or category == "Obese":
        tips.append("Your BMI is above the normal range — 30 minutes of brisk walking daily will help.")
    if category == "Underweight":
        tips.append("Your BMI is below normal — add nutritious calorie-rich foods like nuts, bananas and dairy.")
    if user.physical_activity == "Sedentary":
        tips.append("You have a sedentary routine — take a 5-minute walk break every hour.")
    if user.smoking == "Daily":
        tips.append("Quitting smoking is the single biggest health upgrade you can make.")
    if user.alcohol == "Regular":
        tips.append("Reduce alcohol intake — keep it occasional or none.")
    if user.sleep_hours and user.sleep_hours < 7:
        tips.append(f"You sleep {user.sleep_hours}h — aim for 7–9 hours for better immunity.")
    if user.stress_level == "High":
        tips.append("High stress detected — try 10 minutes of deep breathing or meditation daily.")
    if not tips:
        tips.append("Great job! Your lifestyle metrics look healthy — keep it up.")

    return {"bmi": bmi, "bmi_category": category, "ideal_weight": ideal,
            "water": water, "bmr": bmr, "health_score": score,
            "score_label": label, "tips": tips}


# ---------------- HELPERS ---------------- #
def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.", "warning")
            return redirect(url_for("login"))
        # Guard: session points to a user that no longer exists
        if db.session.get(User, session["user_id"]) is None:
            session.clear()
            flash("Session expired — please log in again.", "info")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped

def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        if not session.get("is_admin"):
            flash("Admin access only.", "danger")
            return redirect(url_for("index"))
        return view(*args, **kwargs)
    return wrapped


def get_top3(selected):
    vector = [[1 if s in selected else 0 for s in SYMPTOMS]]
    probs = MODEL.predict_proba(vector)[0]
    pairs = sorted(zip(MODEL.classes_, probs), key=lambda p: p[1], reverse=True)[:3]
    return [(d, round(float(p) * 100, 1)) for d, p in pairs if p > 0]


def maps_url(specialty, city):
    q = f"{specialty} doctor" + (f" in {city}" if city else " near me")
    return "https://www.google.com/maps/search/" + quote_plus(q)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT


def _profile_dict(user, form=None):
    """FULL patient picture (vitals + lifestyle + history) for the AI."""
    m = health_metrics(user)
    p = {"age": user.age, "gender": user.gender, "city": user.city,
         "blood_group": user.blood_group,
         "height_cm": user.height_cm, "weight_kg": user.weight_kg,
         "bmi": m["bmi"], "bmi_category": m["bmi_category"],
         "health_score": m["health_score"],
         "physical_activity": user.physical_activity,
         "sleep_hours": user.sleep_hours, "diet_type": user.diet_type,
         "smoking": user.smoking, "alcohol": user.alcohol,
         "stress_level": user.stress_level, "occupation": user.occupation,
         "past_history": user.past_history, "family_history": user.family_history,
         "allergies": user.allergies, "medications": user.medications}
    if form:
        for k in ("past_history", "family_history", "allergies", "medications"):
            v = (form.get(k) or "").strip()
            if v:
                p[k] = v
    return p


# ---------------- PUBLIC ---------------- #
@app.route("/")
def index():
    return render_template("index.html",
                           disease_count=len(MODEL.classes_),
                           symptom_count=len(SYMPTOMS),
                           ai_enabled=gemini_enabled())


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")

        errors = []
        if not name or not email or not password:
            errors.append("Name, email and password are required.")
        if password and len(password) < 6:
            errors.append("Password must be at least 6 characters.")
        if password != confirm:
            errors.append("Passwords do not match.")
        if User.query.filter_by(email=email).first():
            errors.append("This email is already registered.")
        if errors:
            for e in errors:
                flash(e, "danger")
        else:
            user = User(name=name, email=email,
                        password_hash=generate_password_hash(password))
            db.session.add(user)
            db.session.commit()
            session["user_id"] = user.id
            session["user_name"] = user.name
            session["is_admin"] = user.is_admin
            flash("Account created! Let's set up your health profile 🩺", "success")
            return redirect(url_for("onboarding"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash,
                                        request.form.get("password", "")):
            session["user_id"] = user.id
            session["user_name"] = user.name
            session["is_admin"] = user.is_admin
            flash(f"Welcome back, {user.name}! 👋", "success")
            if not user.onboarding_done:
                return redirect(url_for("onboarding"))
            return redirect(url_for("dashboard"))
        flash("Invalid email or password.", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


# ---------------- ONBOARDING (first-time profile) ---------------- #
@app.route("/onboarding", methods=["GET", "POST"])
@login_required
def onboarding():
    user = db.session.get(User, session["user_id"])

    if request.method == "POST":
        user.age = int(request.form["age"]) if request.form.get("age") else None
        user.gender = request.form.get("gender") or None
        user.blood_group = request.form.get("blood_group") or None
        user.city = request.form.get("city", "").strip() or None
        user.occupation = request.form.get("occupation", "").strip() or None
        user.height_cm = int(request.form["height_cm"]) if request.form.get("height_cm") else None
        user.weight_kg = int(request.form["weight_kg"]) if request.form.get("weight_kg") else None
        user.physical_activity = request.form.get("physical_activity") or None
        user.sleep_hours = float(request.form["sleep_hours"]) if request.form.get("sleep_hours") else None
        user.diet_type = request.form.get("diet_type") or None
        user.smoking = request.form.get("smoking") or None
        user.alcohol = request.form.get("alcohol") or None
        user.stress_level = request.form.get("stress_level") or None
        user.past_history = request.form.get("past_history", "").strip() or None
        user.family_history = request.form.get("family_history", "").strip() or None
        user.allergies = request.form.get("allergies", "").strip() or None
        user.medications = request.form.get("medications", "").strip() or None
        user.onboarding_done = True
        db.session.commit()
        flash("Health profile saved! Your AI doctor now knows you better 🎉", "success")
        return redirect(url_for("dashboard"))

    return render_template("onboarding.html", user=user,
                           activities=ACTIVITIES, smoking=SMOKING,
                           alcohol=ALCOHOL, diets=DIETS, stress=STRESS)


# ---------------- DASHBOARD ---------------- #
@app.route("/dashboard")
@login_required
def dashboard():
    user = db.session.get(User, session["user_id"])
    if not user.onboarding_done:
        return redirect(url_for("onboarding"))

    m = health_metrics(user)
    recent = (Prediction.query.filter_by(user_id=user.id)
              .order_by(Prediction.created_at.desc()).limit(5).all())
    total = Prediction.query.filter_by(user_id=user.id).count()
    return render_template("dashboard.html", user=user, m=m, recent=recent,
                           total=total, urgent_set=URGENT_DISEASES,
                           ai_enabled=gemini_enabled())


# ---------------- AI CONSULTATION ---------------- #
@app.route("/consult", methods=["GET", "POST"])
@login_required
def consult():
    user = db.session.get(User, session["user_id"])
    if not user.onboarding_done:
        flash("Complete your health profile first — it makes diagnosis far more accurate! 🩺", "info")
        return redirect(url_for("onboarding"))

    if request.method == "POST":
        selected = request.form.getlist("symptoms")
        raw_custom = request.form.get("custom_symptoms", "[]")
        try:
            custom = [c.strip() for c in json.loads(raw_custom) if c and c.strip()]
        except (ValueError, TypeError):
            custom = [c.strip() for c in raw_custom.split(",") if c.strip()]

        duration = request.form.get("duration", "").strip()
        severity = request.form.get("severity", "").strip()

        if len(selected) + len(custom) < 3:
            flash("Please select/describe at least 3 symptoms.", "warning")
            return redirect(url_for("consult"))
        if not duration or not severity:
            flash("Please select symptom duration and severity.", "warning")
            return redirect(url_for("consult"))
        if not request.form.get("consent"):
            flash("Please confirm the awareness declaration.", "warning")
            return redirect(url_for("consult"))

        report_filename = None
        file = request.files.get("report_file")
        if file and file.filename:
            if not allowed_file(file.filename):
                flash("Report must be a PDF, JPG or PNG file.", "warning")
                return redirect(url_for("consult"))
            report_filename = (f"user{user.id}_{int(time.time())}_"
                               f"{secure_filename(file.filename)}")
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], report_filename))

        top3 = get_top3(selected)
        if top3:
            disease, confidence = top3[0]
        else:
            disease, confidence = "Undetermined", 0.0

        profile = _profile_dict(user, request.form)
        ai_text, engine = get_ai_analysis(profile, selected, custom,
                                          top3, duration, severity)

        record = Prediction(
            user_id=user.id, symptoms=json.dumps(selected),
            custom_symptoms=json.dumps(custom), duration=duration,
            severity=severity, disease=disease, confidence=confidence,
            top3=json.dumps(top3), ai_analysis=ai_text, ai_engine=engine,
            report_filename=report_filename)
        db.session.add(record)
        db.session.commit()
        return redirect(url_for("result", prediction_id=record.id))

    return render_template("consult.html", symptoms=SYMPTOMS,
                           durations=DURATIONS, user=user,
                           ai_enabled=gemini_enabled())


@app.route("/result/<int:prediction_id>")
@login_required
def result(prediction_id):
    p = db.get_or_404(Prediction, prediction_id)
    if p.user_id != session["user_id"] and not session.get("is_admin"):
        abort(403)
    user = db.session.get(User, p.user_id)
    m = health_metrics(user)

    symptoms = json.loads(p.symptoms)
    custom = json.loads(p.custom_symptoms or "[]")
    top3 = json.loads(p.top3 or "[]")

    specialists = get_specialists(p.disease)
    for doc in specialists:
        doc["maps"] = maps_url(doc["specialty"], user.city)

    return render_template("result.html", p=p, user=user, m=m, top3=top3,
                           symptoms=symptoms, custom=custom,
                           ai_html=format_ai_text(p.ai_analysis or ""),
                           engine=p.ai_engine or "built-in engine",
                           specialists=specialists,
                           urgent=p.disease in URGENT_DISEASES,
                           advice=RECOMMENDATIONS.get(p.disease, ""))


# ---------------- USER PAGES ---------------- #
@app.route("/history")
@login_required
def history():
    preds = (Prediction.query.filter_by(user_id=session["user_id"])
             .order_by(Prediction.created_at.desc()).all())
    rows = [(p, json.loads(p.symptoms), json.loads(p.custom_symptoms or "[]"))
            for p in preds]
    counts = {}
    for p in preds:
        counts[p.disease] = counts.get(p.disease, 0) + 1
    return render_template("history.html", predictions=rows,
                           urgent_set=URGENT_DISEASES,
                           chart_labels=json.dumps(list(counts.keys())),
                           chart_data=json.dumps(list(counts.values())))


@app.route("/report/<int:prediction_id>")
@login_required
def report(prediction_id):
    p = db.get_or_404(Prediction, prediction_id)
    if p.user_id != session["user_id"] and not session.get("is_admin"):
        abort(403)
    user = db.session.get(User, p.user_id)
    return render_template("report.html", p=p, user=user,
                           symptoms=json.loads(p.symptoms),
                           custom=json.loads(p.custom_symptoms or "[]"),
                           top3=json.loads(p.top3 or "[]"),
                           ai_html=format_ai_text(p.ai_analysis or ""),
                           specialists=get_specialists(p.disease),
                           urgent=p.disease in URGENT_DISEASES)


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user = db.session.get(User, session["user_id"])
    if request.method == "POST":
        user.age = int(request.form["age"]) if request.form.get("age") else None
        user.gender = request.form.get("gender") or None
        user.blood_group = request.form.get("blood_group") or None
        user.height_cm = int(request.form["height_cm"]) if request.form.get("height_cm") else None
        user.weight_kg = int(request.form["weight_kg"]) if request.form.get("weight_kg") else None
        user.city = request.form.get("city", "").strip() or None
        user.occupation = request.form.get("occupation", "").strip() or None
        user.physical_activity = request.form.get("physical_activity") or None
        user.sleep_hours = float(request.form["sleep_hours"]) if request.form.get("sleep_hours") else None
        user.diet_type = request.form.get("diet_type") or None
        user.smoking = request.form.get("smoking") or None
        user.alcohol = request.form.get("alcohol") or None
        user.stress_level = request.form.get("stress_level") or None
        user.past_history = request.form.get("past_history", "").strip() or None
        user.family_history = request.form.get("family_history", "").strip() or None
        user.allergies = request.form.get("allergies", "").strip() or None
        user.medications = request.form.get("medications", "").strip() or None
        user.onboarding_done = True
        db.session.commit()
        flash("Health profile updated ✅", "success")
        return redirect(url_for("profile"))

    m = health_metrics(user)
    count = Prediction.query.filter_by(user_id=user.id).count()
    return render_template("profile.html", user=user, m=m, count=count,
                           activities=ACTIVITIES, smoking=SMOKING,
                           alcohol=ALCOHOL, diets=DIETS, stress=STRESS)


@app.route("/uploads/<path:filename>")
@login_required
def uploaded_file(filename):
    p = Prediction.query.filter_by(report_filename=filename).first()
    if not p:
        abort(404)
    if p.user_id != session["user_id"] and not session.get("is_admin"):
        abort(403)
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


# ---------------- ADMIN ---------------- #
@app.route("/admin")
@admin_required
def admin():
    users = User.query.order_by(User.created_at.desc()).all()
    preds = (Prediction.query.order_by(Prediction.created_at.desc()).limit(15).all())
    top = (db.session.query(Prediction.disease, db.func.count(Prediction.id))
           .group_by(Prediction.disease)
           .order_by(db.func.count(Prediction.id).desc()).limit(6).all())
    today = datetime.utcnow().date()
    stats = {"users": len(users), "total": Prediction.query.count(),
             "today": Prediction.query.filter(
                 db.func.date(Prediction.created_at) == today).count(),
             "urgent": Prediction.query.filter(
                 Prediction.disease.in_(URGENT_DISEASES)).count()}
    return render_template("admin.html", users=users, predictions=preds,
                           top_diseases=top, stats=stats,
                           urgent_set=URGENT_DISEASES,
                           chart_labels=json.dumps([t[0] for t in top]),
                           chart_data=json.dumps([t[1] for t in top]))


# ---------------- INIT ---------------- #
def init_db():
    db.create_all()
    if not User.query.filter_by(is_admin=True).first():
        db.session.add(User(name="Administrator", email="admin@health.com",
                            password_hash=generate_password_hash("admin123"),
                            is_admin=True, onboarding_done=True))
        db.session.commit()


with app.app_context():
    init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)