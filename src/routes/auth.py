from flask import Blueprint, jsonify, request, current_app
from werkzeug.utils import secure_filename
from src.models.user import User, Subscription, Inspection, InspectionImage, InspectionVideo, CodeQuery, SubscriptionTier, db
from datetime import datetime
import os
import uuid
import time

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.json
        
        # Validate required fields
        if not data.get('username') or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Username, email, and password are required'}), 400
        
        # Check if user already exists
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username already exists'}), 400
        
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already exists'}), 400
        
        # Create new user
        user = User(
            username=data['username'],
            email=data['email'],
            subscription_tier=SubscriptionTier.FREEMIUM
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate user login"""
    try:
        data = request.json
        
        if not data.get('username') or not data.get('password'):
            return jsonify({'error': 'Username and password are required'}), 400
        
        user = User.query.filter_by(username=data['username']).first()
        
        if not user or not user.check_password(data['password']):
            return jsonify({'error': 'Invalid username or password'}), 401
        
        if not user.is_active:
            return jsonify({'error': 'Account is deactivated'}), 401
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/users/<int:user_id>/subscription', methods=['GET'])
def get_user_subscription(user_id):
    """Get user's current subscription details"""
    try:
        user = User.query.get_or_404(user_id)
        active_subscription = Subscription.query.filter_by(
            user_id=user_id, 
            is_active=True
        ).first()
        
        return jsonify({
            'user_tier': user.subscription_tier.value,
            'subscription': active_subscription.to_dict() if active_subscription else None,
            'usage': {
                'monthly_uploads': user.monthly_uploads,
                'can_upload': user.can_upload()
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/users/<int:user_id>/subscription', methods=['POST'])
def update_subscription(user_id):
    """Update user's subscription tier"""
    try:
        data = request.json
        user = User.query.get_or_404(user_id)
        
        # Validate tier
        try:
            new_tier = SubscriptionTier(data['tier'])
        except ValueError:
            return jsonify({'error': 'Invalid subscription tier'}), 400
        
        # Deactivate current subscription
        current_subscription = Subscription.query.filter_by(
            user_id=user_id, 
            is_active=True
        ).first()
        
        if current_subscription:
            current_subscription.is_active = False
            current_subscription.end_date = datetime.utcnow()
        
        # Create new subscription
        new_subscription = Subscription(
            user_id=user_id,
            tier=new_tier,
            stripe_subscription_id=data.get('stripe_subscription_id')
        )
        
        # Update user tier
        user.subscription_tier = new_tier
        
        db.session.add(new_subscription)
        db.session.commit()
        
        return jsonify({
            'message': 'Subscription updated successfully',
            'subscription': new_subscription.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

