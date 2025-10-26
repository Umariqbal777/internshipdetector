import joblib
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
from sklearn.feature_extraction.text import TfidfVectorizer
import ast
import random

app = Flask(__name__)
app.secret_key = "secret123"  # for session storage

# -------------------- In-memory User Database --------------------
# NOTE: This is for demonstration only. A real application would use a database.
users = {'user': 'pass'}

# -------------------- Load Data and Model --------------------
try:
    model = joblib.load("internshipmodel.pkl")
except FileNotFoundError:
    model = None
    print("⚠️ internshipmodel.pkl not found. Predictions won't work.")

try:
    df = pd.read_csv("internships.csv")
    df['required_skills'] = df['required_skills'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else [])
except FileNotFoundError:
    df = pd.DataFrame()
    print("⚠️ internships.csv not found. No internships will be available.")

# -------------------- Vectorizer Setup --------------------
if not df.empty:
    df["text_features"] = (
        df["title"].astype(str) + " " +
        df["sector"].astype(str) + " " +
        df["required_skills"].astype(str) + " " +
        df["education_required"].astype(str) + " " +
        df["location"].astype(str)
    )
    vectorizer = TfidfVectorizer(stop_words="english", max_features=1000)
    vectorizer.fit(df["text_features"])
else:
    vectorizer = None

# -------------------- Decorator for Auth --------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session or session['username'] not in users:
            flash("Please log in to access this page.", "info")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# -------------------- Routes --------------------
@app.route("/")
def login():
    return render_template("login.html")

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/do_register", methods=["POST"])
def do_register():
    username = request.form.get("username")
    password = request.form.get("password")

    if username in users:
        flash("Username already exists. Please choose a different one.", "error")
        return redirect(url_for("register"))
    
    users[username] = password
    flash("Registration successful! Please log in.", "success")
    return redirect(url_for("login"))

@app.route("/login", methods=["POST"])
def do_login():
    username = request.form.get("username")
    password = request.form.get("password")

    if username in users and users[username] == password:
        session['username'] = username
        flash("Login successful! Welcome to the PM Internship Scheme.", "success")
        return redirect(url_for("home"))
    else:
        flash("Invalid username or password.", "error")
        return redirect(url_for("login"))

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))

@app.route("/home")
@login_required
def home():
    return render_template("index.html")

@app.route("/predict", methods=["GET", "POST"])
@login_required
def predict():
    if request.method == "POST":
        if model is None or df.empty or vectorizer is None:
            flash("Model or data not loaded. Cannot make recommendations.", "error")
            return redirect(url_for("home"))

        try:
            education = request.form.get("education", "")
            skills = request.form.get("skills", "")
            sector_interest = request.form.get("sector_interest", "")
            location_interest = request.form.get("location_interest", "")
            
            user_input_text = f"{sector_interest} {skills} {education} {location_interest}"
            
            X_user = vectorizer.transform([user_input_text])
            predicted_sector = model.predict(X_user)[0]
            
            recommended_internships = df[df["sector"] == predicted_sector].to_dict('records')
            
            random.shuffle(recommended_internships)
            recommendations_to_show = recommended_internships[:5]
            
            session["recommendations"] = recommendations_to_show
            session["saved"] = session.get("saved", [])

            current_rec = session["recommendations"].pop(0) if session["recommendations"] else None
            session.modified = True
            
            return render_template("recommendations.html", recommendation=current_rec)

        except Exception as e:
            flash(f"An error occurred: {e}", "error")
            return redirect(url_for("home"))
    
    sectors = sorted(df['sector'].unique().tolist())
    locations = sorted(df['location'].unique().tolist())
    return render_template("predict.html", sectors=sectors, locations=locations)

@app.route("/next_recommendation", methods=["POST"])
@login_required
def next_recommendation():
    action = request.form.get('action')
    
    if action == 'like':
        internship = {
            "title": request.form.get("title"),
            "sector": request.form.get("sector"),
            "location": request.form.get("location"),
            "duration": request.form.get("duration"),
            "stipend": request.form.get("stipend")
        }
        if internship not in session["saved"]:
            session["saved"].append(internship)
            flash(f"Saved: {internship['title']}", "success")
            session.modified = True
    
    remaining_recs = session.get("recommendations", [])
    current_rec = remaining_recs.pop(0) if remaining_recs else None
    
    session["recommendations"] = remaining_recs
    session.modified = True

    if current_rec:
        return render_template("recommendations.html", recommendation=current_rec)
    else:
        flash("You've viewed all the recommendations for now!", "info")
        return render_template("recommendations.html", recommendation=None)

@app.route("/shortlist")
@login_required
def shortlist():
    saved_internships = session.get("saved", [])
    return render_template("shortlist.html", saved=saved_internships)

@app.route("/remove_saved", methods=["POST"])
@login_required
def remove_saved():
    title = request.form["internship"]
    if "saved" in session:
        session["saved"] = [i for i in session["saved"] if i["title"] != title]
        session.modified = True
    return redirect(url_for("shortlist"))

@app.route("/apply", methods=["POST"])
@login_required
def apply():
    internship = request.form["internship"]
    flash(f"Redirecting to Apply page for {internship}...", "info")
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)