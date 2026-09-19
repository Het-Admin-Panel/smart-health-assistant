"""
app.py — Smart Health Assistant (Flask application)
Run:  python app.py   →  http://127.0.0.1:5000

Default admin login:  admin@health.com  /  admin123
"""
import os
import json
import pickle
import json
import pickle
from datetime import datetime
from functools import wraps

from flask import (Flask, flash, redirect, render_template, request,
                   session, url_for)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = "change-this-to-a-random-string-of-yours"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
db = SQLAlchemy(app)

# ------------------------------------------------------------------ #
#  MACHINE LEARNING MODEL (loaded once at startup)                    #
# ------------------------------------------------------------------ #
with open("model.pkl", "rb") as f:
    _bundle = pickle.load(f)
MODEL = _bundle["model"]
SYMPTOMS = list(_bundle["symptoms"])

# Conditions that need urgent medical attention (shown as red alert)
URGENT_DISEASES = {
    "Dengue", "Malaria", "Typhoid", "Hepatitis A", "Pneumonia",
    "Tuberculosis", "Appendicitis", "Kidney Stone", "COVID-19", "Measles",
}

RECOMMENDATIONS = {
    "Migraine": "Rest in a dark, quiet room. Stay hydrated and take a mild painkiller if needed. Track trigger foods and stress.",
    "Influenza": "Get plenty of rest, drink warm fluids and take paracetamol for fever. See a doctor if fever lasts more than 3 days.",
    "Common Cold": "Rest, drink fluids and do steam inhalation. A cold usually resolves within 7-10 days without antibiotics.",
    "Dengue": "Drink plenty of fluids and get a platelet count test. Consult a doctor immediately - dengue can become serious.",
    "Malaria": "Get a blood test (malarial parasite) immediately. Malaria requires prescribed anti-malarial medication.",
    "Typhoid": "Consult a doctor for a Widal test and antibiotics. Eat soft, non-spicy food and drink boiled water.",
    "Hepatitis A": "Get liver function tests. Complete rest, avoid alcohol and fatty foods. Needs medical monitoring.",
    "Pneumonia": "Consult a doctor immediately for a chest X-ray and antibiotics. Fever with breathing difficulty needs urgent care.",
    "Tuberculosis": "Get a sputum test and chest X-ray. TB is fully curable with a long course of prescribed medication.",
    "Asthma": "Use your prescribed inhaler and avoid triggers (dust, smoke, cold air). Always carry a reliever inhaler.",
    "Bronchitis": "Rest, drink fluids and use a humidifier. See a doctor if the cough lasts more than 3 weeks.",
    "Sinusitis": "Do steam inhalation and saline nasal rinses. See a doctor if symptoms last more than 10 days.",
    "Gastroenteritis": "Focus on rehydration with ORS. Eat light food like rice and bananas until symptoms settle.",
    "Food Poisoning": "Sip ORS or water frequently. Avoid solid food for a few hours. See a doctor if vomiting persists.",
    "Appendicitis": "Go to a hospital immediately. Do not eat or drink anything until a doctor examines you.",
    "Gastritis": "Eat small frequent meals, avoid spicy food, alcohol and ibuprofen-type painkillers. Antacids help.",
    "Peptic Ulcer": "Avoid spicy food, alcohol and NSAID painkillers. Get tested for H. pylori infection.",
    "GERD": "Avoid late-night meals, elevate your head while sleeping, reduce weight and limit caffeine.",
    "Urinary Tract Infection": "Drink lots of water and do not hold urine. Antibiotics are usually needed - get a urine test.",
    "Kidney Stone": "Drink 3-4 litres of water daily and consult a urologist. Severe pain needs immediate care.",
    "Diabetes": "Get a fasting blood sugar and HbA1c test. Control diet, exercise daily and follow up with a physician.",
    "Hypertension": "Monitor blood pressure regularly, reduce salt, exercise, and consult a physician for medication.",
    "Anemia": "Eat iron-rich foods (green vegetables, dates, jaggery) and get a CBC test. Iron supplements may be needed.",
    "Hypothyroidism": "Get a thyroid profile (TSH, T3, T4) test. Daily medication is usually required.",
    "Arthritis": "Apply warm compresses, do gentle joint exercises and maintain a healthy weight. See a rheumatologist.",
    "Chickenpox": "Isolate yourself, apply calamine lotion and do not scratch blisters. Contagious until blisters crust over.",
    "Measles": "Rest, drink fluids and isolate - measles is highly contagious. Vitamin A supplementation is often advised.",
    "Conjunctivitis": "Do not rub your eyes; use a clean towel and warm compress. Consult a doctor for eye drops.",
    "Eczema": "Moisturise frequently, avoid harsh soaps and take short lukewarm baths. See a dermatologist if severe.",
    "Psoriasis": "Keep skin moisturised. Moderate sunlight may help. A dermatologist can offer effective treatments.",
    "Fungal Skin Infection": "Apply an antifungal cream, keep the area dry and do not share towels or clothes.",
    "Anxiety Disorder": "Practise deep breathing, reduce caffeine and maintain a routine. Counselling or therapy helps greatly.",
    "Depression": "Talk to someone you trust. Depression is treatable - please consult a mental health professional.",
    "Insomnia": "Keep a fixed sleep schedule, avoid screens before bed and limit caffeine after noon.",
    "COVID-19": "Isolate yourself, rest and monitor oxygen levels. Get tested and follow local health guidelines.",
    "Allergic Rhinitis": "Avoid known allergens, use a mask outdoors, and take an antihistamine if needed.",
    "Dehydration": "Drink ORS or water steadily, rest and avoid sun exposure until you recover.",
    "Vertigo": "Move slowly, sit down when dizzy and consult an ENT specialist. The Epley manoeuvre helps some types.",
    "Hemorrhoids": "Eat high-fibre food, drink water, take warm sitz baths and avoid straining. See a doctor if bleeding continues.",
    "Tonsillitis": "Gargle with warm salt water, eat soft cool foods and rest. See a doctor for a throat infection check.",
    "Ear Infection": "Do not insert anything into the ear. Use a warm compress; see an ENT doctor if pain lasts over 2 days.",
    "Tooth Infection": "See a dentist as soon as possible - dental infections can spread. Rinse with warm salt water meanwhile.",
    "Acne": "Wash gently twice daily, do not pick pimples, and use non-comedogenic products. See a dermatologist if severe.",
}

