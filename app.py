import os
import uuid
import requests
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_cors import CORS
from supabase import create_client, Client
from gotrue.errors import AuthApiError
from dotenv import load_dotenv
from models import db, User, About, Skill, Education, Experience, Project, Research, ContactMessage, Achievement, Blog

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-dev-key')

# ==========================================
#  SUPABASE CONFIGURATION
# ==========================================

# 1. Database Connection
uri = os.getenv('DATABASE_URL')
if uri and uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_pre_ping": True, 
    "pool_recycle": 300
}

# 2. Supabase API Credentials
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY in .env file")

# Initialize Supabase Client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Storage Bucket Name
STORAGE_BUCKET = "portfolio"

# ==========================================

CORS(app)

db.init_app(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'webp'}

# --- SUPABASE UPLOAD HELPER ---
def handle_file_upload(file, subfolder='others'):
    if not file or file.filename == '':
        return None

    original_filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4().hex[:8]}_{original_filename}"
    file_path = f"{subfolder}/{unique_filename}"
    
    content_type = file.content_type or 'application/octet-stream'

    print(f"⚡ Attempting to upload: {original_filename} to {file_path}...")

    try:
        file_content = file.read()
        res = supabase.storage.from_(STORAGE_BUCKET).upload(
            file=file_content,
            path=file_path,
            file_options={"content-type": content_type, "x-upsert": "false"}
        )
        public_url_response = supabase.storage.from_(STORAGE_BUCKET).get_public_url(file_path)
        
        print(f"✅ Upload Successful! URL: {public_url_response}")
        return public_url_response
    except Exception as e:
        print(f"❌ Supabase Upload Failed: {e}")
        return None
    finally:
        file.seek(0)

# --- SETUP / INIT ---
@app.cli.command("create-admin")
def create_admin():
    """Creates tables and registers admin in Supabase Auth."""
    with app.app_context():
        try:
            db.create_all()
            
            default_email = 'admin@example.com'
            default_password = 'admin123' # Min 6 chars for Supabase

            # 1. Register in Supabase Auth
            try:
                res = supabase.auth.sign_up({
                    "email": default_email,
                    "password": default_password
                })
                print(f"Supabase Auth: User created/fetched for {default_email}")
            except Exception as e:
                print(f"Supabase Auth Note: {e} (User likely already exists)")

            # 2. Ensure Local DB Record exists (for Flask-Login session mapping)
            if not User.query.filter_by(email=default_email).first():
                new_user = User(email=default_email, password="handled_by_supabase")
                db.session.add(new_user)
                db.session.commit()
                print("Local DB: Admin user record created.")
            
            # Ensure 'About' exists
            if not About.query.first():
                db.session.add(About(name="Your Name"))
                db.session.commit()

        except Exception as e:
            print(f"Error: {e}")

# --- AUTH ROUTES ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        try:
            # 1. Authenticate with Supabase
            auth_response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            # 2. If successful, Supabase returns a user/session
            if auth_response.user:
                # 3. Find corresponding local user for Flask-Login session
                user = User.query.filter_by(email=email).first()
                
                # Create local record if missing (sync)
                if not user:
                    user = User(email=email, password="handled_by_supabase")
                    db.session.add(user)
                    db.session.commit()
                
                # Log in via Flask-Login
                login_user(user)
                return redirect(url_for('dashboard'))
                
        except AuthApiError as e:
            flash(f"Login failed: {e.message}")
        except Exception as e:
            flash("An unexpected error occurred. Check console.")
            print(e)
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    try:
        supabase.auth.sign_out()
    except:
        pass
    logout_user()
    return redirect(url_for('login'))

# --- ADMIN DASHBOARD ROUTES ---
@app.route('/')
@app.route('/dashboard')
@login_required
def dashboard():
    active_tab = request.args.get('tab', 'messages')
    
    about = About.query.first()
    skills = Skill.query.all()
    education = Education.query.all()
    experience = Experience.query.all()
    projects = Project.query.all()
    researches = Research.query.all()
    achievements = Achievement.query.all() # <--- ADD THIS LINE
    blogs = Blog.query.all()  # <--- ADD THIS LINE
    
    messages = ContactMessage.query.order_by(ContactMessage.timestamp.desc()).all()
    unread_count = ContactMessage.query.filter_by(read=False).count()

    image_history = set()
    if about:
        if about.profile_image: image_history.add(about.profile_image)
        if about.mini_profile_image: image_history.add(about.mini_profile_image) # New
        
    for p in projects:
        if p.image_url: image_history.add(p.image_url)
    
    image_history = sorted(list(filter(None, image_history)))
    
    return render_template('dashboard.html', 
                           about=about, skills=skills, education=education, 
                           experience=experience, projects=projects, 
                           researches=researches, achievements=achievements,
                           blogs=blogs,
                           messages=messages,
                           unread_count=unread_count,
                           active_tab=active_tab,
                           image_history=image_history)

