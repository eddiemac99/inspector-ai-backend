import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from src.models.user import db
from src.routes.user import user_bp
from src.routes.auth import auth_bp
from src.routes.inspection import inspection_bp
from src.routes.code import code_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), '..', 'electrical-inspector-frontend', 'dist'))
app.config['SECRET_KEY'] = 'electrical_inspector_ai_secret_key_2025'

# Enable CORS for all routes
CORS(app, origins="*")

# Register blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(inspection_bp, url_prefix='/api')
app.register_blueprint(code_bp, url_prefix='/api')

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# File upload configuration
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), '..', 'uploads')

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize database
db.init_app(app)
with app.app_context():
    db.create_all()

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'service': 'Electrical Inspector AI Backend',
        'version': '1.0.0',
        'features': {
            'image_analysis': True,
            'video_analysis': True,
            'code_query': True,
            'subscription_tiers': ['freemium', 'basic', 'professional', 'enterprise']
        }
    }

@app.route('/api/features', methods=['GET'])
def get_features():
    """Get available features by subscription tier"""
    return {
        'freemium': {
            'monthly_uploads': 3,
            'image_analysis': True,
            'video_analysis': False,
            'photo_library': False,
            'code_query': True,
            'microphone': False,
            'calendar': False,
            'city_inspector_contact': False
        },
        'basic': {  # $9
            'monthly_uploads': 'unlimited',
            'image_analysis': True,
            'video_analysis': False,
            'photo_library': False,
            'code_query': True,
            'microphone': False,
            'calendar': False,
            'city_inspector_contact': False,
            'features': ['Add photos', 'Remove photos', 'Submit photos', 'Pass/fail analysis']
        },
        'professional': {  # $19
            'monthly_uploads': 'unlimited',
            'image_analysis': True,
            'video_analysis': False,
            'photo_library': True,
            'code_query': True,
            'microphone': True,
            'calendar': False,
            'city_inspector_contact': False,
            'features': ['All Basic features', 'Photo library', 'Search past inspections', 'Project organization', 'Microphone dictation', 'Drag-drop functionality']
        },
        'enterprise': {  # $29
            'monthly_uploads': 'unlimited',
            'image_analysis': True,
            'video_analysis': True,
            'photo_library': True,
            'code_query': True,
            'microphone': True,
            'calendar': True,
            'city_inspector_contact': True,
            'features': ['All Professional features', 'Video upload and analysis', 'Advanced dictation for change orders', 'Calendar scheduling', 'City inspector contact integration']
        }
    }

@app.errorhandler(413)
def too_large(e):
    return {'error': 'File too large. Maximum size is 50MB.'}, 413

@app.errorhandler(404)
def not_found(e):
    return {'error': 'Endpoint not found'}, 404

@app.errorhandler(500)
def internal_error(e):
    return {'error': 'Internal server error'}, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)

