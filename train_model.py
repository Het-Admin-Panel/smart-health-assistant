"""
train_model.py — Smart Health Assistant
Trains the disease prediction model from dataset.csv.
Run this BEFORE app.py:   python train_model.py
Outputs: model.pkl (model + symptom vocabulary) and model_metrics.txt (for your report)
"""

import pickle
from itertools import combinations

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MultiLabelBinarizer


def build_training_data():
    """Reads dataset.csv and builds the training set.

    DATA AUGMENTATION: for every disease row we also create samples
    with 1 or 2 symptoms removed. This teaches the model to recognise
    diseases even when the user reports only PART of the symptoms —
    exactly what happens in real usage.
    """
    df = pd.read_csv("dataset.csv")
    symptom_cols = [c for c in df.columns if c.startswith("Symptom")]

    rows = []
    for _, r in df.iterrows():
        disease = str(r["Disease"]).strip()
        symptoms = [str(s).strip().lower() for s in r[symptom_cols].tolist()
                    if pd.notna(s)]

        rows.append((disease, symptoms))                     # full symptom set
        for k in (1, 2):                                     # partial sets
            if len(symptoms) > k:
                for drop in combinations(range(len(symptoms)), k):
                    subset = [s for i, s in enumerate(symptoms) if i not in drop]
                    rows.append((disease, subset))

    return pd.DataFrame(rows, columns=["Disease", "Symptoms"])


def main():
    data = build_training_data()
    print(f"Training samples : {len(data)}")
    print(f"Diseases covered : {data['Disease'].nunique()}")

    # One-hot encode the multi-symptom lists into binary feature vectors
    mlb = MultiLabelBinarizer()
    X = mlb.fit_transform(data["Symptoms"])
    y = data["Disease"]
    print(f"Feature vector   : {X.shape[1]} symptoms (one-hot encoded)")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # RandomForest: handles multiclass + non-linear symptom patterns well,
    # gives probability scores, and is robust on small datasets.
    model = RandomForestClassifier(n_estimators=200, random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred) * 100
    print(f"Test accuracy    : {accuracy:.2f}%")

    # Save metrics — paste these numbers into your report (Chapter 7)
    with open("model_metrics.txt", "w") as f:
        f.write(f"Accuracy: {accuracy:.2f}%\n\n")
        f.write(classification_report(y_test, y_pred, zero_division=0))

    # Save model + symptom vocabulary for the web app
    with open("model.pkl", "wb") as f:
        pickle.dump({"model": model, "symptoms": mlb.classes_}, f)

    print("Saved: model.pkl, model_metrics.txt")


if __name__ == "__main__":
    main()