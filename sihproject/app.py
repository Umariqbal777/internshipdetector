import joblib
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
from sklearn.feature_extraction.text import TfidfVectorizer
import ast
import random
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secret123"

# -------------------- Database Configuration --------------------
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# -------------------- User Database Models --------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    shortlisted_internships = db.relationship('ShortlistedInternship', backref='user', lazy='dynamic', cascade="all, delete-orphan")
    preferences = db.relationship('UserPreferences', backref='user', uselist=False, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class ShortlistedInternship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    sector = db.Column(db.String(100), nullable=True)
    location = db.Column(db.String(100), nullable=True)
    duration = db.Column(db.String(50), nullable=True)
    stipend = db.Column(db.String(50), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class UserPreferences(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    education = db.Column(db.String(100))
    skills = db.Column(db.String(255))
    sector = db.Column(db.String(100))
    location = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True)

# -------------------- Language Configuration --------------------
LANGUAGES = {
    'en': {
        'title': 'PM Internship Scheme',
        'login_heading': 'Login',
        'register_link': 'Register',
        'login_button': 'Log In',
        'logout_button': 'Log out',
        'home_link': 'Home',
        'dashboard_link': 'Dashboard',
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
        'dashboard_link': 'डैशबोर्ड',
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
        'dashboard_link': 'डॅशबोर्ड',
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
        if 'username' not in session:
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

    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        flash("Username already exists. Please choose a different one.", "error")
        return redirect(url_for("register"))
    
    new_user = User(username=username)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()
    
    flash("Registration successful! Please log in.", "success")
    return redirect(url_for("login"))

@app.route("/login", methods=["POST"])
def do_login():
    username = request.form.get("username")
    password = request.form.get("password")

    user = User.query.filter_by(username=username).first()
    
    if user and user.check_password(password):
        session['username'] = username
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

@app.route("/dashboard")
@login_required
def dashboard():
    user = User.query.filter_by(username=session['username']).first()
    preferences = UserPreferences.query.filter_by(user_id=user.id).first()
    
    # Get the count of saved internships for the user
    shortlist_count = ShortlistedInternship.query.filter_by(user_id=user.id).count()

    return render_template("dashboard.html", 
                           user=user, 
                           preferences=preferences, 
                           shortlist_count=shortlist_count)

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

            user = User.query.filter_by(username=session['username']).first()
            preferences = UserPreferences.query.filter_by(user_id=user.id).first()
            
            if preferences:
                preferences.education = education
                preferences.skills = skills
                preferences.sector = sector_interest
                preferences.location = location_interest
            else:
                new_preferences = UserPreferences(
                    education=education,
                    skills=skills,
                    sector=sector_interest,
                    location=location_interest,
                    user=user
                )
                db.session.add(new_preferences)
            
            db.session.commit()
            
            user_input_text = f"{sector_interest} {skills} {education} {location_interest}"
            
            X_user = vectorizer.transform([user_input_text])
            predicted_sector = model.predict(X_user)[0]
            
            recommended_internships = df[df["sector"] == predicted_sector].to_dict('records')
            
            random.shuffle(recommended_internships)
            recommendations_to_show = recommended_internships[:5]
            
            session["recommendations"] = recommendations_to_show
            session.modified = True
            
            current_rec = session["recommendations"].pop(0) if session["recommendations"] else None
            session.modified = True
            
            return render_template("recommendations.html", recommendation=current_rec)

        except Exception as e:
            flash(f"An error occurred: {e}", "error")
            return redirect(url_for("home"))
    
    # --- Code for GET request ---
    else:
        user = User.query.filter_by(username=session['username']).first()
        preferences = UserPreferences.query.filter_by(user_id=user.id).first()
        
        sectors = sorted(df['sector'].unique().tolist())
        locations = sorted(df['location'].unique().tolist())
        
        return render_template("predict.html", 
                               sectors=sectors, 
                               locations=locations, 
                               preferences=preferences)

@app.route("/next_recommendation", methods=["POST"])
@login_required
def next_recommendation():
    action = request.form.get('action')
    
    if action == 'like':
        user = User.query.filter_by(username=session['username']).first()
        
        new_shortlist_item = ShortlistedInternship(
            title=request.form.get("title"),
            sector=request.form.get("sector"),
            location=request.form.get("location"),
            duration=request.form.get("duration"),
            stipend=request.form.get("stipend"),
            user_id=user.id
        )
        
        db.session.add(new_shortlist_item)
        db.session.commit()
        
        flash(f"Saved: {request.form.get('title')}", "success")
    
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
    user = User.query.filter_by(username=session['username']).first()
    
    saved_internships = ShortlistedInternship.query.filter_by(user_id=user.id).all()
    
    return render_template("shortlist.html", saved=saved_internships)

@app.route("/remove_saved", methods=["POST"])
@login_required
def remove_saved():
    title = request.form["internship"]
    user = User.query.filter_by(username=session['username']).first()
    
    item_to_remove = ShortlistedInternship.query.filter_by(user_id=user.id, title=title).first()
    
    if item_to_remove:
        db.session.delete(item_to_remove)
        db.session.commit()
    
    return redirect(url_for("shortlist"))

@app.route("/apply", methods=["POST"])
@login_required
def apply():
    internship = request.form["internship"]
    flash(f"Redirecting to Apply page for {internship}...", "info")
    return redirect(url_for("home"))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)