"""ai_doctor.py — v3 STRICT RESEARCH MODE
- temperature 0.1 + top_k 1  -> near-deterministic output (no random answers)
- evidence-based clinical reasoning prompt
- personalised diet/exercise/lifestyle/follow-up plan
- rule-based fallback if Gemini unavailable (never crashes)"""

import html as _html
import os
import re

try:
    import google.generativeai as genai
    GEMINI_LIB = True
except ImportError:
    GEMINI_LIB = False

from medical_data import RECOMMENDATIONS, URGENT_DISEASES

MODELS = ["gemini-3.1-flash-lite"]


def _load_key():
    """Key from environment variable OR gemini_key.txt file (foolproof)."""
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if key:
        return key
    try:
        with open("gemini_key.txt", encoding="utf-8-sig") as f:
            return f.read().strip() or None
    except FileNotFoundError:
        return None


def gemini_enabled():
    return GEMINI_LIB and bool(_load_key())

def build_prompt(profile, symptoms, custom, top3, duration, severity):
    ml = "\n".join(f"- {d}: {c}% statistical confidence" for d, c in top3) \
         or "- Undetermined (insufficient recognised symptoms)"

    return f"""You are a clinical decision-support AI operating inside an educational symptom-checker.
You MUST follow evidence-based medicine using standard clinical knowledge (WHO / CDC style guidelines).
Reason step by step like a physician performing differential diagnosis. Be precise and consistent:
the same patient data must always produce the same assessment.

===== PATIENT RECORD =====
VITALS & BODY
- Age: {profile.get('age') or 'not provided'} | Gender: {profile.get('gender') or 'not provided'}
- Height: {profile.get('height_cm') or 'not provided'} cm | Weight: {profile.get('weight_kg') or 'not provided'} kg
- BMI: {profile.get('bmi') or 'not provided'} ({profile.get('bmi_category') or 'not provided'})
- Blood group: {profile.get('blood_group') or 'not provided'} | City: {profile.get('city') or 'not provided'}
- Composite lifestyle health score: {profile.get('health_score')}/100

LIFESTYLE
- Physical activity: {profile.get('physical_activity') or 'not provided'}
- Sleep: {profile.get('sleep_hours') or 'not provided'} hours/day
- Diet type: {profile.get('diet_type') or 'not provided'}
- Smoking: {profile.get('smoking') or 'not provided'} | Alcohol: {profile.get('alcohol') or 'not provided'}
- Stress level: {profile.get('stress_level') or 'not provided'} | Occupation: {profile.get('occupation') or 'not provided'}

CURRENT ILLNESS
- Duration: {duration or 'not provided'} | Severity: {severity or 'not provided'}
- Selected symptoms: {', '.join(symptoms) if symptoms else 'none'}
- Patient-described extra symptoms: {', '.join(custom) if custom else 'none'}

MEDICAL BACKGROUND
- Past history: {profile.get('past_history') or 'none reported'}
- Family history: {profile.get('family_history') or 'none reported'}
- Allergies: {profile.get('allergies') or 'none reported'}
- Current medications: {profile.get('medications') or 'none reported'}

MACHINE LEARNING MODEL OUTPUT (statistical pattern match)
{ml}

===== YOUR TASK =====
Produce the assessment in PLAIN TEXT using EXACTLY these headings, each on its own line:

OVERALL ASSESSMENT:
CONDITION ANALYSIS:
RED FLAGS - SEE A DOCTOR IMMEDIATELY IF:
HOME CARE AND DOS AND DONTS:
PERSONALIZED DIET PLAN:
PERSONALIZED EXERCISE PLAN:
LIFESTYLE MODIFICATIONS:
SUGGESTED MEDICAL TESTS TO DISCUSS WITH A DOCTOR:
WHEN TO CONSULT A DOCTOR:
FOLLOW-UP PLAN:

STRICT RULES:
1. 2-4 bullet points per section, each bullet starts with "- ".
2. PERSONALIZED DIET PLAN must respect the patient's diet type ({profile.get('diet_type') or 'unspecified'}) and BMI category.
3. PERSONALIZED EXERCISE PLAN must match their activity level and current severity — never suggest intense exercise for Severe cases.
4. LIFESTYLE MODIFICATIONS must directly reference their actual smoking/alcohol/sleep/stress data.
5. Reference duration, severity, age and medical background in your reasoning.
6. NEVER name prescription medicines or dosages. Over-the-counter general categories only.
7. Use deterministic clinical language. No speculation, no invented statistics.
8. Maximum 300 words total."""


def get_ai_analysis(profile, symptoms, custom, top3, duration, severity):
    """Returns (analysis_text, engine_name)."""
    if gemini_enabled():
        try:
            genai.configure(api_key=_load_key())
            prompt = build_prompt(profile, symptoms, custom, top3, duration, severity)
            strict = genai.GenerationConfig(temperature=0.1, top_p=0.1, top_k=1)
            for name in MODELS:
                try:
                    resp = genai.GenerativeModel(name).generate_content(
                        prompt, generation_config=strict)
                    if resp.text and resp.text.strip():
                        return resp.text.strip(), name
                except Exception:
                    continue
        except Exception:
            pass
    return _fallback(profile, symptoms, custom, top3, duration, severity), "built-in engine"


