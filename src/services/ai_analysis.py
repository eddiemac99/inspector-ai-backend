import cv2
import numpy as np
import tensorflow as tf
from PIL import Image
import json
import os
from typing import Dict, List, Any

class ImageAnalysisService:
    """
    AI service for analyzing electrical installation images
    Detects components, identifies violations, and provides pass/fail assessment
    """
    
    def __init__(self):
        self.model = None
        self.component_classes = [
            'outlet', 'switch', 'panel', 'conduit', 'junction_box', 
            'wire', 'breaker', 'gfci_outlet', 'light_fixture', 'meter'
        ]
        self.violation_types = [
            'improper_wiring', 'missing_gfci', 'overcrowded_box', 
            'improper_grounding', 'code_violation', 'safety_hazard'
        ]
        
    def load_model(self):
        """Load the trained electrical inspection model"""
        try:
            # In a real implementation, this would load a trained TensorFlow model
            # For now, we'll create a mock model structure
            print("Loading electrical inspection AI model...")
            
            # Mock model loading - in production this would be:
            # self.model = tf.keras.models.load_model('path/to/trained_model.h5')
            
            self.model = self._create_mock_model()
            print("Model loaded successfully")
            
        except Exception as e:
            print(f"Error loading model: {e}")
            self.model = None
    
    def _create_mock_model(self):
        """Create a mock model for demonstration purposes"""
        # This is a placeholder - in production, this would be a real trained model
        model = tf.keras.Sequential([
            tf.keras.layers.Input(shape=(224, 224, 3)),
            tf.keras.layers.Conv2D(32, 3, activation='relu'),
            tf.keras.layers.GlobalAveragePooling2D(),
            tf.keras.layers.Dense(len(self.component_classes) + len(self.violation_types), activation='sigmoid')
        ])
        return model
    
    def preprocess_image(self, image_path: str) -> np.ndarray:
        """Preprocess image for AI analysis"""
        try:
            # Load image using PIL
            image = Image.open(image_path)
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize to model input size
            image = image.resize((224, 224))
            
            # Convert to numpy array and normalize
            image_array = np.array(image) / 255.0
            
            # Add batch dimension
            image_array = np.expand_dims(image_array, axis=0)
            
            return image_array
            
        except Exception as e:
            raise Exception(f"Error preprocessing image: {e}")
    
    def detect_components(self, image_array: np.ndarray) -> List[Dict]:
        """Detect electrical components in the image"""
        try:
            # Mock component detection - in production this would use the real model
            detected_components = [
                {
                    'type': 'outlet',
                    'confidence': 0.92,
                    'bbox': [100, 150, 200, 250],  # x1, y1, x2, y2
                    'properties': {
                        'grounded': True,
                        'gfci_protected': False
                    }
                },
                {
                    'type': 'switch',
                    'confidence': 0.87,
                    'bbox': [300, 100, 350, 180],
                    'properties': {
                        'type': 'single_pole',
                        'properly_wired': True
                    }
                }
            ]
            
            return detected_components
            
        except Exception as e:
            print(f"Error detecting components: {e}")
            return []
    
    def check_code_violations(self, components: List[Dict], image_path: str) -> List[Dict]:
        """Check for electrical code violations"""
        violations = []
        
        try:
            # Mock violation detection logic
            for component in components:
                if component['type'] == 'outlet':
                    # Check for GFCI requirements (mock logic)
                    if not component['properties'].get('gfci_protected', False):
                        violations.append({
                            'type': 'missing_gfci',
                            'severity': 'high',
                            'description': 'GFCI protection may be required for this outlet location',
                            'code_reference': 'NEC 210.8',
                            'component_id': component.get('id'),
                            'confidence': 0.75
                        })
                
                elif component['type'] == 'junction_box':
                    # Check for overcrowding (mock logic)
                    violations.append({
                        'type': 'potential_overcrowding',
                        'severity': 'medium',
                        'description': 'Junction box may be overcrowded - verify wire fill calculations',
                        'code_reference': 'NEC 314.16',
                        'component_id': component.get('id'),
                        'confidence': 0.60
                    })
            
            return violations
            
        except Exception as e:
            print(f"Error checking violations: {e}")
            return []
    
    def calculate_overall_assessment(self, components: List[Dict], violations: List[Dict]) -> Dict:
        """Calculate overall pass/fail assessment"""
        try:
            high_severity_violations = [v for v in violations if v['severity'] == 'high']
            medium_severity_violations = [v for v in violations if v['severity'] == 'medium']
            
            # Determine overall result
            if len(high_severity_violations) > 0:
                overall_result = 'fail'
                confidence = 0.85
            elif len(medium_severity_violations) > 2:
                overall_result = 'warning'
                confidence = 0.70
            else:
                overall_result = 'pass'
                confidence = 0.90
            
            return {
                'overall_result': overall_result,
                'confidence': confidence,
                'summary': {
                    'components_detected': len(components),
                    'violations_found': len(violations),
                    'high_severity': len(high_severity_violations),
                    'medium_severity': len(medium_severity_violations)
                }
            }
            
        except Exception as e:
            print(f"Error calculating assessment: {e}")
            return {
                'overall_result': 'error',
                'confidence': 0.0,
                'summary': {}
            }
    
    def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """
        Main method to analyze an electrical installation image
        Returns comprehensive analysis results
        """
        try:
            # Load model if not already loaded
            if self.model is None:
                self.load_model()
            
            # Preprocess image
            image_array = self.preprocess_image(image_path)
            
            # Detect components
            components = self.detect_components(image_array)
            
            # Check for violations
            violations = self.check_code_violations(components, image_path)
            
            # Calculate overall assessment
            assessment = self.calculate_overall_assessment(components, violations)
            
            # Compile results
            analysis_result = {
                'detected_components': components,
                'violations_found': violations,
                'overall_result': assessment['overall_result'],
                'confidence_scores': {
                    'overall_confidence': assessment['confidence'],
                    'component_detection': np.mean([c['confidence'] for c in components]) if components else 0.0,
                    'violation_detection': np.mean([v['confidence'] for v in violations]) if violations else 1.0
                },
                'summary': assessment['summary'],
                'recommendations': self._generate_recommendations(violations),
                'analysis_metadata': {
                    'model_version': '1.0.0',
                    'analysis_timestamp': tf.timestamp().numpy(),
                    'image_dimensions': Image.open(image_path).size
                }
            }
            
            return analysis_result
            
        except Exception as e:
            return {
                'detected_components': [],
                'violations_found': [],
                'overall_result': 'error',
                'confidence_scores': {'overall_confidence': 0.0},
                'summary': {},
                'recommendations': [],
                'error': str(e)
            }
    
    def _generate_recommendations(self, violations: List[Dict]) -> List[str]:
        """Generate actionable recommendations based on violations"""
        recommendations = []
        
        for violation in violations:
            if violation['type'] == 'missing_gfci':
                recommendations.append("Install GFCI protection for outlets in wet locations (bathrooms, kitchens, garages, etc.)")
            elif violation['type'] == 'potential_overcrowding':
                recommendations.append("Verify junction box fill calculations per NEC 314.16 and consider larger box if needed")
            elif violation['type'] == 'improper_grounding':
                recommendations.append("Ensure proper grounding connections per NEC Article 250")
            else:
                recommendations.append(f"Address {violation['type']} - refer to {violation.get('code_reference', 'NEC')}")
        
        if not violations:
            recommendations.append("Installation appears to meet basic code requirements. Consider professional inspection for final verification.")
        
        return recommendations


