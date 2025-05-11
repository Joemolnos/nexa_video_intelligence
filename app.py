import os
import tempfile
import uuid
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import subprocess
import json
import csv
import time
from werkzeug.serving import run_simple

app = Flask(__name__, static_url_path='', static_folder='.')
CORS(app)  # Cross-Origin Resource Sharing engedélyezése

# Feltöltési és elemzési könyvtárak
UPLOAD_FOLDER = 'uploads'
RESULTS_FOLDER = 'results'

# Könyvtárak létrehozása, ha még nem léteznek
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Videófájl feltöltése és feldolgozás indítása"""
    if 'video' not in request.files:
        return jsonify({'error': 'Nincs videófájl a kérésben'}), 400
    
    file = request.files['video']
    if file.filename == '':
        return jsonify({'error': 'Nincs kiválasztott fájl'}), 400
    
    # Egyedi fájlnév generálása és mentés
    filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)
    
    # Elemzési folyamat indítása
    task_id = str(uuid.uuid4())
    result = {
        'task_id': task_id,
        'status': 'processing',
        'file_path': file_path,
        'original_filename': file.filename,
        'progress': 0
    }
    
    # Az elemzést aszinkron indítjuk
    subprocess.Popen(
        ['python', 'analyze_video_task.py', file_path, task_id],
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE
    )
    
    return jsonify(result)

@app.route('/status/<task_id>', methods=['GET'])
def check_status(task_id):
    """Elemzési feladat állapotának lekérdezése"""
    status_file = os.path.join(RESULTS_FOLDER, f"{task_id}_status.json")
    
    if not os.path.exists(status_file):
        return jsonify({'status': 'pending', 'progress': 0})
    
    with open(status_file, 'r') as f:
        status = json.load(f)
    
    if status['status'] == 'completed':
        # Ha kész, visszaadjuk a CSV adatok elérési útját is
        status['summary_csv'] = f"{task_id}_summary.csv"
        status['full_csv'] = f"{task_id}_full.csv"
    
    return jsonify(status)

@app.route('/results/<filename>', methods=['GET'])
def get_result_file(filename):
    """Eredményfájl letöltése"""
    return send_from_directory(RESULTS_FOLDER, filename)

if __name__ == '__main__':
    # Hosszabb időtúllépési küszöb és nagyobb timeout érték beállítása
    run_simple('0.0.0.0', 5000, app, 
               use_reloader=True, 
               use_debugger=True,
               threaded=True,
               # Hosszabb timeout és keep-alive időtartam
               passthrough_errors=True,
               ssl_context=None)
    
    # Eredeti kód kikommentezve
    # app.run(debug=True, host='0.0.0.0', port=5000) 