# ------------------------------------------------------------------ #
#  DATABASE MODELS                                                    #
# ------------------------------------------------------------------ #
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    predictions = db.relationship("Prediction", backref="user", lazy=True)


class Prediction(db.Model):
    __tablename__ = "predictions"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    symptoms = db.Column(db.Text, nullable=False)      # stored as JSON list
    disease = db.Column(db.String(100), nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ------------------------------------------------------------------ #
#  DECORATORS                                                         #
# ------------------------------------------------------------------ #
def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.", "warning")
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


# ------------------------------------------------------------------ #
#  PREDICTION LOGIC — returns top-3 (disease, confidence%)            #
# ------------------------------------------------------------------ #
def get_top3(selected):
    vector = [[1 if s in selected else 0 for s in SYMPTOMS]]
    probs = MODEL.predict_proba(vector)[0]
    pairs = sorted(zip(MODEL.classes_, probs),
                   key=lambda p: p[1], reverse=True)[:3]
    return [(d, round(float(p) * 100, 1)) for d, p in pairs if p > 0]


# ------------------------------------------------------------------ #
#  ROUTES                                                             #
# ------------------------------------------------------------------ #
@app.route("/")
def index():
    return render_template("index.html",
                           disease_count=len(MODEL.classes_),
                           symptom_count=len(SYMPTOMS))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")
        age = request.form.get("age")
        gender = request.form.get("gender")

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
                        password_hash=generate_password_hash(password),
                        age=int(age) if age else None, gender=gender)
            db.session.add(user)
            db.session.commit()
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for("login"))

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
            flash(f"Welcome back, {user.name}!", "success")
            return redirect(url_for("index"))
        flash("Invalid email or password.", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


@app.route("/predict", methods=["GET", "POST"])
@login_required
def predict():
    if request.method == "POST":
        selected = request.form.getlist("symptoms")
        if len(selected) < 3:
            flash("Please select at least 3 symptoms.", "warning")
            return redirect(url_for("predict"))

        top3 = get_top3(selected)
        disease, confidence = top3[0]

        record = Prediction(user_id=session["user_id"],
                            symptoms=json.dumps(selected),
                            disease=disease, confidence=confidence)
        db.session.add(record)
        db.session.commit()

        return render_template(
            "result.html", top3=top3, selected=selected,
            advice=RECOMMENDATIONS.get(disease, "Consult a doctor."),
            urgent=disease in URGENT_DISEASES,
            prediction_id=record.id)

    return render_template("predict.html", symptoms=SYMPTOMS)


@app.route("/history")
@login_required
def history():
    preds = (Prediction.query.filter_by(user_id=session["user_id"])
             .order_by(Prediction.created_at.desc()).all())

    rows = [(p, json.loads(p.symptoms)) for p in preds]

    counts = {}
    for p in preds:
        counts[p.disease] = counts.get(p.disease, 0) + 1

    return render_template("history.html", predictions=rows,
                           chart_labels=json.dumps(list(counts.keys())),
                           chart_data=json.dumps(list(counts.values())))


@app.route("/report/<int:prediction_id>")
@login_required
def report(prediction_id):
    p = db.get_or_404(Prediction, prediction_id)
    if p.user_id != session["user_id"] and not session.get("is_admin"):
        flash("You can only view your own reports.", "danger")
        return redirect(url_for("history"))

    return render_template("report.html", p=p,
                           symptoms=json.loads(p.symptoms),
                           advice=RECOMMENDATIONS.get(p.disease, ""),
                           urgent=p.disease in URGENT_DISEASES,
                           user=db.session.get(User, p.user_id))


@app.route("/profile")
@login_required
def profile():
    user = db.session.get(User, session["user_id"])
    count = Prediction.query.filter_by(user_id=user.id).count()
    return render_template("profile.html", user=user, count=count)


@app.route("/admin")
@admin_required
def admin():
    users = User.query.order_by(User.created_at.desc()).all()
    preds = (Prediction.query.order_by(Prediction.created_at.desc())
             .limit(50).all())
    top = (db.session.query(Prediction.disease, db.func.count(Prediction.id))
           .group_by(Prediction.disease)
           .order_by(db.func.count(Prediction.id).desc()).limit(5).all())
    return render_template("admin.html", users=users, predictions=preds,
                           top_diseases=top,
                           total_preds=Prediction.query.count())


# ------------------------------------------------------------------ #
#  INITIALISE DB + DEFAULT ADMIN                                      #
# ------------------------------------------------------------------ #
def init_db():
    db.create_all()
    if not User.query.filter_by(is_admin=True).first():
        db.session.add(User(name="Administrator",
                            email="admin@health.com",
                            password_hash=generate_password_hash("admin123"),
                            is_admin=True))
        db.session.commit()


# Create database + admin on startup (works locally AND on the server)
with app.app_context():
    init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)