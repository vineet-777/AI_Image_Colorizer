# -*- coding: utf-8 -*-
"""
Flask Image Colorization Application
Converts black & white images to color using deep learning
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import numpy as np
import cv2
import os
from PIL import Image
import webbrowser
from threading import Timer
import hashlib
from dotenv import load_dotenv
from datetime import datetime
from functools import wraps
import traceback
import uuid
import database as db

# Load environment variables
load_dotenv()

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Initialize SQLite database
print("Initializing database...")
try:
    db.init_database()
    print("Database ready")
except Exception as e:
    print(f"Database error: {e}")

# Ensure uploads folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Load colorization model
try:
    prototxt = "models/models_colorization_deploy_v2.prototxt"
    model = "models/colorization_release_v2.caffemodel"
    points = "models/pts_in_hull.npy"

    net = cv2.dnn.readNetFromCaffe(prototxt, model)
    pts = np.load(points)
    class8 = net.getLayerId("class8_ab")
    conv8 = net.getLayerId("conv8_313_rh")
    pts = pts.transpose().reshape(2, 313, 1, 1)
    net.getLayer(class8).blobs = [pts.astype("float32")]
    net.getLayer(conv8).blobs = [np.full([1, 313], 2.606, dtype="float32")]
    print("Model loaded successfully")
except Exception as e:
    print(f"Failed to load model: {e}")
    net = None

# Helper functions

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def login_required(f):
    """Decorator to require login for protected routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def colorizer(img):
    """Apply colorization to grayscale image using neural network"""
    try:
        # Convert to grayscale if needed
        if len(img.shape) == 3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Convert to RGB for processing
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        
        # Normalize and convert to LAB color space
        scaled = img.astype("float32") / 255.0
        lab = cv2.cvtColor(scaled, cv2.COLOR_RGB2LAB)
        resized = cv2.resize(lab, (224, 224))
        L = cv2.split(resized)[0]
        L -= 50
        
        # Run neural network prediction
        net.setInput(cv2.dnn.blobFromImage(L))
        ab = net.forward()[0, :, :, :].transpose((1, 2, 0))
        ab = cv2.resize(ab, (img.shape[1], img.shape[0]))
        
        # Merge L and ab channels
        L = cv2.split(lab)[0]
        colorized = np.concatenate((L[:, :, np.newaxis], ab), axis=2)
        colorized = cv2.cvtColor(colorized, cv2.COLOR_LAB2RGB)
        colorized = np.clip(colorized, 0, 1)
        colorized = (255 * colorized).astype("uint8")
        
        return colorized
    except Exception as e:
        print(f"Colorization error: {e}")
        traceback.print_exc()
        raise

def open_browser():
    """Auto-open browser on startup"""
    webbrowser.open_new('http://127.0.0.1:5000/')

# Routes

@app.route('/')
def index():
    """Dashboard - displays user's colorized images"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    try:
        user_images = db.get_user_images(session['user_id'])
        print(f"Loaded {len(user_images)} images for user {session['user_id']}")
    except Exception as e:
        print(f"Error fetching images: {e}")
        traceback.print_exc()
        user_images = []
        flash('Error loading your images.', 'error')

    return render_template('dashboard.html', user_name=session.get('user_name'), images=user_images)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        try:
            user = db.get_user_by_email(email)

            if user and user['password_hash'] == hash_password(password):
                session['user_id'] = user['id']
                session['user_name'] = user['full_name']
                session['user_email'] = user['email']

                db.update_user_last_login(user['id'])

                flash('Welcome back!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Invalid email or password.', 'error')

        except Exception as e:
            print(f"Login error: {e}")
            traceback.print_exc()
            flash('An error occurred. Please try again.', 'error')

    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """User registration"""
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('signup'))

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return redirect(url_for('signup'))

        try:
            existing_user = db.get_user_by_email(email)

            if existing_user:
                flash('Email already registered. Please log in.', 'error')
                return redirect(url_for('login'))

            user_id = str(uuid.uuid4())
            db.create_user(user_id, full_name, email, hash_password(password))

            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('login'))

        except Exception as e:
            print(f"Signup error: {e}")
            traceback.print_exc()
            flash('An error occurred. Please try again.', 'error')

    return render_template('signup.html')

@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@app.route('/upload', methods=['POST'])
@login_required
def upload():
    """Handle image upload and colorization"""
    print("\n=== Processing Upload ===")
    
    if 'file' not in request.files:
        flash('No file selected.', 'error')
        return redirect(url_for('index'))

    file = request.files['file']
    if file.filename == '':
        flash('No file selected.', 'error')
        return redirect(url_for('index'))

    if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
        flash('Invalid file type. Please upload an image.', 'error')
        return redirect(url_for('index'))

    if not net:
        flash('Colorization model not available.', 'error')
        return redirect(url_for('index'))

    try:
        # Save original file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_filename = f"{session['user_id']}_{timestamp}_{file.filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
        file.save(filepath)

        file_size = os.path.getsize(filepath)
        print(f"File size: {file_size} bytes")

        # Read and colorize image
        img = cv2.imread(filepath)
        if img is None:
            raise Exception(f"Failed to read image from {filepath}")

        print("Applying colorization...")
        colorized = colorizer(img)

        # Save colorized image
        colorized_filename = f"colorized_{safe_filename}"
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], colorized_filename)
        cv2.imwrite(output_path, cv2.cvtColor(colorized, cv2.COLOR_RGB2BGR))

        # Save to database
        image_id = str(uuid.uuid4())
        db.create_user_image(
            image_id,
            session['user_id'],
            file.filename,
            f'uploads/{safe_filename}',
            f'uploads/{colorized_filename}',
            file_size
        )

        flash('Image colorized successfully!', 'success')
        print("=== Upload Complete ===\n")

    except Exception as e:
        print(f"Upload error: {e}")
        traceback.print_exc()
        flash('An error occurred while processing your image.', 'error')

    return redirect(url_for('index'))

@app.route('/delete/<image_id>', methods=['POST'])
@login_required
def delete_image(image_id):
    """Delete an uploaded image"""
    try:
        image = db.get_user_image(image_id, session['user_id'])

        if image:
            original_path = os.path.join('static', image['original_image_path'])
            colorized_path = os.path.join('static', image['colorized_image_path'])

            if os.path.exists(original_path):
                os.remove(original_path)
            if os.path.exists(colorized_path):
                os.remove(colorized_path)

            db.delete_user_image(image_id)
            flash('Image deleted successfully.', 'success')
        else:
            flash('Image not found.', 'error')

    except Exception as e:
        print(f"Delete error: {e}")
        traceback.print_exc()
        flash('An error occurred while deleting the image.', 'error')

    return redirect(url_for('index'))

# Main

if __name__ == '__main__':
    print("\n" + "="*50)
    print("Image Colorization App")
    print("="*50)
    print(f"Upload folder: {app.config['UPLOAD_FOLDER']}")
    print(f"Database: SQLite")
    print(f"Model: {'Loaded' if net else 'Not loaded'}")
    print("="*50 + "\n")
    
    # Only open browser in main process, not the reloader
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        Timer(1, open_browser).start()
    
    app.run(debug=True)