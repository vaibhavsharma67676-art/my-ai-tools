import os
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from rembg import remove
from PIL import Image
import io
import img2pdf
from pypdf import PdfWriter
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'vaibhav-secret-key-999'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
CORS(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return render_template('index.html', user=current_user)

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data['username']).first()
    if user and check_password_hash(user.password, data['password']):
        login_user(user)
        return jsonify({"message": "Login Successful", "success": True})
    return jsonify({"message": "Invalid credentials", "success": False})

@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    try:
        hashed_password = generate_password_hash(data['password'], method='pbkdf2:sha256')
        new_user = User(username=data['username'], password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"message": "Account Created!", "success": True})
    except:
        return jsonify({"message": "Username already exists", "success": False})

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

# --- TOOL 1: BG REMOVER ---
@app.route('/api/remove-bg', methods=['POST'])
def remove_background():
    if not current_user.is_authenticated: return jsonify({"error": "Login First"}), 401
    file = request.files.get('file')
    if not file: return jsonify({"error": "No file"}), 400
    try:
        input_image = Image.open(file.stream)
        output_image = remove(input_image)
        img_io = io.BytesIO()
        output_image.save(img_io, 'PNG')
        img_io.seek(0)
        return send_file(img_io, mimetype='image/png')
    except Exception as e: return jsonify({"error": str(e)}), 500

# --- TOOL 2: IMAGE TO PDF ---
@app.route('/api/img-to-pdf', methods=['POST'])
def img_to_pdf():
    if not current_user.is_authenticated: return jsonify({"error": "Login First"}), 401
    file = request.files.get('file')
    if not file: return jsonify({"error": "No file"}), 400
    try:
        pdf_bytes = img2pdf.convert(file.stream.read())
        pdf_io = io.BytesIO(pdf_bytes)
        pdf_io.seek(0)
        return send_file(pdf_io, mimetype='application/pdf', download_name='converted.pdf')
    except Exception as e: return jsonify({"error": str(e)}), 500

# --- TOOL 3: PDF MERGER (EDITOR) ---
@app.route('/api/merge-pdf', methods=['POST'])
def merge_pdf():
    if not current_user.is_authenticated: return jsonify({"error": "Login First"}), 401
    files = request.files.getlist('file') # Multiple files
    if not files: return jsonify({"error": "No files"}), 400
    try:
        merger = PdfWriter()
        for pdf in files:
            merger.append(pdf)
        pdf_io = io.BytesIO()
        merger.write(pdf_io)
        merger.close()
        pdf_io.seek(0)
        return send_file(pdf_io, mimetype='application/pdf', download_name='merged.pdf')
    except Exception as e: return jsonify({"error": str(e)}), 500

# --- TOOL 4: IMAGE RESIZE (KB) ---
@app.route('/api/resize-image', methods=['POST'])
def resize_image():
    if not current_user.is_authenticated: return jsonify({"error": "Login First"}), 401
    file = request.files.get('file')
    target_kb = int(request.form.get('kb', 50)) # Default 50KB
    if not file: return jsonify({"error": "No file"}), 400
    
    try:
        img = Image.open(file.stream)
        if img.mode in ("RGBA", "P"): img = img.convert("RGB") # JPG doesnt support transparent
        
        img_io = io.BytesIO()
        quality = 95
        
        # Loop to reduce size
        while quality > 10:
            img_io = io.BytesIO()
            img.save(img_io, 'JPEG', quality=quality)
            size_kb = img_io.tell() / 1024
            if size_kb <= target_kb:
                break
            quality -= 5
            
        img_io.seek(0)
        return send_file(img_io, mimetype='image/jpeg', download_name='resized.jpg')
    except Exception as e: return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    if not os.path.exists('database.db'):
        with app.app_context():
            db.create_all()
    app.run(debug=True, port=5000)