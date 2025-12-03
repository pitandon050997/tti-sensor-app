# 🔬 TTI Sensor Analysis Web Application

**Food Freshness Monitoring System using Time-Temperature Indicator Sensors**

Author: Piyush Tandon  
Supervisor: Dr. Juming Tang  
University of Washington

---

## ✅ Issues Fixed in This Version

1. **Upload picture doesn't respond** → ✅ Fixed with proper FormData handling
2. **Camera capture doesn't analyze** → ✅ Fixed with base64 image processing
3. **No manual calibration option** → ✅ Added web-based calibration tool

---

## 🚀 Quick Start

### Local Development

```bash
# 1. Navigate to folder
cd tti-sensor-app

# 2. Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
python3 app.py

# 5. Open in browser
# Desktop: http://localhost:8080
# Mobile: http://YOUR-IP:8080
```

---

## 📱 Features

### Desktop Interface
- Drag & drop image upload
- Click to analyze
- View history of analyses
- Export results

### Mobile Interface
- Camera capture support
- Gallery upload
- Touch-optimized UI
- Instant analysis

### Web Calibration
- Upload sensor image
- Click & drag to select color regions
- Visual feedback with colored boxes
- Save calibration instantly

---

## 🌐 Deploy to Render (Free Hosting)

### Step 1: Push to GitHub

```bash
cd tti-sensor-app
git init
git add .
git commit -m "TTI Sensor Analysis - Complete App"
git remote add origin https://github.com/YOUR-USERNAME/tti-sensor-app.git
git push -u origin main
```

### Step 2: Deploy on Render

1. Go to [render.com](https://render.com)
2. Sign in with GitHub
3. Click "New +" → "Web Service"
4. Select your `tti-sensor-app` repository
5. Configure:
   - **Name:** `tti-sensor-app`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Instance Type:** Free
6. Click "Create Web Service"
7. Wait 2-3 minutes for deployment
8. Access at: `https://tti-sensor-app.onrender.com`

---

## 📁 Project Structure

```
tti-sensor-app/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── Procfile              # Deployment config
├── render.yaml           # Render config
├── core/
│   ├── __init__.py
│   └── tti_analyzer.py   # Core analysis engine
├── templates/
│   ├── index.html        # Main interface
│   ├── mobile.html       # Mobile interface
│   ├── calibrate.html    # Web calibration
│   └── upload_calibration.html
├── uploads/              # Uploaded images (temp)
├── output/               # Analysis outputs
└── calibrations/         # Saved calibrations
```

---

## 🎯 How to Use

### First Time Setup

1. Open the app
2. Click "🎯 Web Calibration" (or "⚡ Use Default" for quick start)
3. Upload a sensor image showing all color states
4. Click and drag to select each region (Fresh → Good → Warning → Expired)
5. Save calibration

### Analyzing Sensors

**Desktop:**
1. Drag & drop sensor image OR click to upload
2. Click "🔍 Analyze Sensor"
3. View results

**Mobile:**
1. Tap camera button to capture
2. Or tap gallery button to upload
3. Tap "Analyze Sensor"
4. View results

---

## 🔧 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main interface |
| `/mobile` | GET | Mobile interface |
| `/calibrate` | GET | Web calibration |
| `/api/analyze` | POST | Analyze image |
| `/api/calibrate` | POST | Save calibration |
| `/api/calibration/status` | GET | Check calibration |
| `/api/calibration/default` | POST | Use default calibration |
| `/api/history` | GET | Get analysis history |

---

## 🎨 Color States

| Status | Color | Days Remaining |
|--------|-------|----------------|
| 🟢 Fresh | Green | 30-40 days |
| 🟡 Good | Light Green | 15-30 days |
| 🟠 Warning | Brown | 5-15 days |
| 🔴 Expired | Red | 0 days |

---

## 🐛 Troubleshooting

### "Port 5000 in use" (macOS)
The app uses port 8080 by default. If you need to change it:
```python
# In app.py, change the port
port = int(os.environ.get('PORT', 8080))  # Change 8080 to desired port
```

### "Camera not working" (Mobile)
- Ensure you're using HTTPS (required for camera access)
- Grant camera permissions when prompted
- Try using gallery upload as alternative

### "Analysis fails"
- Ensure calibration is set up
- Check image is clear and well-lit
- Try the "Use Default" calibration option

---

## 📞 Support

For issues or questions:
- Create an issue on GitHub
- Contact: Piyush Tandon, University of Washington

---

## 📄 License

Academic use only. For commercial licensing, contact University of Washington.
