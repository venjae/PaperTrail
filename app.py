import os
import secrets
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
from flask import Flask, jsonify, request, render_template, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_dance.contrib.google import make_google_blueprint, google

if not os.path.exists('logs'):
    os.makedirs('logs')

logging.basicConfig(
    level=logging.DEBUG,
    handlers=[
        RotatingFileHandler('logs/app.log', maxBytes=10000000, backupCount=5),
        logging.StreamHandler()
    ],
    format='%(asctime)s | %(levelname)-8s | %(module)s:%(lineno)d | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# Use SQLite locally, PostgreSQL on Railway
database_url = os.environ.get('DATABASE_URL', 'sqlite:///tracker.db')
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Fix PostgreSQL URL format for Railway
if database_url and database_url.startswith('postgres://'):
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url.replace('postgres://', 'postgresql://', 1)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# OAuth Configuration (set these in environment variables)
google_bp = make_google_blueprint(
    client_id=os.environ.get('GOOGLE_CLIENT_ID', ''),
    client_secret=os.environ.get('GOOGLE_CLIENT_SECRET', ''),
    scope=['profile', 'email'],
    redirect_to='oauth_callback'
)
app.register_blueprint(google_bp, url_prefix='/login/google')

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(256), nullable=True)
    name = db.Column(db.String(100), nullable=True)
    oauth_provider = db.Column(db.String(20), nullable=True)
    oauth_id = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    courses = db.relationship('Course', backref='user', lazy=True, cascade='all, delete-orphan')
    assignments = db.relationship('Assignment', backref='user', lazy=True, cascade='all, delete-orphan')

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    color = db.Column(db.String(7), default='#808080')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    assignments = db.relationship('Assignment', backref='course', lazy=True, cascade='all, delete-orphan')

class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    due_date = db.Column(db.DateTime, nullable=False)
    priority = db.Column(db.String(10), default='medium')
    status = db.Column(db.String(20), default='pending')
    notes = db.Column(db.Text, default='')
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Request logging middleware
@app.after_request
def log_response(response):
    logging.info(f"Request: {request.method} {request.path} | Response: {response.status_code} | IP: {request.remote_addr}")
    return response

# Auth routes
@app.route('/login')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('register'))
        
        from werkzeug.security import generate_password_hash
        user = User(email=email, password_hash=generate_password_hash(password), name=name)
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        return redirect(url_for('index'))
    
    return render_template('register.html')

@app.route('/login/email', methods=['POST'])
def login_email():
    from werkzeug.security import check_password_hash
    
    email = request.form.get('email')
    password = request.form.get('password')
    
    user = User.query.filter_by(email=email).first()
    
    if user and user.password_hash and check_password_hash(user.password_hash, password):
        login_user(user)
        return redirect(url_for('index'))
    
    flash('Invalid email or password', 'error')
    return redirect(url_for('login'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/oauth_callback')
def oauth_callback():
    if google.authorized:
        resp = google.get('oauth2/userinfo')
        email = resp.json().get('email')
        name = resp.json().get('name')
        
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(email=email, name=name, oauth_provider='google', oauth_id=email)
            db.session.add(user)
            db.session.commit()
        
        login_user(user)
        return redirect(url_for('index'))
    
    # Apple OAuth - requires custom implementation
    # Apple Sign In requires specific setup through Apple Developer Portal
    
    flash('OAuth failed', 'error')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    return render_template('index.html')

# API routes
@app.route('/api/assignments', methods=['GET'])
@login_required
def get_assignments():
    assignments = Assignment.query.filter_by(user_id=current_user.id).all()
    return jsonify([{
        'id': a.id,
        'title': a.title,
        'course_id': a.course_id,
        'due_date': a.due_date.isoformat(),
        'priority': a.priority,
        'status': a.status,
        'notes': a.notes
    } for a in assignments])

@app.route('/api/assignments', methods=['POST'])
@login_required
def add_assignment():
    data = request.json
    due_date = datetime.fromisoformat(data['due_date'].replace('Z', '+00:00'))
    assignment = Assignment(
        title=data['title'],
        course_id=data['course_id'],
        due_date=due_date,
        priority=data.get('priority', 'medium'),
        notes=data.get('notes', ''),
        user_id=current_user.id
    )
    db.session.add(assignment)
    db.session.commit()
    return jsonify({'id': assignment.id}), 201

@app.route('/api/assignments/<int:id>', methods=['PUT'])
@login_required
def update_assignment(id):
    data = request.json
    assignment = Assignment.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    if 'title' in data:
        assignment.title = data['title']
    if 'due_date' in data:
        assignment.due_date = datetime.fromisoformat(data['due_date'].replace('Z', '+00:00'))
    if 'priority' in data:
        assignment.priority = data['priority']
    if 'status' in data:
        assignment.status = data['status']
    if 'notes' in data:
        assignment.notes = data['notes']
    if 'course_id' in data:
        assignment.course_id = data['course_id']
    db.session.commit()
    return jsonify({'id': assignment.id})

@app.route('/api/assignments/<int:id>', methods=['DELETE'])
@login_required
def delete_assignment(id):
    assignment = Assignment.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    db.session.delete(assignment)
    db.session.commit()
    return '', 204

@app.route('/api/courses', methods=['GET'])
@login_required
def get_courses():
    courses = Course.query.filter_by(user_id=current_user.id).all()
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'color': c.color
    } for c in courses])

@app.route('/api/courses', methods=['POST'])
@login_required
def add_course():
    data = request.json
    course = Course(
        name=data['name'],
        color=data.get('color', '#808080'),
        user_id=current_user.id
    )
    db.session.add(course)
    db.session.commit()
    return jsonify({'id': course.id}), 201

@app.route('/api/courses/<int:id>', methods=['DELETE'])
@login_required
def delete_course(id):
    course = Course.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    db.session.delete(course)
    db.session.commit()
    return '', 204

@app.route('/api/user')
@login_required
def get_user():
    return jsonify({
        'id': current_user.id,
        'name': current_user.name,
        'email': current_user.email
    })

@app.route('/api/auth_status')
def auth_status():
    if current_user.is_authenticated:
        return jsonify({'authenticated': True, 'user': {'name': current_user.name, 'email': current_user.email}})
    return jsonify({'authenticated': False})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run()