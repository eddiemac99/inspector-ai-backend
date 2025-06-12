from flask import Blueprint, jsonify, request, current_app
from werkzeug.utils import secure_filename
from src.models.user import User, Inspection, InspectionImage, InspectionVideo, SubscriptionTier, db
from src.services.ai_analysis import ImageAnalysisService, VideoAnalysisService
from datetime import datetime
import os
import uuid

inspection_bp = Blueprint('inspection', __name__)

# Configure upload settings
UPLOAD_FOLDER = 'uploads'
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'wmv', 'flv', 'webm'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

def allowed_file(filename, allowed_extensions):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def ensure_upload_directory():
    """Ensure upload directory exists"""
    upload_path = os.path.join(os.getcwd(), UPLOAD_FOLDER)
    if not os.path.exists(upload_path):
        os.makedirs(upload_path)
    return upload_path

@inspection_bp.route('/inspections', methods=['POST'])
def create_inspection():
    """Create a new inspection session"""
    try:
        data = request.json
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'User ID is required'}), 400
        
        user = User.query.get_or_404(user_id)
        
        # Create new inspection
        inspection = Inspection(
            user_id=user_id,
            project_name=data.get('project_name', 'Untitled Project'),
            location=data.get('location', '')
        )
        
        db.session.add(inspection)
        db.session.commit()
        
        return jsonify({
            'message': 'Inspection created successfully',
            'inspection': inspection.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@inspection_bp.route('/inspections/<int:inspection_id>/upload-image', methods=['POST'])
def upload_image(inspection_id):
    """Upload and analyze an image for inspection"""
    try:
        inspection = Inspection.query.get_or_404(inspection_id)
        user = User.query.get_or_404(inspection.user_id)
        
        # Check upload permissions
        if not user.can_upload():
            return jsonify({
                'error': 'Upload limit exceeded. Please upgrade your subscription.',
                'monthly_uploads': user.monthly_uploads,
                'limit': 3 if user.subscription_tier == SubscriptionTier.FREEMIUM else 'unlimited'
            }), 403
        
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file type
        if not allowed_file(file.filename, ALLOWED_IMAGE_EXTENSIONS):
            return jsonify({'error': 'Invalid file type. Allowed: ' + ', '.join(ALLOWED_IMAGE_EXTENSIONS)}), 400
        
        # Ensure upload directory exists
        upload_path = ensure_upload_directory()
        
        # Generate unique filename
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = os.path.join(upload_path, unique_filename)
        
        # Save file
        file.save(file_path)
        file_size = os.path.getsize(file_path)
        
        # Create database record
        inspection_image = InspectionImage(
            inspection_id=inspection_id,
            filename=unique_filename,
            original_filename=file.filename,
            file_path=file_path,
            file_size=file_size
        )
        
        db.session.add(inspection_image)
        
        # Increment user upload count
        user.increment_upload_count()
        
        # Perform AI analysis
        try:
            analysis_service = ImageAnalysisService()
            analysis_result = analysis_service.analyze_image(file_path)
            
            # Update image record with analysis results
            inspection_image.detected_components = analysis_result.get('detected_components', [])
            inspection_image.violations_found = analysis_result.get('violations_found', [])
            inspection_image.confidence_scores = analysis_result.get('confidence_scores', {})
            inspection_image.analysis_result = analysis_result.get('overall_result', 'unknown')
            
        except Exception as ai_error:
            # Log AI error but don't fail the upload
            print(f"AI Analysis Error: {ai_error}")
            inspection_image.analysis_result = 'error'
        
        db.session.commit()
        
        return jsonify({
            'message': 'Image uploaded and analyzed successfully',
            'image': inspection_image.to_dict(),
            'remaining_uploads': 3 - user.monthly_uploads if user.subscription_tier == SubscriptionTier.FREEMIUM else 'unlimited'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@inspection_bp.route('/inspections/<int:inspection_id>/upload-video', methods=['POST'])
def upload_video(inspection_id):
    """Upload and analyze a video for inspection (Premium feature)"""
    try:
        inspection = Inspection.query.get_or_404(inspection_id)
        user = User.query.get_or_404(inspection.user_id)
        
        # Check if user has video upload permissions (Enterprise tier only)
        if user.subscription_tier != SubscriptionTier.ENTERPRISE:
            return jsonify({
                'error': 'Video upload is only available for Enterprise subscribers ($29/month)',
                'current_tier': user.subscription_tier.value
            }), 403
        
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file type
        if not allowed_file(file.filename, ALLOWED_VIDEO_EXTENSIONS):
            return jsonify({'error': 'Invalid file type. Allowed: ' + ', '.join(ALLOWED_VIDEO_EXTENSIONS)}), 400
        
        # Ensure upload directory exists
        upload_path = ensure_upload_directory()
        
        # Generate unique filename
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = os.path.join(upload_path, unique_filename)
        
        # Save file
        file.save(file_path)
        file_size = os.path.getsize(file_path)
        
        # Create database record
        inspection_video = InspectionVideo(
            inspection_id=inspection_id,
            filename=unique_filename,
            original_filename=file.filename,
            file_path=file_path,
            file_size=file_size
        )
        
        db.session.add(inspection_video)
        
        # Perform AI analysis
        try:
            analysis_service = VideoAnalysisService()
            analysis_result = analysis_service.analyze_video(file_path)
            
            # Update video record with analysis results
            inspection_video.frame_analyses = analysis_result.get('frame_analyses', [])
            inspection_video.overall_result = analysis_result.get('overall_result', 'unknown')
            inspection_video.duration = analysis_result.get('duration', 0)
            
        except Exception as ai_error:
            # Log AI error but don't fail the upload
            print(f"AI Video Analysis Error: {ai_error}")
            inspection_video.overall_result = 'error'
        
        db.session.commit()
        
        return jsonify({
            'message': 'Video uploaded and analyzed successfully',
            'video': inspection_video.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@inspection_bp.route('/inspections/<int:inspection_id>', methods=['GET'])
def get_inspection(inspection_id):
    """Get inspection details with all images and videos"""
    try:
        inspection = Inspection.query.get_or_404(inspection_id)
        
        # Get all images and videos for this inspection
        images = [img.to_dict() for img in inspection.images]
        videos = [vid.to_dict() for vid in inspection.videos]
        
        inspection_data = inspection.to_dict()
        inspection_data['images'] = images
        inspection_data['videos'] = videos
        
        return jsonify(inspection_data), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@inspection_bp.route('/users/<int:user_id>/inspections', methods=['GET'])
def get_user_inspections(user_id):
    """Get all inspections for a user (Photo Library feature)"""
    try:
        user = User.query.get_or_404(user_id)
        
        # Check if user has access to photo library (Professional and Enterprise tiers)
        if user.subscription_tier == SubscriptionTier.FREEMIUM or user.subscription_tier == SubscriptionTier.BASIC:
            return jsonify({
                'error': 'Photo library is only available for Professional ($19/month) and Enterprise ($29/month) subscribers',
                'current_tier': user.subscription_tier.value
            }), 403
        
        # Get query parameters for filtering
        project_name = request.args.get('project_name')
        location = request.args.get('location')
        result_filter = request.args.get('result')  # 'pass', 'fail', 'warning'
        
        # Build query
        query = Inspection.query.filter_by(user_id=user_id)
        
        if project_name:
            query = query.filter(Inspection.project_name.ilike(f'%{project_name}%'))
        if location:
            query = query.filter(Inspection.location.ilike(f'%{location}%'))
        if result_filter:
            query = query.filter(Inspection.overall_result == result_filter)
        
        # Order by most recent first
        inspections = query.order_by(Inspection.created_at.desc()).all()
        
        return jsonify({
            'inspections': [inspection.to_dict() for inspection in inspections],
            'total_count': len(inspections)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@inspection_bp.route('/inspections/<int:inspection_id>/feedback', methods=['POST'])
def submit_feedback(inspection_id):
    """Submit user feedback for an inspection"""
    try:
        data = request.json
        inspection = Inspection.query.get_or_404(inspection_id)
        
        # Update inspection with user feedback
        if 'rating' in data:
            inspection.user_rating = data['rating']
        if 'feedback' in data:
            inspection.user_feedback = data['feedback']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Feedback submitted successfully',
            'inspection': inspection.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

