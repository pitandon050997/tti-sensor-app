"""
TTI Sensor Analysis - Web Application
Complete Flask application with calibration, analysis, and mobile support

Author: Piyush Tandon
Supervisor: Dr. Juming Tang
University of Washington

Usage:
    python3 app.py
    Open: http://localhost:8080
"""

from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
import os
import sys
import json
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from PIL import Image
import io
import base64

# Add core module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))
from tti_analyzer import TTISensorAnalyzer, create_default_calibration

app = Flask(__name__, 
           template_folder='templates',
           static_folder='static')

app.secret_key = os.environ.get('SECRET_KEY', 'tti-sensor-analysis-dev-key')

# Configuration
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
CALIBRATION_FOLDER = 'calibrations'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'gif', 'webp'}

# Create directories
for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER, CALIBRATION_FOLDER]:
    os.makedirs(folder, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Initialize analyzer
CALIBRATION_PATH = os.path.join(CALIBRATION_FOLDER, 'calibration.json')
analyzer = TTISensorAnalyzer(CALIBRATION_PATH)

# Analysis history (in-memory for simplicity)
analysis_history = []


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_uploaded_file(file):
    """Save uploaded file and return path"""
    if file and allowed_file(file.filename):
        filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return filepath
    return None


def process_base64_image(base64_data):
    """Process base64 encoded image and save to file"""
    try:
        # Remove data URL prefix if present
        if ',' in base64_data:
            base64_data = base64_data.split(',')[1]
        
        # Decode and save
        image_data = base64.b64decode(base64_data)
        filename = f"{uuid.uuid4().hex}.png"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        with open(filepath, 'wb') as f:
            f.write(image_data)
        
        return filepath
    except Exception as e:
        print(f"Error processing base64 image: {e}")
        return None


# ============== ROUTES ==============

@app.route('/')
def index():
    """Main page - show app or welcome based on calibration status"""
    has_calibration = analyzer.has_calibration()
    return render_template('index.html', 
                         has_calibration=has_calibration,
                         history=analysis_history[-10:])


@app.route('/mobile')
def mobile():
    """Mobile-optimized interface with camera support"""
    return render_template('mobile.html', has_calibration=analyzer.has_calibration())


@app.route('/calibrate')
def calibrate_page():
    """Web-based calibration interface"""
    return render_template('calibrate.html')


@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    """
    API endpoint for image analysis
    Accepts: file upload OR base64 image OR JSON with image data
    Returns: JSON analysis results
    """
    filepath = None
    region = None
    
    try:
        # Handle different input types
        if request.content_type and 'multipart/form-data' in request.content_type:
            # File upload
            if 'image' not in request.files:
                return jsonify({'error': 'No image file provided'}), 400
            
            file = request.files['image']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            filepath = save_uploaded_file(file)
            
            # Get region if provided
            if 'region' in request.form:
                try:
                    region = json.loads(request.form['region'])
                except:
                    pass
                    
        elif request.is_json:
            # JSON with base64 image
            data = request.get_json()
            
            if 'image' in data:
                filepath = process_base64_image(data['image'])
            elif 'image_base64' in data:
                filepath = process_base64_image(data['image_base64'])
            
            if 'region' in data:
                region = data['region']
        else:
            # Try to get raw base64 data
            data = request.get_data(as_text=True)
            if data:
                try:
                    json_data = json.loads(data)
                    if 'image' in json_data:
                        filepath = process_base64_image(json_data['image'])
                except:
                    pass
        
        if not filepath:
            return jsonify({'error': 'Could not process image. Please try again.'}), 400
        
        # Perform analysis
        result = analyzer.analyze_image(filepath, region)
        
        if 'error' in result:
            return jsonify({'error': result['error']}), 500
        
        # Add to history
        analysis_history.append({
            'id': len(analysis_history) + 1,
            'timestamp': result['timestamp'],
            'status': result['analysis']['status'],
            'label': result['analysis']['label'],
            'confidence': result['analysis']['confidence'],
            'days_remaining': result['analysis']['days_remaining']
        })
        
        return jsonify({
            'success': True,
            'result': result
        })
        
    except Exception as e:
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500


@app.route('/api/calibrate', methods=['POST'])
def api_calibrate():
    """
    API endpoint for saving calibration
    Accepts: JSON with calibration data
    """
    try:
        if not request.is_json:
            # Try to parse form data
            data = request.form.to_dict()
            if 'calibration' in data:
                data = json.loads(data['calibration'])
        else:
            data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No calibration data provided'}), 400
        
        # Validate calibration data
        if 'colors' not in data:
            return jsonify({'error': 'Invalid calibration: missing colors'}), 400
        
        # Add metadata
        data['created'] = datetime.now().isoformat()
        data['source'] = 'web_calibration'
        
        # Save calibration
        if analyzer.save_calibration(data):
            return jsonify({
                'success': True,
                'message': 'Calibration saved successfully'
            })
        else:
            return jsonify({'error': 'Failed to save calibration'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Calibration failed: {str(e)}'}), 500


@app.route('/api/calibrate/extract-color', methods=['POST'])
def api_extract_color():
    """Extract color from a region of an uploaded image"""
    try:
        filepath = None
        
        if 'image' in request.files:
            file = request.files['image']
            filepath = save_uploaded_file(file)
        elif request.is_json:
            data = request.get_json()
            if 'image' in data:
                filepath = process_base64_image(data['image'])
        
        if not filepath:
            return jsonify({'error': 'No image provided'}), 400
        
        # Get region from request
        region = None
        if request.is_json:
            data = request.get_json()
            region = data.get('region')
        elif 'region' in request.form:
            region = json.loads(request.form['region'])
        
        if not region:
            # Use center of image
            img = Image.open(filepath)
            w, h = img.size
            region = {
                'x': w // 4,
                'y': h // 4,
                'width': w // 2,
                'height': h // 2
            }
        
        # Extract color
        color = analyzer.extract_region_color(filepath, region)
        
        return jsonify({
            'success': True,
            'color': {
                'rgb': color,
                'hex': '#{:02x}{:02x}{:02x}'.format(*color)
            },
            'region': region
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/calibration/status')
def api_calibration_status():
    """Check calibration status"""
    return jsonify({
        'has_calibration': analyzer.has_calibration(),
        'calibration': analyzer.calibration if analyzer.has_calibration() else None
    })


@app.route('/api/calibration/default', methods=['POST'])
def api_use_default_calibration():
    """Use default calibration"""
    try:
        default_cal = create_default_calibration()
        if analyzer.save_calibration(default_cal):
            return jsonify({
                'success': True,
                'message': 'Default calibration applied'
            })
        return jsonify({'error': 'Failed to save default calibration'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/history')
def api_history():
    """Get analysis history"""
    return jsonify({
        'history': analysis_history[-50:],
        'total': len(analysis_history)
    })


@app.route('/upload-calibration', methods=['GET', 'POST'])
def upload_calibration():
    """Page to upload calibration file"""
    if request.method == 'POST':
        if 'file' not in request.files:
            return render_template('upload_calibration.html', error='No file provided')
        
        file = request.files['file']
        if file.filename == '':
            return render_template('upload_calibration.html', error='No file selected')
        
        try:
            content = file.read().decode('utf-8')
            calibration_data = json.loads(content)
            
            if analyzer.save_calibration(calibration_data):
                return redirect(url_for('index'))
            else:
                return render_template('upload_calibration.html', error='Failed to save calibration')
        except json.JSONDecodeError:
            return render_template('upload_calibration.html', error='Invalid JSON file')
        except Exception as e:
            return render_template('upload_calibration.html', error=str(e))
    
    return render_template('upload_calibration.html')


# ============== MAIN ==============

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    debug = os.environ.get('FLASK_ENV') != 'production'
    
    print("\n" + "=" * 70)
    print("  TTI Sensor Analysis - Web Application")
    print("=" * 70)
    print(f"\n  🌐 URL: http://localhost:{port}")
    print(f"  📱 Mobile: http://localhost:{port}/mobile")
    print(f"  🎯 Calibrate: http://localhost:{port}/calibrate")
    print("\n  Press Ctrl+C to stop\n")
    print("=" * 70 + "\n")
    
    app.run(debug=debug, host='0.0.0.0', port=port)
