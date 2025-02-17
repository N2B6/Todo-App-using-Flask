from flask import Flask, session, render_template, request, redirect, jsonify, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone, timedelta
import os
from authlib.integrations.flask_client import OAuth
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import uuid
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'todos.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.environ.get('SECRET_KEY')  # Use proper secret key in production

# Add Google OAuth config
app.config['GOOGLE_CLIENT_ID'] = os.environ.get('GOOGLE_CLIENT_ID')
app.config['GOOGLE_CLIENT_SECRET'] = os.environ.get('GOOGLE_CLIENT_SECRET')
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=app.config['GOOGLE_CLIENT_ID'],
    client_secret=app.config['GOOGLE_CLIENT_SECRET'],
    access_token_url='https://oauth2.googleapis.com/token',
    authorize_url='https://accounts.google.com/o/oauth2/v2/auth',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile',
        'authorize_url': 'https://accounts.google.com/o/oauth2/v2/auth?access_type=offline&prompt=consent'
    },
    jwks_uri='https://www.googleapis.com/oauth2/v3/certs'
)

db = SQLAlchemy(app)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text(100))
    completed = db.Column(db.Boolean, default=False)
    priority = db.Column(db.Integer, default=2)
    date_created = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    date_completed = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    user = db.relationship('User', backref='todos')
    session_id = db.Column(db.String(36), nullable=False)
    is_temporary = db.Column(db.Boolean, default=True, nullable=False)

# Add User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.String(100), unique=True)
    email = db.Column(db.String(100), unique=True)
    name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))

# Create database tables within application context
with app.app_context():
    db.create_all()

# Initialize scheduler
scheduler = BackgroundScheduler(daemon=True)
scheduler.add_jobstore('sqlalchemy', url=app.config['SQLALCHEMY_DATABASE_URI'])

def delete_old_temp_tasks():
    with app.app_context():
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(days=30)
            deleted_count = Todo.query.filter(
                Todo.is_temporary == True,
                Todo.date_created < cutoff
            ).delete()
            db.session.commit()
            app.logger.info(f"Cleaned up {deleted_count} temporary tasks")
        except Exception as e:
            app.logger.error(f"Cleanup error: {str(e)}")
            db.session.rollback()

# Schedule cleanup to run daily at 3 AM
scheduler.add_job(
    delete_old_temp_tasks,
    'cron',
    hour=3,
    minute=0,
    timezone='UTC'
)

# Start scheduler when app starts
if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
    scheduler.start()

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        if 'user_id' not in session:
            flash('Please login with Google to create tasks', 'warning')
            return redirect(url_for('login'))
            
        todo_title = request.form.get('title')
        todo_description = request.form.get('description', '')
        todo_priority = request.form.get('priority', 2, type=int)

        # Validate required fields
        if not todo_title:
            flash('Task title is required', 'danger')
            return redirect(url_for('home'))
            
        if len(todo_description) > 300:
            flash('Description cannot exceed 300 characters', 'danger')
            return redirect(url_for('home'))

        # Create new task with user association
        new_todo = Todo(
            title=todo_title,
            description=todo_description,
            priority=todo_priority,
            completed=False,
            date_created=datetime.now(timezone.utc),
            user_id=session['user_id']
        )

        try:
            db.session.add(new_todo)
            db.session.commit()
            flash('Task added successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error saving task to database', 'danger')

        return redirect(url_for('home'))

    # GET request - show todos for current session
    active_todos = []
    completed_todos = []
    
    if 'user_id' in session:
        # Logged-in user - show all their tasks
        active_todos = Todo.query.filter_by(
            completed=False, 
            user_id=session['user_id']
        ).order_by(Todo.date_created.desc()).all()
        
        completed_todos = Todo.query.filter_by(
            completed=True, 
            user_id=session['user_id']
        ).order_by(Todo.date_completed.desc()).all()
    else:
        # Guest user - show temporary session tasks
        session_id = session.get('temp_user')
        if session_id:
            active_todos = Todo.query.filter_by(
                completed=False, 
                session_id=session_id
            ).order_by(Todo.date_created.desc()).all()
            
            completed_todos = Todo.query.filter_by(
                completed=True, 
                session_id=session_id
            ).order_by(Todo.date_completed.desc()).all()

    return render_template('index.html', 
                         active_todos=active_todos,
                         completed_todos=completed_todos)