# --- API ROUTES ---

@app.route('/api/message/read/<int:id>', methods=['POST'])
@login_required
def mark_message_read(id):
    msg = ContactMessage.query.get_or_404(id)
    if not msg.read:
        msg.read = True
        db.session.commit()
    new_count = ContactMessage.query.filter_by(read=False).count()
    return jsonify({'success': True, 'unread_count': new_count})

# --- CRUD ROUTES ---

@app.route('/update/about', methods=['POST'])
@login_required
def update_about():
    about = About.query.first()
    if not about:
        about = About()
        db.session.add(about)
    
    # Basic Info
    about.name = request.form.get('name')
    about.birthday = request.form.get('birthday')
    about.website = request.form.get('website')
    about.phone = request.form.get('phone')
    about.city = request.form.get('city')
    about.age = request.form.get('age')
    about.degree = request.form.get('degree')
    about.email = request.form.get('email')
    about.freelance_status = request.form.get('freelance_status')
    about.short_bio = request.form.get('short_bio')
    about.long_bio = request.form.get('long_bio')
    
    # Social Links
    about.github = request.form.get('github')
    about.facebook = request.form.get('facebook')
    about.linkedin = request.form.get('linkedin')
    about.whatsapp = request.form.get('whatsapp')
    about.instagram = request.form.get('instagram')
    about.twitter = request.form.get('twitter')
    
    # Resume
    if request.form.get('resume_link'):
        about.resume_link = request.form.get('resume_link')
        
    if 'resume_file' in request.files:
        url = handle_file_upload(request.files['resume_file'], subfolder='resumes')
        if url: about.resume_link = url

    # 1. Main Profile Image
    if request.form.get('profile_image'):
        about.profile_image = request.form.get('profile_image')
    
    if 'image_file' in request.files:
        url = handle_file_upload(request.files['image_file'], subfolder='profile')
        if url: about.profile_image = url

    # 2. Mini Profile Image (NEW)
    if request.form.get('mini_profile_image'):
        about.mini_profile_image = request.form.get('mini_profile_image')
    
    if 'mini_image_file' in request.files:
        url = handle_file_upload(request.files['mini_image_file'], subfolder='profile')
        if url: about.mini_profile_image = url
    
    db.session.commit()
    flash('About section updated!')
    return redirect(url_for('dashboard', tab='about'))


@app.route('/add/skill', methods=['POST'])
@login_required
def add_skill():
    image_url = None
    if 'image_file' in request.files:
        url = handle_file_upload(request.files['image_file'], subfolder='skills')
        if url: image_url = url

    new_skill = Skill(
        name=request.form['name'], 
        percentage=request.form['percentage'],
        image_url=image_url
    )
    db.session.add(new_skill)
    db.session.commit()
    return redirect(url_for('dashboard', tab='skills'))

@app.route('/edit/skill/<int:id>', methods=['POST'])
@login_required
def edit_skill(id):
    skill = Skill.query.get_or_404(id)
    skill.name = request.form['name']
    skill.percentage = request.form['percentage']
    
    if 'image_file' in request.files:
        url = handle_file_upload(request.files['image_file'], subfolder='skills')
        if url: skill.image_url = url

    db.session.commit()
    flash('Skill updated successfully!')
    return redirect(url_for('dashboard', tab='skills'))

@app.route('/delete/skill/<int:id>')
@login_required
def delete_skill(id):
    Skill.query.filter_by(id=id).delete()
    db.session.commit()
    return redirect(url_for('dashboard', tab='skills'))

@app.route('/add/education', methods=['POST'])
@login_required
def add_education():
    logo_url = None
    # Handle Logo Upload
    if 'logo_file' in request.files:
        url = handle_file_upload(request.files['logo_file'], subfolder='education')
        if url: logo_url = url

    new_edu = Education(
        degree=request.form['degree'],
        institution=request.form['institution'],
        logo_url=logo_url,
        year_range=request.form['year_range'],
        description=request.form['description']
    )
    db.session.add(new_edu)
    db.session.commit()
    return redirect(url_for('dashboard', tab='education'))

