import joblib
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
from sklearn.feature_extraction.text import TfidfVectorizer
import ast
import random

app = Flask(__name__)
app.secret_key = "secret123"

# -------------------- Language Configuration --------------------
LANGUAGES = {
    'en': {
        'title': 'PM Internship Scheme',
        'login_heading': 'Login',
        'register_link': 'Register',
        'login_button': 'Log In',
        'logout_button': 'Log out',
        'home_link': 'Home',
        'predict_link': 'Find Internships',
        'shortlist_link': 'Shortlist',
        'welcome_message': 'Welcome',
        'home_slogan': 'Find your perfect internship and jumpstart your career.',
        'start_search_button': 'Start a Search!',
        'predict_heading': 'Filter Internships',
        'predict_slogan': "Tell us what you're looking for to find the best matches.",
        'education_label': 'Education Level',
        'skills_label': 'Skills',
        'sector_label': 'Sector',
        'location_label': 'Location',
        'skills_placeholder': 'e.g., Python, Data Science, Marketing',
        'find_button': 'Find Internships',
        'school_option': 'School',
        'college_option': 'College',
        'post_grad_option': 'Post Graduation',
        'any_option': 'Any',
        'duration_label': 'Duration',
        'stipend_label': 'Stipend',
        'months_text': 'months',
        'like_label': 'LIKE',
        'nope_label': 'NOPE',
        'no_more_recs': "You've viewed all the recommendations for now!",
        'no_more_recs_msg': "Start a new search to find more!",
        'shortlist_heading': 'Your Saved Internships',
        'apply_button': 'Apply',
        'remove_button': 'Remove',
        'no_shortlist_msg': 'You have not saved any internships yet.',
        'start_shortlist_msg': 'Start a search and like internships to add them here!'
    },
    'hi': {
        'title': 'पीएम इंटर्नशिप योजना',
        'login_heading': 'लॉग इन',
        'register_link': 'रजिस्टर',
        'login_button': 'लॉग इन करें',
        'logout_button': 'लॉग आउट',
        'home_link': 'होम',
        'predict_link': 'इंटर्नशिप खोजें',
        'shortlist_link': 'शॉर्टलिस्ट',
        'welcome_message': 'स्वागत है',
        'home_slogan': 'अपनी पसंदीदा इंटर्नशिप ढूंढें और अपने करियर की शुरुआत करें।',
        'start_search_button': 'खोज शुरू करें!',
        'predict_heading': 'इंटर्नशिप फ़िल्टर करें',
        'predict_slogan': 'सबसे अच्छे मैच ढूंढने के लिए हमें बताएं कि आप क्या खोज रहे हैं।',
        'education_label': 'शिक्षा का स्तर',
        'skills_label': 'कौशल',
        'sector_label': 'क्षेत्र',
        'location_label': 'स्थान',
        'skills_placeholder': 'जैसे: पायथन, डेटा साइंस, मार्केटिंग',
        'find_button': 'इंटर्नशिप खोजें',
        'school_option': 'स्कूल',
        'college_option': 'कॉलेज',
        'post_grad_option': 'स्नातकोत्तर',
        'any_option': 'कोई भी',
        'duration_label': 'अवधि',
        'stipend_label': 'स्टाइपेंड',
        'months_text': 'महीने',
        'like_label': 'पसंद करें',
        'nope_label': 'नापसंद करें',
        'no_more_recs': 'आपने अभी के लिए सभी सिफारिशें देख ली हैं!',
        'no_more_recs_msg': 'और अधिक खोजने के लिए एक नई खोज शुरू करें!',
        'shortlist_heading': 'आपकी सहेजी गई इंटर्नशिप',
        'apply_button': 'आवेदन करें',
        'remove_button': 'हटाएं',
        'no_shortlist_msg': 'आपने अभी तक कोई इंटर्नशिप सहेजी नहीं है।',
        'start_shortlist_msg': 'एक खोज शुरू करें और उन्हें यहां जोड़ने के लिए इंटर्नशिप पसंद करें!'
    },
    'mr': {
        'title': 'पीएम इंटर्नशिप योजना',
        'login_heading': 'लॉगिन',
        'register_link': 'नोंदणी करा',
        'login_button': 'लॉगिन करा',
        'logout_button': 'लॉगआउट',
        'home_link': 'मुख्यपृष्ठ',
        'predict_link': 'इंटर्नशिप शोधा',
        'shortlist_link': 'शॉर्टलिस्ट',
        'welcome_message': 'स्वागत आहे',
        'home_slogan': 'तुमची योग्य इंटर्नशिप शोधा आणि तुमच्या करिअरची सुरुवात करा.',
        'start_search_button': 'शोध सुरू करा!',
        'predict_heading': 'इंटर्नशिप फिल्टर करा',
        'predict_slogan': 'सर्वोत्तम जुळणारे शोधण्यासाठी तुम्ही काय शोधत आहात ते आम्हाला सांगा.',
        'education_label': 'शिक्षणाचे स्तर',
        'skills_label': 'कौशल्ये',
        'sector_label': 'क्षेत्र',
        'location_label': 'स्थान',
        'skills_placeholder': 'उदा. पायथन, डेटा सायन्स, मार्केटिंग',
        'find_button': 'इंटर्नशिप शोधा',
        'school_option': 'शाळा',
        'college_option': 'महाविद्यालय',
        'post_grad_option': 'पदव्युत्तर',
        'any_option': 'कोणतेही',
        'duration_label': 'कालावधी',
        'stipend_label': 'मानधन',
        'months_text': 'महिने',
        'like_label': 'आवडले',
        'nope_label': 'नाही',
        'no_more_recs': 'तुम्ही आतापर्यंत सर्व शिफारसी पाहिल्या आहेत!',
        'no_more_recs_msg': 'अधिक शोधण्यासाठी नवीन शोध सुरू करा!',
        'shortlist_heading': 'तुमच्या जतन केलेल्या इंटर्नशिप',
        'apply_button': 'अर्ज करा',
        'remove_button': 'काढून टाका',
        'no_shortlist_msg': 'तुम्ही अद्याप कोणतीही इंटर्नशिप जतन केलेली नाही.',
        'start_shortlist_msg': 'एक शोध सुरू करा आणि त्यांना येथे जोडण्यासाठी इंटर्नशिप लाइक करा!'
    }
}
AVAILABLE_LANGS = [{'code': 'en', 'name': 'English'}, {'code': 'hi', 'name': 'Hindi'}, {'code': 'mr', 'name': 'Marathi'}]