@app.route('/delete/<int:id>', methods=['DELETE'])
def delete(id):
    try:
        # Check for both user_id and session_id
        if 'user_id' in session:
            todo = Todo.query.filter_by(id=id, user_id=session['user_id']).first_or_404()
        else:
            todo = Todo.query.filter_by(id=id, session_id=session.get('temp_user')).first_or_404()
            
        db.session.delete(todo)
        db.session.commit()
        return jsonify({'success': True}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False}), 500

@app.route('/update/<int:id>', methods=['POST'])
def update(id):
    # Check for both user_id and session_id
    if 'user_id' in session:
        todo = Todo.query.filter_by(id=id, user_id=session['user_id']).first_or_404()
    else:
        todo = Todo.query.filter_by(id=id, session_id=session.get('temp_user')).first_or_404()
        
    if 'completed' in request.json:
        todo.completed = request.json['completed']
        todo.date_completed = datetime.now(timezone.utc) if request.json['completed'] else None
    db.session.commit()
    return jsonify({'success': True})

@app.route('/delete-completed', methods=['POST'])
def delete_completed():
    try:
        Todo.query.filter_by(completed=True, user_id=session['user_id']).delete()
        db.session.commit()
        flash('All completed tasks deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting completed tasks', 'danger')
    return redirect(url_for('home'))

@app.route('/login')
def login():
    redirect_uri = url_for('authorize', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/authorize')
def authorize():
    try:
        token = google.authorize_access_token()
        if not token:
            flash('Failed to obtain access token', 'danger')
            return redirect(url_for('home'))
            
        # Get and verify ID token
        idinfo = id_token.verify_oauth2_token(
            token['id_token'],
            google_requests.Request(),
            app.config['GOOGLE_CLIENT_ID']
        )
        
        # Additional validation
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer.')
            
        if idinfo['aud'] != app.config['GOOGLE_CLIENT_ID']:
            raise ValueError('Invalid client ID')

        # Debug logging (remove in production)
        app.logger.debug('Google ID info: %s', idinfo)
        
        # Extract user information
        google_id = idinfo['sub']
        email = idinfo['email']
        name = idinfo.get('name', email.split('@')[0])
        
        # Check for existing user
        user = User.query.filter_by(google_id=google_id).first()
        
        if not user:
            # Check if email exists with different provider
            if User.query.filter_by(email=email).first():
                flash('Email already registered with different login method', 'danger')
                return redirect(url_for('home'))
                
            # Create new user
            user = User(
                google_id=google_id,
                email=email,
                name=name
            )
            db.session.add(user)
            db.session.commit()
            app.logger.info('Created new user: %s', email)

        # Update session
        session.permanent = True
        session['user_id'] = user.id
        session['user_name'] = user.name
        session['user_email'] = user.email
        session['user_picture'] = idinfo.get('picture')
        
        flash('Logged in successfully!', 'success')
        return redirect(url_for('home'))

    except ValueError as e:
        app.logger.error('Google auth error: %s', str(e))
        flash('Invalid authentication credentials', 'danger')
    except Exception as e:
        app.logger.exception('Login error:')
        flash('Login failed. Please try again.', 'danger')
        
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('home'))

@app.route('/add-task', methods=['POST'])
def add_task():
    if request.method == 'POST':
        # Get form data
        title = request.form['title']
        description = request.form.get('description', '')
        priority = request.form.get('priority', 2, type=int)

        # Validate input
        if not title:
            flash('Task title is required', 'danger')
            return redirect(url_for('home'))

        # Create new Todo item
        new_todo = Todo(
            title=title,
            description=description,
            priority=priority,
            completed=False,
            date_created=datetime.now(timezone.utc)
        )

        # Handle user session
        if 'user_id' in session:
            new_todo.user_id = session['user_id']
            new_todo.is_temporary = False
            new_todo.session_id = str(uuid.uuid4())
        else:
            if 'temp_user' not in session:
                session['temp_user'] = str(uuid.uuid4())
            new_todo.session_id = session['temp_user']
            new_todo.is_temporary = True

        try:
            db.session.add(new_todo)
            db.session.commit()
            flash('Task added successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error saving task', 'danger')

        return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)

