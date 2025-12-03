"""
TTI Sensor Analyzer Core Module
Handles color detection and freshness analysis for TTI sensors

Author: Piyush Tandon
Supervisor: Dr. Juming Tang
University of Washington
"""

import numpy as np
from PIL import Image
import json
import os
from datetime import datetime
import math

class TTISensorAnalyzer:
    """Core analyzer for Time-Temperature Indicator sensors"""
    
    # Default calibration colors (Green-Light Green-Brown-Red scheme)
    DEFAULT_COLORS = {
        'fresh': {'rgb': [34, 139, 34], 'name': 'Forest Green', 'days': '30-40'},
        'good': {'rgb': [144, 238, 144], 'name': 'Light Green', 'days': '15-30'},
        'warning': {'rgb': [139, 90, 43], 'name': 'Brown', 'days': '5-15'},
        'expired': {'rgb': [178, 34, 34], 'name': 'Firebrick Red', 'days': '0'}
    }
    
    # Status labels
    STATUS_LABELS = {
        'fresh': {'label': 'FRESH', 'days_min': 30, 'days_max': 40, 'color': '#22c55e'},
        'good': {'label': 'GOOD', 'days_min': 15, 'days_max': 30, 'color': '#84cc16'},
        'warning': {'label': 'WARNING', 'days_min': 5, 'days_max': 15, 'color': '#f59e0b'},
        'expired': {'label': 'EXPIRED', 'days_min': 0, 'days_max': 0, 'color': '#ef4444'}
    }
    
    def __init__(self, calibration_path='calibration.json'):
        """Initialize analyzer with calibration data"""
        self.calibration_path = calibration_path
        self.calibration = None
        self.load_calibration()
    
    def load_calibration(self):
        """Load calibration data from file"""
        if os.path.exists(self.calibration_path):
            try:
                with open(self.calibration_path, 'r') as f:
                    self.calibration = json.load(f)
                return True
            except Exception as e:
                print(f"Error loading calibration: {e}")
                self.calibration = None
        return False
    
    def save_calibration(self, calibration_data):
        """Save calibration data to file"""
        try:
            with open(self.calibration_path, 'w') as f:
                json.dump(calibration_data, f, indent=2)
            self.calibration = calibration_data
            return True
        except Exception as e:
            print(f"Error saving calibration: {e}")
            return False
    
    def has_calibration(self):
        """Check if calibration is available"""
        return self.calibration is not None
    
    def get_reference_colors(self):
        """Get reference colors from calibration or defaults"""
        if self.calibration and 'colors' in self.calibration:
            return self.calibration['colors']
        return self.DEFAULT_COLORS
    
    def extract_region_color(self, image, region):
        """Extract average color from a region of an image"""
        if isinstance(image, str):
            img = Image.open(image)
        else:
            img = image
        
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        img_array = np.array(img)
        
        x, y, w, h = region['x'], region['y'], region['width'], region['height']
        
        # Ensure bounds are valid
        x = max(0, min(x, img_array.shape[1] - 1))
        y = max(0, min(y, img_array.shape[0] - 1))
        x2 = max(0, min(x + w, img_array.shape[1]))
        y2 = max(0, min(y + h, img_array.shape[0]))
        
        # Extract region
        region_pixels = img_array[y:y2, x:x2]
        
        if region_pixels.size == 0:
            return [128, 128, 128]  # Default gray if region is invalid
        
        # Calculate average color
        avg_color = np.mean(region_pixels.reshape(-1, 3), axis=0)
        return [int(c) for c in avg_color]
    
    def color_distance_euclidean(self, color1, color2):
        """Calculate Euclidean distance between two RGB colors"""
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(color1, color2)))
    
    def color_distance_manhattan(self, color1, color2):
        """Calculate Manhattan distance between two RGB colors"""
        return sum(abs(a - b) for a, b in zip(color1, color2))
    
    def rgb_to_lab(self, rgb):
        """Convert RGB to LAB color space for Delta E calculation"""
        # Normalize RGB to [0, 1]
        r, g, b = [x / 255.0 for x in rgb]
        
        # Apply gamma correction
        def gamma(c):
            return ((c + 0.055) / 1.055) ** 2.4 if c > 0.04045 else c / 12.92
        
        r, g, b = gamma(r), gamma(g), gamma(b)
        
        # Convert to XYZ
        x = r * 0.4124564 + g * 0.3575761 + b * 0.1804375
        y = r * 0.2126729 + g * 0.7151522 + b * 0.0721750
        z = r * 0.0193339 + g * 0.1191920 + b * 0.9503041
        
        # Normalize for D65 white point
        x, y, z = x / 0.95047, y / 1.0, z / 1.08883
        
        # Convert to Lab
        def f(t):
            return t ** (1/3) if t > 0.008856 else (7.787 * t) + (16 / 116)
        
        L = (116 * f(y)) - 16
        a = 500 * (f(x) - f(y))
        b_val = 200 * (f(y) - f(z))
        
        return [L, a, b_val]
    
    def color_distance_delta_e(self, color1, color2):
        """Calculate Delta E (CIE76) distance between two RGB colors"""
        lab1 = self.rgb_to_lab(color1)
        lab2 = self.rgb_to_lab(color2)
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(lab1, lab2)))
    
    def analyze_color(self, sample_color):
        """Analyze a sample color against reference colors"""
        ref_colors = self.get_reference_colors()
        
        results = {}
        
        for status, ref_data in ref_colors.items():
            ref_rgb = ref_data['rgb']
            
            # Calculate distances using all three metrics
            euclidean = self.color_distance_euclidean(sample_color, ref_rgb)
            manhattan = self.color_distance_manhattan(sample_color, ref_rgb)
            delta_e = self.color_distance_delta_e(sample_color, ref_rgb)
            
            results[status] = {
                'euclidean': euclidean,
                'manhattan': manhattan,
                'delta_e': delta_e,
                'reference_rgb': ref_rgb,
                'reference_name': ref_data.get('name', status)
            }
        
        return results
    
    def determine_status(self, distance_results, metric='delta_e'):
        """Determine freshness status based on color distances"""
        min_distance = float('inf')
        best_status = 'expired'
        
        for status, distances in distance_results.items():
            if distances[metric] < min_distance:
                min_distance = distances[metric]
                best_status = status
        
        # Calculate confidence (inverse of distance, normalized)
        max_distance = max(d[metric] for d in distance_results.values())
        if max_distance > 0:
            confidence = 1 - (min_distance / max_distance)
        else:
            confidence = 1.0
        
        return {
            'status': best_status,
            'confidence': round(confidence * 100, 1),
            'distance': round(min_distance, 2),
            'label': self.STATUS_LABELS[best_status]['label'],
            'color': self.STATUS_LABELS[best_status]['color'],
            'days_remaining': f"{self.STATUS_LABELS[best_status]['days_min']}-{self.STATUS_LABELS[best_status]['days_max']}"
        }
    
    def analyze_image(self, image_path, region=None):
        """Analyze an image and return freshness status"""
        try:
            img = Image.open(image_path)
            
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            img_array = np.array(img)
            
            # If no region specified, use center portion
            if region is None:
                h, w = img_array.shape[:2]
                center_x = w // 4
                center_y = h // 4
                region = {
                    'x': center_x,
                    'y': center_y,
                    'width': w // 2,
                    'height': h // 2
                }
            
            # Extract sample color
            sample_color = self.extract_region_color(img, region)
            
            # Analyze against references
            distance_results = self.analyze_color(sample_color)
            
            # Determine status using Delta E (most perceptually accurate)
            status_result = self.determine_status(distance_results, 'delta_e')
            
            # Build complete result
            result = {
                'timestamp': datetime.now().isoformat(),
                'image_path': image_path,
                'sample_color': {
                    'rgb': sample_color,
                    'hex': '#{:02x}{:02x}{:02x}'.format(*sample_color)
                },
                'region': region,
                'analysis': {
                    'status': status_result['status'],
                    'label': status_result['label'],
                    'confidence': status_result['confidence'],
                    'days_remaining': status_result['days_remaining'],
                    'status_color': status_result['color']
                },
                'distances': {
                    status: {
                        'euclidean': round(data['euclidean'], 2),
                        'manhattan': round(data['manhattan'], 2),
                        'delta_e': round(data['delta_e'], 2)
                    }
                    for status, data in distance_results.items()
                },
                'calibration_used': self.has_calibration()
            }
            
            return result
            
        except Exception as e:
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'image_path': image_path
            }


def create_default_calibration():
    """Create a default calibration file"""
    default_cal = {
        'name': 'Default MilkFresh Calibration',
        'created': datetime.now().isoformat(),
        'sensor_type': 'Dr. Talbots MilkFresh / Evigence FreshSense',
        'colors': TTISensorAnalyzer.DEFAULT_COLORS,
        'notes': 'Default calibration based on Green-Light Green-Brown-Red color scheme'
    }
    return default_cal
