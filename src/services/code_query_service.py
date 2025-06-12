import re
import json
import time
from typing import Dict, List, Any, Tuple
import numpy as np

class CodeQueryService:
    """
    AI service for processing electrical code queries
    Implements retrieval-augmented generation for NEC code questions
    """
    
    def __init__(self):
        self.nec_database = self._initialize_nec_database()
        self.common_patterns = self._initialize_query_patterns()
        
    def _initialize_nec_database(self) -> Dict[str, Any]:
        """Initialize mock NEC database with common code sections"""
        # In production, this would be a comprehensive vector database
        # with embeddings of the entire NEC code book
        return {
            "210.8": {
                "title": "Ground-Fault Circuit-Interrupter Protection for Personnel",
                "content": "Ground-fault circuit-interrupter protection for personnel shall be provided as required in 210.8(A) through (F). The ground-fault circuit-interrupter shall be installed in a readily accessible location.",
                "subsections": {
                    "210.8(A)": "Dwelling Units. All 125-volt, single-phase, 15- and 20-ampere receptacles installed in bathrooms, garages, outdoors, crawl spaces, basements, kitchens, and other specified locations shall have ground-fault circuit-interrupter protection for personnel.",
                    "210.8(B)": "Other Than Dwelling Units. All 125-volt, single-phase, 15-, 20-, and 30-ampere receptacles installed in bathrooms, kitchens, rooftops, outdoors, and other specified locations shall have ground-fault circuit-interrupter protection for personnel."
                },
                "keywords": ["gfci", "ground fault", "protection", "bathroom", "kitchen", "garage", "outdoor", "basement"]
            },
            "250.66": {
                "title": "Size of Alternating-Current Grounding Electrode Conductor",
                "content": "The size of the grounding electrode conductor of a grounded or ungrounded ac system shall not be less than given in Table 250.66, except as permitted in 250.66(A) through (C).",
                "keywords": ["grounding", "electrode", "conductor", "size", "table"]
            },
            "314.16": {
                "title": "Number of Conductors in Outlet, Device, and Junction Boxes, and Conduit Bodies",
                "content": "Boxes and conduit bodies shall be of sufficient size to provide free space for all enclosed conductors. In no case shall the volume of the box, as calculated in 314.16(A), be less than the fill calculation as calculated in 314.16(B).",
                "keywords": ["box fill", "conductors", "junction box", "outlet box", "volume", "calculation"]
            },
            "240.21": {
                "title": "Location in Circuit",
                "content": "Overcurrent protection shall be provided in each ungrounded conductor and shall be located at the point where the conductor to be protected receives its supply except as specified in 240.21(A) through (H).",
                "keywords": ["overcurrent", "protection", "breaker", "fuse", "conductor"]
            },
            "110.26": {
                "title": "Spaces About Electrical Equipment",
                "content": "Sufficient access and working space shall be provided and maintained about all electrical equipment to permit ready and safe operation and maintenance of such equipment.",
                "keywords": ["clearance", "working space", "electrical equipment", "panel", "access"]
            }
        }
    
    def _initialize_query_patterns(self) -> List[Dict]:
        """Initialize common query patterns and their responses"""
        return [
            {
                "pattern": r"(?i).*gfci.*(?:required|need|install).*",
                "response_template": "GFCI protection is required in specific locations per NEC 210.8. For dwelling units, GFCI protection is required for 125-volt, 15- and 20-ampere receptacles in: bathrooms, garages, outdoors, crawl spaces, unfinished basements, kitchens (countertop receptacles), laundry areas, utility rooms, and within 6 feet of sinks.",
                "primary_reference": "210.8"
            },
            {
                "pattern": r"(?i).*(?:grounding|ground).*(?:size|conductor|wire).*",
                "response_template": "The size of the grounding electrode conductor is determined by NEC Table 250.66, which bases the size on the largest ungrounded service-entrance conductor or equivalent area for parallel conductors.",
                "primary_reference": "250.66"
            },
            {
                "pattern": r"(?i).*(?:box fill|junction box|outlet box).*(?:calculation|size|conductors).*",
                "response_template": "Box fill calculations are covered in NEC 314.16. Each conductor, device, and fitting counts toward the box fill. The total volume must not exceed the box's rated capacity. Use Table 314.16(A) for standard box volumes and Table 314.16(B) for conductor volumes.",
                "primary_reference": "314.16"
            },
            {
                "pattern": r"(?i).*(?:clearance|working space|panel).*(?:distance|feet|inches).*",
                "response_template": "Working space requirements are specified in NEC 110.26. Generally, a minimum of 3 feet of clear working space is required in front of electrical equipment rated 600 volts or less. The width shall be at least 30 inches or the width of the equipment, whichever is greater.",
                "primary_reference": "110.26"
            }
        ]
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract relevant keywords from the query"""
        # Remove common stop words and extract meaningful terms
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'what', 'when', 'where', 'why', 'how'}
        
        # Convert to lowercase and split into words
        words = re.findall(r'\b\w+\b', query.lower())
        
        # Filter out stop words and short words
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        return keywords
    
    def _search_nec_sections(self, keywords: List[str]) -> List[Tuple[str, float]]:
        """Search NEC database for relevant sections based on keywords"""
        matches = []
        
        for section_id, section_data in self.nec_database.items():
            score = 0
            section_keywords = section_data.get('keywords', [])
            
            # Calculate relevance score
            for keyword in keywords:
                for section_keyword in section_keywords:
                    if keyword in section_keyword or section_keyword in keyword:
                        score += 1
                    elif keyword == section_keyword:
                        score += 2
            
            if score > 0:
                # Normalize score
                normalized_score = score / (len(keywords) + len(section_keywords))
                matches.append((section_id, normalized_score))
        
        # Sort by relevance score
        matches.sort(key=lambda x: x[1], reverse=True)
        
        return matches[:3]  # Return top 3 matches
    
    def _match_query_patterns(self, query: str) -> Dict[str, Any]:
        """Match query against common patterns"""
        for pattern_data in self.common_patterns:
            if re.match(pattern_data['pattern'], query):
                return {
                    'response': pattern_data['response_template'],
                    'primary_reference': pattern_data['primary_reference'],
                    'confidence': 0.85
                }
        
        return None
    
    def _generate_response(self, query: str, relevant_sections: List[Tuple[str, float]]) -> Dict[str, Any]:
        """Generate response based on relevant NEC sections"""
        if not relevant_sections:
            return {
                'response': "I couldn't find specific information about your query in my current database. Please refer to the official NEC code book or consult with a licensed electrician for detailed guidance.",
                'references': [],
                'confidence': 0.1
            }
        
        # Get the most relevant section
        primary_section = relevant_sections[0][0]
        primary_data = self.nec_database[primary_section]
        
        # Build response
        response_parts = []
        references = []
        
        # Add primary section information
        response_parts.append(f"According to NEC {primary_section} ({primary_data['title']}): {primary_data['content']}")
        references.append({
            'section': primary_section,
            'title': primary_data['title'],
            'relevance': relevant_sections[0][1]
        })
        
        # Add subsection information if available
        if 'subsections' in primary_data:
            for subsection_id, subsection_content in primary_data['subsections'].items():
                response_parts.append(f"\n\n{subsection_id}: {subsection_content}")
                references.append({
                    'section': subsection_id,
                    'title': f"{primary_data['title']} - Subsection",
                    'relevance': relevant_sections[0][1] * 0.9
                })
        
        # Add additional relevant sections
        for section_id, score in relevant_sections[1:]:
            section_data = self.nec_database[section_id]
            response_parts.append(f"\n\nAlso see NEC {section_id} ({section_data['title']}) for related requirements.")
            references.append({
                'section': section_id,
                'title': section_data['title'],
                'relevance': score
            })
        
        response = ''.join(response_parts)
        confidence = min(relevant_sections[0][1] * 1.2, 0.95)  # Cap confidence at 95%
        
        return {
            'response': response,
            'references': references,
            'confidence': confidence
        }
    
    def _enhance_response_with_context(self, response_data: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Enhance response with additional context and recommendations"""
        enhanced_response = response_data['response']
        
        # Add practical recommendations based on query type
        if any(keyword in query.lower() for keyword in ['install', 'installation', 'how to']):
            enhanced_response += "\n\n💡 Practical Tip: Always verify local code requirements as they may be more restrictive than the NEC. Consider consulting with a licensed electrician for complex installations."
        
        if any(keyword in query.lower() for keyword in ['gfci', 'ground fault']):
            enhanced_response += "\n\n⚠️ Safety Note: GFCI devices should be tested monthly using the TEST and RESET buttons to ensure proper operation."
        
        if any(keyword in query.lower() for keyword in ['wire size', 'conductor size', 'ampacity']):
            enhanced_response += "\n\n📏 Sizing Note: Always consider voltage drop calculations for long wire runs and ensure proper derating for multiple conductors in conduit."
        
        response_data['response'] = enhanced_response
        return response_data
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Main method to process electrical code queries
        Returns comprehensive response with NEC references
        """
        try:
            # First, try to match against common patterns
            pattern_match = self._match_query_patterns(query)
            if pattern_match:
                # Get detailed information for the matched section
                section_data = self.nec_database.get(pattern_match['primary_reference'], {})
                enhanced_response = self._enhance_response_with_context({
                    'response': pattern_match['response'],
                    'references': [{
                        'section': pattern_match['primary_reference'],
                        'title': section_data.get('title', 'NEC Section'),
                        'relevance': pattern_match['confidence']
                    }],
                    'confidence': pattern_match['confidence']
                }, query)
                return enhanced_response
            
            # Extract keywords from query
            keywords = self._extract_keywords(query)
            
            if not keywords:
                return {
                    'response': "I need more specific information to help you. Please ask about specific electrical components, installations, or code requirements.",
                    'references': [],
                    'confidence': 0.1
                }
            
            # Search for relevant NEC sections
            relevant_sections = self._search_nec_sections(keywords)
            
            # Generate response
            response_data = self._generate_response(query, relevant_sections)
            
            # Enhance with additional context
            enhanced_response = self._enhance_response_with_context(response_data, query)
            
            return enhanced_response
            
        except Exception as e:
            return {
                'response': f"I encountered an error processing your query: {str(e)}. Please try rephrasing your question or refer to the official NEC code book.",
                'references': [],
                'confidence': 0.0,
                'error': str(e)
            }
    
    def get_related_queries(self, query: str) -> List[str]:
        """Generate related query suggestions"""
        keywords = self._extract_keywords(query)
        
        related_queries = []
        
        # Generate related questions based on keywords
        if any(keyword in ['gfci', 'ground', 'fault'] for keyword in keywords):
            related_queries.extend([
                "Where are GFCI outlets required in a kitchen?",
                "What is the difference between GFCI and AFCI?",
                "How do I test a GFCI outlet?"
            ])
        
        if any(keyword in ['wire', 'conductor', 'size'] for keyword in keywords):
            related_queries.extend([
                "How do I calculate wire size for a circuit?",
                "What is the ampacity of 12 AWG wire?",
                "When do I need to derate wire ampacity?"
            ])
        
        if any(keyword in ['box', 'fill', 'junction'] for keyword in keywords):
            related_queries.extend([
                "How many wires can fit in a junction box?",
                "What size box do I need for 6 conductors?",
                "How do I calculate box fill for devices?"
            ])
        
        return related_queries[:5]  # Return up to 5 related queries

