"""
Simple reranker based on keyword matching and semantic score combination
"""
import re
from typing import List, Dict, Any

class SimpleReranker:
    """
    Simple reranker that combines:
    1. Vector similarity score
    2. Keyword matching score
    3. Price range matching (أولوية أكبر)
    """
    
    def __init__(self):
        # Common Arabic car-related terms mapping
        self.arabic_mappings = {
            'كهربا': ['electric', 'ev', 'battery'],
            'بنزين': ['petrol', 'gasoline', 'fuel'],
            'ديزل': ['diesel'],
            'اوتوماتيك': ['automatic', 'cvt', 'at'],
            'مانيوال': ['manual', 'mt'],
            'سيدان': ['sedan'],
            'suv': ['suv', 'crossover'],
            'هاتشباك': ['hatchback'],
            'دفع رباعي': ['awd', '4wd', 'four wheel'],
            'دفع امامي': ['fwd', 'front wheel'],
        }
        
    def extract_query_features(self, query: str) -> Dict[str, Any]:
        """Extract features from user query"""
        query_lower = query.lower()
        features = {
            'fuel_preference': None,
            'transmission': None,
            'body_type': None,
            'price_max': None,
            'keywords': []
        }
        
        # Fuel type
        if any(term in query_lower for term in ['كهربا', 'electric', 'ev']):
            features['fuel_preference'] = 'electric'
        elif any(term in query_lower for term in ['بنزين', 'petrol', 'gasoline']):
            features['fuel_preference'] = 'petrol'
        
        # Transmission
        if any(term in query_lower for term in ['اوتوماتيك', 'automatic', 'cvt']):
            features['transmission'] = 'automatic'
        elif any(term in query_lower for term in ['مانيوال', 'manual']):
            features['transmission'] = 'manual'
        
        # Body type
        if any(term in query_lower for term in ['سيدان', 'sedan']):
            features['body_type'] = 'sedan'
        elif 'suv' in query_lower:
            features['body_type'] = 'suv'
        
        return features
    
    def calculate_keyword_score(self, result_text: str, query: str) -> float:
        """Calculate keyword matching score"""
        query_words = set(query.lower().split())
        result_words = set(result_text.lower().split())
        
        # Remove common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}
        query_words -= stop_words
        
        if not query_words:
            return 0.0
        
        matches = query_words & result_words
        return len(matches) / len(query_words)
    
    def calculate_feature_score(self, result: Any, query_features: Dict) -> float:
        """Calculate score based on extracted features with price priority"""
        score = 0.0
        max_score = 0.0
        
        result_text = result.text.lower()
        
        # Fuel type matching
        if query_features['fuel_preference']:
            max_score += 2.0
            if query_features['fuel_preference'] in result_text:
                score += 2.0
        
        # Transmission matching
        if query_features['transmission']:
            max_score += 1.0
            if query_features['transmission'] in result_text:
                score += 1.0
        
        # Body type matching
        if query_features['body_type']:
            max_score += 1.0
            if query_features['body_type'] in result_text:
                score += 1.0
        
        if query_features['price_max']:
            max_score += 3.0
            price_match = re.search(r'([\d,]+)\s*egp', result_text, re.IGNORECASE)
            if price_match:
                try:
                    result_price = int(price_match.group(1).replace(',', ''))
                    if result_price <= query_features['price_max']:
                        ratio = result_price / query_features['price_max']
                        score += 3.0 * (1.0 - ratio * 0.3)
                except:
                    pass
        
        # Normalize
        return score / max_score if max_score > 0 else 0.0
    
    def rerank(self, results: List[Any], query: str, top_k: int = 5) -> List[Any]:
        """
        Rerank results based on:
        - Original vector similarity
        - Keyword matching
        - Feature matching (السعر له أولوية)
        """
        if not results:
            return []
        
        query_features = self.extract_query_features(query)
        
        scored_results = []
        for result in results:
            # Original similarity score (normalized to 0-1)
            vector_score = result.score
            
            # Keyword matching score
            keyword_score = self.calculate_keyword_score(result.text, query)
            
            # Feature matching score
            feature_score = self.calculate_feature_score(result, query_features)
            
            # Combined score with weights
            combined_score = (
                vector_score * 0.5 +
                keyword_score * 0.1 +
                feature_score * 0.4
            )
            
            scored_results.append({
                'result': result,
                'combined_score': combined_score,
                'vector_score': vector_score,
                'keyword_score': keyword_score,
                'feature_score': feature_score
            })
        
        # Sort by combined score
        scored_results.sort(key=lambda x: x['combined_score'], reverse=True)
        
        # Return top_k results
        reranked = [item['result'] for item in scored_results[:top_k]]
        
        # Update scores in results
        for i, item in enumerate(scored_results[:top_k]):
            reranked[i].score = item['combined_score']
        
        return reranked