class VideoAnalysisService:
    """
    AI service for analyzing electrical installation videos
    Processes video frames and provides temporal analysis
    """
    
    def __init__(self):
        self.image_service = ImageAnalysisService()
        self.frame_extraction_interval = 30  # Extract frame every 30 frames
    
    def extract_key_frames(self, video_path: str) -> List[str]:
        """Extract key frames from video for analysis"""
        try:
            cap = cv2.VideoCapture(video_path)
            frame_count = 0
            extracted_frames = []
            
            # Create temporary directory for frames
            temp_dir = os.path.join(os.path.dirname(video_path), 'temp_frames')
            os.makedirs(temp_dir, exist_ok=True)
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Extract frame at intervals
                if frame_count % self.frame_extraction_interval == 0:
                    frame_path = os.path.join(temp_dir, f'frame_{frame_count}.jpg')
                    cv2.imwrite(frame_path, frame)
                    extracted_frames.append(frame_path)
                
                frame_count += 1
            
            cap.release()
            
            # Get video duration
            fps = cap.get(cv2.CAP_PROP_FPS)
            duration = frame_count / fps if fps > 0 else 0
            
            return extracted_frames, duration
            
        except Exception as e:
            print(f"Error extracting frames: {e}")
            return [], 0
    
    def analyze_video(self, video_path: str) -> Dict[str, Any]:
        """
        Analyze electrical installation video
        Returns analysis of key frames and overall assessment
        """
        try:
            # Extract key frames
            frame_paths, duration = self.extract_key_frames(video_path)
            
            if not frame_paths:
                return {
                    'frame_analyses': [],
                    'overall_result': 'error',
                    'duration': 0,
                    'error': 'Could not extract frames from video'
                }
            
            # Analyze each frame
            frame_analyses = []
            all_components = []
            all_violations = []
            
            for i, frame_path in enumerate(frame_paths):
                try:
                    frame_analysis = self.image_service.analyze_image(frame_path)
                    frame_analyses.append({
                        'frame_number': i * self.frame_extraction_interval,
                        'timestamp': (i * self.frame_extraction_interval) / 30.0,  # Assuming 30 FPS
                        'analysis': frame_analysis
                    })
                    
                    # Collect components and violations
                    all_components.extend(frame_analysis.get('detected_components', []))
                    all_violations.extend(frame_analysis.get('violations_found', []))
                    
                except Exception as frame_error:
                    print(f"Error analyzing frame {i}: {frame_error}")
                    continue
            
            # Calculate overall video assessment
            overall_result = self._calculate_video_assessment(frame_analyses)
            
            # Clean up temporary frames
            self._cleanup_temp_frames(frame_paths)
            
            return {
                'frame_analyses': frame_analyses,
                'overall_result': overall_result,
                'duration': duration,
                'summary': {
                    'frames_analyzed': len(frame_analyses),
                    'total_components': len(all_components),
                    'total_violations': len(all_violations)
                }
            }
            
        except Exception as e:
            return {
                'frame_analyses': [],
                'overall_result': 'error',
                'duration': 0,
                'error': str(e)
            }
    
    def _calculate_video_assessment(self, frame_analyses: List[Dict]) -> str:
        """Calculate overall assessment for video based on frame analyses"""
        if not frame_analyses:
            return 'error'
        
        results = [frame['analysis'].get('overall_result', 'unknown') for frame in frame_analyses]
        
        # If any frame shows 'fail', overall is fail
        if 'fail' in results:
            return 'fail'
        # If any frame shows 'warning', overall is warning
        elif 'warning' in results:
            return 'warning'
        # If all frames pass, overall is pass
        elif all(result == 'pass' for result in results):
            return 'pass'
        else:
            return 'warning'
    
    def _cleanup_temp_frames(self, frame_paths: List[str]):
        """Clean up temporary frame files"""
        try:
            for frame_path in frame_paths:
                if os.path.exists(frame_path):
                    os.remove(frame_path)
            
            # Remove temp directory if empty
            temp_dir = os.path.dirname(frame_paths[0]) if frame_paths else None
            if temp_dir and os.path.exists(temp_dir) and not os.listdir(temp_dir):
                os.rmdir(temp_dir)
                
        except Exception as e:
            print(f"Error cleaning up temp frames: {e}")

