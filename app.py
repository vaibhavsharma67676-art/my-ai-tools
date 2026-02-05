import os
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from rembg import remove
from PIL import Image, ImageEnhance
import io
import img2pdf
from pypdf import PdfWriter, PdfReader

app = Flask(__name__)
CORS(app)

# --- HOME PAGE ---
@app.route('/')
def home():
    return render_template('index.html')

# --- TOOL 1: BG REMOVER ---
@app.route('/api/remove-bg', methods=['POST'])
def remove_background():
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
    file = request.files.get('file')
    if not file: return jsonify({"error": "No file"}), 400
    try:
        pdf_bytes = img2pdf.convert(file.stream.read())
        pdf_io = io.BytesIO(pdf_bytes)
        pdf_io.seek(0)
        return send_file(pdf_io, mimetype='application/pdf', download_name='converted.pdf')
    except Exception as e: return jsonify({"error": str(e)}), 500

# --- TOOL 3: PDF MERGER ---
@app.route('/api/merge-pdf', methods=['POST'])
def merge_pdf():
    files = request.files.getlist('file')
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

# --- TOOL 4: IMAGE RESIZER (KB) ---
@app.route('/api/resize-image', methods=['POST'])
def resize_image():
    file = request.files.get('file')
    target_kb = int(request.form.get('val', 50))
    if not file: return jsonify({"error": "No file"}), 400
    try:
        img = Image.open(file.stream)
        if img.mode in ("RGBA", "P"): img = img.convert("RGB")
        img_io = io.BytesIO()
        quality = 95
        while quality > 10:
            img_io = io.BytesIO()
            img.save(img_io, 'JPEG', quality=quality)
            if (img_io.tell() / 1024) <= target_kb: break
            quality -= 5
        img_io.seek(0)
        return send_file(img_io, mimetype='image/jpeg', download_name='resized.jpg')
    except Exception as e: return jsonify({"error": str(e)}), 500

# --- TOOL 5: PDF COMPRESSOR ---
@app.route('/api/compress-pdf', methods=['POST'])
def compress_pdf():
    file = request.files.get('file')
    if not file: return jsonify({"error": "No file"}), 400
    try:
        reader = PdfReader(file)
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        for page in writer.pages:
            page.compress_content_streams()
        pdf_io = io.BytesIO()
        writer.write(pdf_io)
        pdf_io.seek(0)
        return send_file(pdf_io, mimetype='application/pdf', download_name='compressed.pdf')
    except Exception as e: return jsonify({"error": str(e)}), 500

# --- TOOL 6: IMAGE ENHANCER ---
@app.route('/api/enhance-image', methods=['POST'])
def enhance_image():
    file = request.files.get('file')
    factor = float(request.form.get('val', 1.5))
    if not file: return jsonify({"error": "No file"}), 400
    try:
        img = Image.open(file.stream)
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(factor)
        enhancer_con = ImageEnhance.Contrast(img)
        img = enhancer_con.enhance(1.2)
        
        img_io = io.BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)
        return send_file(img_io, mimetype='image/png')
    except Exception as e: return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)