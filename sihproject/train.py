# internship_model_training.py

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.svm import SVC
import pickle

# -----------------------------
# STEP 1: Load Data
# -----------------------------
df = pd.read_csv("internships.csv")

# Convert skills list into string if needed
df["required_skills"] = df["required_skills"].astype(str)

# -----------------------------
# STEP 2: Feature Engineering
# -----------------------------
# Combine internship fields into text
df["text_features"] = (
    df["title"].astype(str) + " " +
    df["sector"].astype(str) + " " +
    df["required_skills"].astype(str) + " " +
    df["education_required"].astype(str) + " " +
    df["location"].astype(str)
)

# Vectorize text
vectorizer = TfidfVectorizer(stop_words="english", max_features=1000)
X = vectorizer.fit_transform(df["text_features"])

# ⚠️ NOTE: You don’t have real labels (y) → for demo, we simulate
# Example: predict "sector" as a classification problem
y = df["sector"]

# -----------------------------
# STEP 3: Train/Test Split
# -----------------------------
x_train, x_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# -----------------------------
# STEP 4: Train Multiple Models
# -----------------------------
results = []

# Logistic Regression
lr = LogisticRegression(max_iter=500)
lr.fit(x_train, y_train)
y_pred = lr.predict(x_test)
results.append(("Logistic Regression", accuracy_score(y_test, y_pred)))
print("Logistic Regression:\n", classification_report(y_test, y_pred))

# Decision Tree
dt = DecisionTreeClassifier()
dt.fit(x_train, y_train)
y_pred = dt.predict(x_test)
results.append(("Decision Tree", accuracy_score(y_test, y_pred)))
print("Decision Tree:\n", classification_report(y_test, y_pred))

# Random Forest
rf = RandomForestClassifier()
rf.fit(x_train, y_train)
y_pred = rf.predict(x_test)
results.append(("Random Forest", accuracy_score(y_test, y_pred)))
print("Random Forest:\n", classification_report(y_test, y_pred))

# Naive Bayes
nb = GaussianNB()
nb.fit(x_train.toarray(), y_train)  # needs dense input
y_pred = nb.predict(x_test.toarray())
results.append(("Naive Bayes", accuracy_score(y_test, y_pred)))
print("Naive Bayes:\n", classification_report(y_test, y_pred))

# SVM
svc = SVC()
svc.fit(x_train, y_train)
y_pred = svc.predict(x_test)
results.append(("SVM", accuracy_score(y_test, y_pred)))
print("SVM:\n", classification_report(y_test, y_pred))

# Gradient Boosting
gbc = GradientBoostingClassifier()
gbc.fit(x_train.toarray(), y_train)  # GBC may require dense input
y_pred = gbc.predict(x_test.toarray())
results.append(("Gradient Boosting", accuracy_score(y_test, y_pred)))
print("Gradient Boosting:\n", classification_report(y_test, y_pred))

# -----------------------------
# STEP 5: Pick Best Model
# -----------------------------
results_df = pd.DataFrame(results, columns=["Model", "Accuracy"])
print("\nModel Comparison:\n", results_df)

best_model_name, best_acc = max(results, key=lambda x: x[1])
print(f"\nBest Model: {best_model_name} with accuracy {best_acc:.4f}")

# Save the best model
best_model = {
    "Logistic Regression": lr,
    "Decision Tree": dt,
    "Random Forest": rf,
    "Naive Bayes": nb,
    "SVM": svc,
    "Gradient Boosting": gbc
}[best_model_name]

pickle.dump(best_model, open("internshipmodel.pkl", "wb"))
print("✅ Model saved as internshipmodel.pkl")
