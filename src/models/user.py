from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import enum

db = SQLAlchemy()

class SubscriptionTier(enum.Enum):
    FREEMIUM = "freemium"
    BASIC = "basic"  # $9
    PROFESSIONAL = "professional"  # $19
    ENTERPRISE = "enterprise"  # $29

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    subscription_tier = db.Column(db.Enum(SubscriptionTier), default=SubscriptionTier.FREEMIUM)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    # Usage tracking for freemium limits
    monthly_uploads = db.Column(db.Integer, default=0)
    last_reset_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    inspections = db.relationship('Inspection', backref='user', lazy=True, cascade='all, delete-orphan')
    subscriptions = db.relationship('Subscription', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def can_upload(self):
        """Check if user can upload based on their subscription tier and usage"""
        if self.subscription_tier != SubscriptionTier.FREEMIUM:
            return True
        
        # Reset monthly counter if needed
        now = datetime.utcnow()
        if self.last_reset_date.month != now.month or self.last_reset_date.year != now.year:
            self.monthly_uploads = 0
            self.last_reset_date = now
            db.session.commit()
        
        return self.monthly_uploads < 3  # Freemium limit

    def increment_upload_count(self):
        """Increment upload count for usage tracking"""
        self.monthly_uploads += 1
        db.session.commit()

    def __repr__(self):
        return f'<User {self.username}>'

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'subscription_tier': self.subscription_tier.value,
            'created_at': self.created_at.isoformat(),
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'is_active': self.is_active,
            'monthly_uploads': self.monthly_uploads,
            'can_upload': self.can_upload()
        }

class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tier = db.Column(db.Enum(SubscriptionTier), nullable=False)
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    stripe_subscription_id = db.Column(db.String(255))
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'tier': self.tier.value,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'is_active': self.is_active,
            'stripe_subscription_id': self.stripe_subscription_id
        }

class Inspection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    project_name = db.Column(db.String(255))
    location = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Analysis results
    overall_result = db.Column(db.String(20))  # 'pass', 'fail', 'warning'
    confidence_score = db.Column(db.Float)
    ai_analysis = db.Column(db.Text)
    
    # User feedback
    user_rating = db.Column(db.Integer)  # 1-5 stars
    user_feedback = db.Column(db.Text)
    
    # Relationships
    images = db.relationship('InspectionImage', backref='inspection', lazy=True, cascade='all, delete-orphan')
    videos = db.relationship('InspectionVideo', backref='inspection', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'project_name': self.project_name,
            'location': self.location,
            'created_at': self.created_at.isoformat(),
            'overall_result': self.overall_result,
            'confidence_score': self.confidence_score,
            'ai_analysis': self.ai_analysis,
            'user_rating': self.user_rating,
            'user_feedback': self.user_feedback,
            'image_count': len(self.images),
            'video_count': len(self.videos)
        }

class InspectionImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    inspection_id = db.Column(db.Integer, db.ForeignKey('inspection.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255))
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # AI analysis results for this specific image
    detected_components = db.Column(db.JSON)
    violations_found = db.Column(db.JSON)
    confidence_scores = db.Column(db.JSON)
    analysis_result = db.Column(db.String(20))  # 'pass', 'fail', 'warning'
    
    def to_dict(self):
        return {
            'id': self.id,
            'inspection_id': self.inspection_id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'uploaded_at': self.uploaded_at.isoformat(),
            'detected_components': self.detected_components,
            'violations_found': self.violations_found,
            'confidence_scores': self.confidence_scores,
            'analysis_result': self.analysis_result
        }

class InspectionVideo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    inspection_id = db.Column(db.Integer, db.ForeignKey('inspection.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255))
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)
    duration = db.Column(db.Float)  # in seconds
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # AI analysis results
    frame_analyses = db.Column(db.JSON)  # Analysis results for key frames
    overall_result = db.Column(db.String(20))  # 'pass', 'fail', 'warning'
    
    def to_dict(self):
        return {
            'id': self.id,
            'inspection_id': self.inspection_id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'duration': self.duration,
            'uploaded_at': self.uploaded_at.isoformat(),
            'frame_analyses': self.frame_analyses,
            'overall_result': self.overall_result
        }

class CodeQuery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Can be anonymous
    query_text = db.Column(db.Text, nullable=False)
    response_text = db.Column(db.Text)
    code_references = db.Column(db.JSON)  # NEC section references
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    response_time = db.Column(db.Float)  # in seconds
    user_rating = db.Column(db.Integer)  # 1-5 stars for response quality
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'query_text': self.query_text,
            'response_text': self.response_text,
            'code_references': self.code_references,
            'created_at': self.created_at.isoformat(),
            'response_time': self.response_time,
            'user_rating': self.user_rating
        }