def _fallback(profile, symptoms, custom, top3, duration, severity):
    """Deterministic rule-based analysis (used when Gemini is unavailable)."""
    if top3:
        disease, conf = top3[0]
        rec = RECOMMENDATIONS.get(disease, "Consult a doctor for proper evaluation.")
        urgent = disease in URGENT_DISEASES
        alt = ", ".join(f"{d} ({c}%)" for d, c in top3[1:])
    else:
        disease, conf, rec, urgent, alt = ("Undetermined condition", 0,
                                           "Please consult a doctor.", False, "")

    long_duration = duration in ("1-4 weeks", "More than 1 month")
    severe = severity == "Severe"
    bmi_cat = profile.get("bmi_category") or "not provided"
    act = profile.get("physical_activity") or "not provided"
    diet = profile.get("diet_type") or "general"

    L = []
    L.append("OVERALL ASSESSMENT:")
    L.append(f"- Symptom pattern most closely matches {disease} ({conf}% statistical confidence).")
    if alt:
        L.append(f"- Other possibilities: {alt}.")
    L.append(f"- Duration {duration or 'unknown'}, severity {severity or 'unknown'}; "
             f"lifestyle health score {profile.get('health_score')}/100.")

    L.append("CONDITION ANALYSIS:")
    L.append(f"- Standard guidance for {disease}: {rec}")
    if profile.get("past_history"):
        L.append(f"- Past history ({profile['past_history']}) considered in assessment.")
    if profile.get("allergies"):
        L.append(f"- Inform doctors about allergy: {profile['allergies']}.")

    L.append("RED FLAGS - SEE A DOCTOR IMMEDIATELY IF:")
    L.append("- Symptoms suddenly worsen or high fever above 103F/39.4C")
    L.append("- Difficulty breathing, persistent vomiting, confusion or fainting")
    if urgent:
        L.append(f"- {disease} is potentially serious - do not delay consultation.")

    L.append("HOME CARE AND DOS AND DONTS:")
    L.append("- Stay hydrated (water/ORS) and take adequate rest.")
    L.append("- Monitor symptoms twice daily; avoid self-medicating with antibiotics.")

    L.append("PERSONALIZED DIET PLAN:")
    if bmi_cat == "Overweight" or bmi_cat == "Obese":
        L.append(f"- Calorie-controlled {diet.lower()} diet; more fibre, less sugar and fried food (BMI: {bmi_cat}).")
    elif bmi_cat == "Underweight":
        L.append(f"- Nutrient-dense {diet.lower()} diet with extra healthy calories (nuts, dairy, bananas).")
    else:
        L.append(f"- Balanced {diet.lower()} diet with vegetables, proteins and whole grains.")
    L.append("- Eat light freshly cooked food, small frequent meals until recovery.")

    L.append("PERSONALIZED EXERCISE PLAN:")
    if severe:
        L.append("- Rest only until symptoms improve; resume activity gradually after recovery.")
    elif act == "Sedentary":
        L.append("- Start with 15-20 minutes slow walking daily, build up gradually.")
    else:
        L.append("- Continue moderate activity like walking/yoga; avoid intense workouts while ill.")

    L.append("LIFESTYLE MODIFICATIONS:")
    if profile.get("smoking") in ("Daily", "Occasionally"):
        L.append(f"- Smoking ({profile['smoking']}) slows recovery - reduce/avoid completely.")
    if profile.get("alcohol") == "Regular":
        L.append("- Regular alcohol intake should be reduced, especially during illness.")
    if profile.get("sleep_hours") and profile["sleep_hours"] < 7:
        L.append(f"- Sleep {profile['sleep_hours']}h is low - target 7-9 hours to aid recovery.")
    if profile.get("stress_level") == "High":
        L.append("- Practice 10 minutes of deep breathing daily to lower stress.")
    L.append("- Maintain hydration and a fixed sleep routine.")

    L.append("SUGGESTED MEDICAL TESTS TO DISCUSS WITH A DOCTOR:")
    L.append("- Basic blood test (CBC) plus condition-specific tests as advised.")

    L.append("WHEN TO CONSULT A DOCTOR:")
    if urgent or severe:
        L.append("- Within 24 hours.")
    elif long_duration:
        L.append("- Symptoms have persisted - schedule a visit soon.")
    else:
        L.append("- If symptoms last beyond 3-4 days or worsen.")

    L.append("FOLLOW-UP PLAN:")
    L.append("- Re-assess symptoms after 48 hours using this application.")
    L.append("- Keep a daily note of temperature and symptom changes.")
    return "\n".join(L)


def format_ai_text(text):
    """Plain-text AI output -> safe styled HTML."""
    if not text:
        return ""
    out = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        line = re.sub(r"\*+", "", line)
        line = re.sub(r"^#+\s*", "", line)
        if (line.endswith(":") and len(line) < 70) or (line.isupper() and 3 < len(line) < 70):
            out.append(f'<h6 class="ai-heading">{_html.escape(line.rstrip(":"))}</h6>')
        elif line.startswith("- "):
            out.append(f'<p class="ai-p">• {_html.escape(line[2:])}</p>')
        else:
            out.append(f'<p class="ai-p">{_html.escape(line)}</p>')
    return "\n".join(out)