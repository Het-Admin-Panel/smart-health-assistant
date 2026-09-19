"""medical_data.py — medical knowledge base
Keeps recommendations, urgency list and disease→specialist mapping
in one place (used by app.py AND ai_doctor.py)."""

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

URGENT_DISEASES = {
    "Dengue", "Malaria", "Typhoid", "Hepatitis A", "Pneumonia",
    "Tuberculosis", "Appendicitis", "Kidney Stone", "COVID-19", "Measles",
}

SPECIALIST_MAP = {
    "Migraine": "Neurologist", "Influenza": "General Physician",
    "Common Cold": "General Physician", "Dengue": "Infectious Disease Specialist",
    "Malaria": "Infectious Disease Specialist", "Typhoid": "Infectious Disease Specialist",
    "Hepatitis A": "Gastroenterologist", "Pneumonia": "Pulmonologist",
    "Tuberculosis": "Pulmonologist", "Asthma": "Pulmonologist",
    "Bronchitis": "Pulmonologist", "Sinusitis": "ENT Specialist",
    "Gastroenteritis": "Gastroenterologist", "Food Poisoning": "Gastroenterologist",
    "Appendicitis": "General Surgeon", "Gastritis": "Gastroenterologist",
    "Peptic Ulcer": "Gastroenterologist", "GERD": "Gastroenterologist",
    "Urinary Tract Infection": "Urologist", "Kidney Stone": "Urologist",
    "Diabetes": "Endocrinologist", "Hypertension": "Cardiologist",
    "Anemia": "General Physician", "Hypothyroidism": "Endocrinologist",
    "Arthritis": "Rheumatologist", "Chickenpox": "Dermatologist",
    "Measles": "General Physician", "Conjunctivitis": "Ophthalmologist",
    "Eczema": "Dermatologist", "Psoriasis": "Dermatologist",
    "Fungal Skin Infection": "Dermatologist", "Anxiety Disorder": "Psychiatrist",
    "Depression": "Psychiatrist", "Insomnia": "Neurologist",
    "COVID-19": "General Physician", "Allergic Rhinitis": "ENT Specialist",
    "Dehydration": "General Physician", "Vertigo": "ENT Specialist",
    "Hemorrhoids": "General Surgeon", "Tonsillitis": "ENT Specialist",
    "Ear Infection": "ENT Specialist", "Tooth Infection": "Dentist",
    "Acne": "Dermatologist",
}


def get_specialists(disease):
    """Returns a list of doctor recommendations for a predicted disease."""
    if not disease or disease == "Undetermined":
        return [{"specialty": "General Physician",
                 "reason": "General check-up and initial assessment",
                 "urgency": "Within 2-3 days"}]

    urgent = disease in URGENT_DISEASES
    spec = SPECIALIST_MAP.get(disease, "General Physician")
    docs = []

    if urgent:
        docs.append({"specialty": "Emergency Room / Hospital",
                     "reason": f"{disease} may worsen quickly and needs prompt evaluation",
                     "urgency": "Immediately"})
    docs.append({"specialty": "General Physician",
                 "reason": "First consultation, initial tests and referral if needed",
                 "urgency": "Within 24 hours" if urgent else "Within 2-3 days"})
    if spec != "General Physician":
        docs.append({"specialty": spec,
                     "reason": f"Specialised management for {disease}",
                     "urgency": "Within 24-48 hours" if urgent else "Within a week"})
    return docs