@app.route('/edit/education/<int:id>', methods=['POST'])
@login_required
def edit_education(id):
    edu = Education.query.get_or_404(id)
    edu.degree = request.form['degree']
    edu.institution = request.form['institution']
    edu.year_range = request.form['year_range']
    edu.description = request.form['description']
    
    # Handle Logo Update
    if 'logo_file' in request.files:
         url = handle_file_upload(request.files['logo_file'], subfolder='education')
         if url: edu.logo_url = url
         
    db.session.commit()
    flash('Education updated successfully!')
    return redirect(url_for('dashboard', tab='education'))

@app.route('/delete/education/<int:id>')
@login_required
def delete_education(id):
    Education.query.filter_by(id=id).delete()
    db.session.commit()
    return redirect(url_for('dashboard', tab='education'))

@app.route('/add/experience', methods=['POST'])
@login_required
def add_experience():
    new_exp = Experience(
        role=request.form['role'],
        company=request.form['company'],
        year_range=request.form['year_range'],
        description=request.form['description']
    )
    db.session.add(new_exp)
    db.session.commit()
    return redirect(url_for('dashboard', tab='experience'))

@app.route('/delete/experience/<int:id>')
@login_required
def delete_experience(id):
    Experience.query.filter_by(id=id).delete()
    db.session.commit()
    return redirect(url_for('dashboard', tab='experience'))

@app.route('/edit/experience/<int:id>', methods=['POST'])
@login_required
def edit_experience(id):
    exp = Experience.query.get_or_404(id)
    exp.role = request.form['role']
    exp.company = request.form['company']
    exp.year_range = request.form['year_range']
    exp.description = request.form['description']
    db.session.commit()
    flash('Experience updated successfully!')
    return redirect(url_for('dashboard', tab='experience'))

@app.route('/add/project', methods=['POST'])
@login_required
def add_project():
    image_url = request.form.get('image_url')
    
    if 'image_file' in request.files:
        uploaded_url = handle_file_upload(request.files['image_file'], subfolder='projects')
        if uploaded_url: image_url = uploaded_url

    new_proj = Project(
        title=request.form['title'],
        category=request.form['category'],
        image_url=image_url,
        project_link=request.form['project_link']
    )
    db.session.add(new_proj)
    db.session.commit()
    return redirect(url_for('dashboard', tab='projects'))

@app.route('/delete/project/<int:id>')
@login_required
def delete_project(id):
    Project.query.filter_by(id=id).delete()
    db.session.commit()
    return redirect(url_for('dashboard', tab='projects'))

@app.route('/edit/project/<int:id>', methods=['POST'])
@login_required
def edit_project(id):
    proj = Project.query.get_or_404(id)
    proj.title = request.form['title']
    proj.category = request.form['category']
    proj.project_link = request.form['project_link']
    
    if request.form.get('image_url'):
        proj.image_url = request.form.get('image_url')
        
    if 'image_file' in request.files:
        uploaded_url = handle_file_upload(request.files['image_file'], subfolder='projects')
        if uploaded_url: proj.image_url = uploaded_url

    db.session.commit()
    flash('Project updated successfully!')
    return redirect(url_for('dashboard', tab='projects'))

@app.route('/add/research', methods=['POST'])
@login_required
def add_research():
    link = request.form.get('link')

    if 'research_pdf' in request.files:
        uploaded_link = handle_file_upload(request.files['research_pdf'], subfolder='research')
        if uploaded_link: link = uploaded_link

    new_research = Research(
        title=request.form['title'],
        description=request.form['description'],
        link=link,
        publication_date=request.form['publication_date']
    )
    db.session.add(new_research)
    db.session.commit()
    return redirect(url_for('dashboard', tab='research'))

@app.route('/delete/research/<int:id>')
@login_required
def delete_research(id):
    Research.query.filter_by(id=id).delete()
    db.session.commit()
    return redirect(url_for('dashboard', tab='research'))

@app.route('/edit/research/<int:id>', methods=['POST'])
@login_required
def edit_research(id):
    research = Research.query.get_or_404(id)
    research.title = request.form['title']
    research.publication_date = request.form['publication_date']
    research.link = request.form['link']
    research.description = request.form['description']
    
    if 'research_pdf' in request.files:
        uploaded_link = handle_file_upload(request.files['research_pdf'], subfolder='research')
        if uploaded_link: research.link = uploaded_link

    db.session.commit()
    flash('Research updated successfully!')
    return redirect(url_for('dashboard', tab='research'))

