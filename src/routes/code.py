from flask import Blueprint, jsonify, request
from src.models.user import CodeQuery, User, db
from src.services.code_query_service import CodeQueryService
from datetime import datetime
import time

code_bp = Blueprint('code', __name__)

@code_bp.route('/code/query', methods=['POST'])
def query_electrical_code():
    """
    Free electrical code query service available to all users
    Ask AI anything about the NEC code book
    """
    try:
        data = request.json
        
        if not data.get('query'):
            return jsonify({'error': 'Query text is required'}), 400
        
        query_text = data['query'].strip()
        user_id = data.get('user_id')  # Optional - can be anonymous
        
        # Validate user if provided
        if user_id:
            user = User.query.get(user_id)
            if not user:
                return jsonify({'error': 'Invalid user ID'}), 400
        
        # Record start time for performance tracking
        start_time = time.time()
        
        # Process the query using AI service
        try:
            code_service = CodeQueryService()
            response_data = code_service.process_query(query_text)
            
            response_time = time.time() - start_time
            
            # Create query record
            code_query = CodeQuery(
                user_id=user_id,
                query_text=query_text,
                response_text=response_data.get('response'),
                code_references=response_data.get('references', []),
                response_time=response_time
            )
            
            db.session.add(code_query)
            db.session.commit()
            
            return jsonify({
                'query_id': code_query.id,
                'response': response_data.get('response'),
                'references': response_data.get('references', []),
                'confidence': response_data.get('confidence', 0.0),
                'response_time': response_time,
                'disclaimer': 'This AI response is for informational purposes only. Always consult with a licensed electrician and refer to the official NEC code book for final verification.'
            }), 200
            
        except Exception as ai_error:
            # Log the error but provide a helpful response
            print(f"Code Query AI Error: {ai_error}")
            
            # Create query record even for errors
            code_query = CodeQuery(
                user_id=user_id,
                query_text=query_text,
                response_text="I apologize, but I'm unable to process your query at the moment. Please try again later or consult the official NEC code book.",
                response_time=time.time() - start_time
            )
            
            db.session.add(code_query)
            db.session.commit()
            
            return jsonify({
                'query_id': code_query.id,
                'response': "I apologize, but I'm unable to process your query at the moment. Please try again later or consult the official NEC code book.",
                'references': [],
                'confidence': 0.0,
                'error': 'AI service temporarily unavailable',
                'disclaimer': 'This AI response is for informational purposes only. Always consult with a licensed electrician and refer to the official NEC code book for final verification.'
            }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@code_bp.route('/code/query/<int:query_id>/rate', methods=['POST'])
def rate_query_response(query_id):
    """Rate the quality of a code query response"""
    try:
        data = request.json
        code_query = CodeQuery.query.get_or_404(query_id)
        
        rating = data.get('rating')
        if not rating or rating < 1 or rating > 5:
            return jsonify({'error': 'Rating must be between 1 and 5'}), 400
        
        code_query.user_rating = rating
        db.session.commit()
        
        return jsonify({
            'message': 'Rating submitted successfully',
            'query_id': query_id,
            'rating': rating
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@code_bp.route('/code/popular-queries', methods=['GET'])
def get_popular_queries():
    """Get popular/recent code queries for inspiration"""
    try:
        # Get recent highly-rated queries (anonymized)
        popular_queries = db.session.query(CodeQuery.query_text, CodeQuery.response_text) \
            .filter(CodeQuery.user_rating >= 4) \
            .order_by(CodeQuery.created_at.desc()) \
            .limit(10) \
            .all()
        
        return jsonify({
            'popular_queries': [
                {
                    'query': query[0],
                    'response_preview': query[1][:200] + '...' if len(query[1]) > 200 else query[1]
                }
                for query in popular_queries
            ]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@code_bp.route('/code/search-history/<int:user_id>', methods=['GET'])
def get_user_query_history(user_id):
    """Get user's code query history"""
    try:
        user = User.query.get_or_404(user_id)
        
        # Get user's recent queries
        queries = CodeQuery.query.filter_by(user_id=user_id) \
            .order_by(CodeQuery.created_at.desc()) \
            .limit(50) \
            .all()
        
        return jsonify({
            'queries': [query.to_dict() for query in queries],
            'total_count': len(queries)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@code_bp.route('/code/categories', methods=['GET'])
def get_code_categories():
    """Get common electrical code categories for quick access"""
    try:
        categories = [
            {
                'name': 'Wiring Methods',
                'description': 'Questions about cable types, conduits, and installation methods',
                'sample_queries': [
                    'What type of cable should I use for outdoor wiring?',
                    'When is conduit required for electrical wiring?',
                    'What are the requirements for THWN wire?'
                ]
            },
            {
                'name': 'Grounding & Bonding',
                'description': 'Questions about electrical grounding and bonding requirements',
                'sample_queries': [
                    'What size grounding conductor do I need?',
                    'How do I properly bond a metal water pipe?',
                    'What are the grounding requirements for a sub-panel?'
                ]
            },
            {
                'name': 'Circuit Protection',
                'description': 'Questions about breakers, fuses, and overcurrent protection',
                'sample_queries': [
                    'What size breaker do I need for a 20 amp circuit?',
                    'When are GFCI outlets required?',
                    'What is the difference between GFCI and AFCI?'
                ]
            },
            {
                'name': 'Load Calculations',
                'description': 'Questions about electrical load calculations and capacity',
                'sample_queries': [
                    'How do I calculate the load for a residential service?',
                    'What is the demand factor for electric heating?',
                    'How many outlets can I put on a 20 amp circuit?'
                ]
            },
            {
                'name': 'Special Locations',
                'description': 'Questions about bathrooms, kitchens, garages, and other special areas',
                'sample_queries': [
                    'What are the outlet requirements for a kitchen?',
                    'Do I need GFCI protection in a garage?',
                    'What are the clearance requirements around electrical panels?'
                ]
            }
        ]
        
        return jsonify({'categories': categories}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