# -------------------- In-memory User Database --------------------
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

# -------------------- Context Processor for Translations --------------------
@app.context_processor
def inject_translations():
    lang_code = session.get('lang', 'en')
    translations = LANGUAGES.get(lang_code, LANGUAGES['en'])
    return {'_': translations, 'current_lang': lang_code, 'available_langs': AVAILABLE_LANGS}

# -------------------- New Route for Language Switching --------------------
@app.route('/set_language/<lang_code>')
def set_language(lang_code):
    if lang_code in LANGUAGES:
        session['lang'] = lang_code
    return redirect(request.referrer or url_for('login'))

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
        # Flash messages are not translated dynamically in the template, so you need to provide the translation here.
        flash(f"{LANGUAGES[session.get('lang', 'en')]['welcome_message']} to the PM Internship Scheme!", "success")
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
    return render_template("home.html")

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
            # You would also need to translate this flash message.
            flash(f"Saved: {internship['title']}", "success")
            session.modified = True
    
    remaining_recs = session.get("recommendations", [])
    current_rec = remaining_recs.pop(0) if remaining_recs else None
    
    session["recommendations"] = remaining_recs
    session.modified = True

    if current_rec:
        return render_template("recommendations.html", recommendation=current_rec)
    else:
        # And this one too.
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
    # And this one...
    flash(f"Redirecting to Apply page for {internship}...", "info")
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)