# --- ACHIEVEMENT ROUTES ---

@app.route('/add/achievement', methods=['POST'])
@login_required
def add_achievement():
    new_ach = Achievement(
        title=request.form['title'],
        description=request.form['description'],
        date=request.form['date'],
        link=request.form['link']
    )
    db.session.add(new_ach)
    db.session.commit()
    return redirect(url_for('dashboard', tab='achievements'))

@app.route('/delete/achievement/<int:id>')
@login_required
def delete_achievement(id):
    Achievement.query.filter_by(id=id).delete()
    db.session.commit()
    return redirect(url_for('dashboard', tab='achievements'))

@app.route('/edit/achievement/<int:id>', methods=['POST'])
@login_required
def edit_achievement(id):
    ach = Achievement.query.get_or_404(id)
    ach.title = request.form['title']
    ach.description = request.form['description']
    ach.date = request.form['date']
    ach.link = request.form['link']
    db.session.commit()
    flash('Achievement updated successfully!')
    return redirect(url_for('dashboard', tab='achievements'))


# BLOG (New)
@app.route('/add/blog', methods=['POST'])
@login_required
def add_blog():
    cover_image = None
    if 'cover_file' in request.files:
        url = handle_file_upload(request.files['cover_file'], subfolder='blog')
        if url: cover_image = url

    new_blog = Blog(
        title=request.form['title'],
        content=request.form['content'],
        tags=request.form['tags'],
        date=request.form['date'],
        cover_image=cover_image
    )
    db.session.add(new_blog)
    db.session.commit()
    return redirect(url_for('dashboard', tab='blog'))

@app.route('/delete/blog/<int:id>')
@login_required
def delete_blog(id):
    Blog.query.filter_by(id=id).delete()
    db.session.commit()
    return redirect(url_for('dashboard', tab='blog'))

@app.route('/edit/blog/<int:id>', methods=['POST'])
@login_required
def edit_blog(id):
    blog = Blog.query.get_or_404(id)
    blog.title = request.form['title']
    blog.content = request.form['content']
    blog.tags = request.form['tags']
    blog.date = request.form['date']
    
    if 'cover_file' in request.files:
        url = handle_file_upload(request.files['cover_file'], subfolder='blog')
        if url: blog.cover_image = url

    db.session.commit()
    flash('Blog updated successfully!')
    return redirect(url_for('dashboard', tab='blog'))


# --- PUBLIC API ENDPOINTS ---

@app.route('/api/about', methods=['GET'])
def get_about():
    about = About.query.first()
    return jsonify(about.to_dict() if about else {})

@app.route('/api/skills', methods=['GET'])
def get_skills():
    skills = Skill.query.all()
    return jsonify([s.to_dict() for s in skills])

@app.route('/api/education', methods=['GET'])
def get_education():
    education = Education.query.all()
    return jsonify([e.to_dict() for e in education])

@app.route('/api/experience', methods=['GET'])
def get_experience():
    experience = Experience.query.all()
    return jsonify([e.to_dict() for e in experience])

@app.route('/api/projects', methods=['GET'])
def get_projects():
    projects = Project.query.all()
    return jsonify([p.to_dict() for p in projects])

@app.route('/api/research', methods=['GET'])
def get_research():
    research = Research.query.all()
    return jsonify([t.to_dict() for t in research])

@app.route('/api/achievements', methods=['GET'])
def get_achievements():
    achievements = Achievement.query.all()
    return jsonify([a.to_dict() for a in achievements])

@app.route('/api/blogs', methods=['GET'])
def get_blogs():
    blogs = Blog.query.all()
    return jsonify([b.to_dict() for b in blogs])

@app.route('/api/contact', methods=['POST'])
def api_contact():
    data = request.json or request.form
    if not data: return jsonify({"error": "No data provided"}), 400
    new_msg = ContactMessage(
        name=data.get('name'),
        email=data.get('email'),
        subject=data.get('subject'),
        message=data.get('message')
    )
    db.session.add(new_msg)
    db.session.commit()
    return jsonify({"success": True, "message": "Message sent successfully!"}), 201

if __name__ == '__main__':
    app.run(debug=True)