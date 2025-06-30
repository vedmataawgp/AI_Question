"""
Advanced Transformer-based NLP processor for better semantic understanding
Uses open-source models for improved question-answer matching
"""

import logging
import numpy as np
from typing import List, Dict, Tuple, Optional
import re
import json
from datetime import datetime

# Import with fallback handling
try:
    from transformers import AutoTokenizer, AutoModel
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

class TransformerNLP:
    """Advanced NLP processor using transformer models for semantic understanding"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.model = None
        self.tokenizer = None
        self.device = 'cpu'  # Use CPU for compatibility
        self.model_name = 'sentence-transformers/all-MiniLM-L6-v2'  # Lightweight model
        self.max_length = 512
        
        self._load_model()
    
    def _load_model(self):
        """Load transformer model with fallback"""
        if not TRANSFORMERS_AVAILABLE:
            self.logger.warning("Transformers not available, using fallback similarity")
            return
        
        try:
            # Try to load a lightweight sentence transformer model
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModel.from_pretrained(self.model_name)
            self.model.eval()
            self.logger.info(f"Loaded transformer model: {self.model_name}")
        except Exception as e:
            self.logger.warning(f"Could not load transformer model: {e}")
            # Try alternative models
            try:
                self.model_name = 'distilbert-base-uncased'
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                self.model = AutoModel.from_pretrained(self.model_name)
                self.model.eval()
                self.logger.info(f"Loaded fallback model: {self.model_name}")
            except Exception as e2:
                self.logger.error(f"Could not load any transformer model: {e2}")
                self.model = None
                self.tokenizer = None
    
    def get_embeddings(self, text: str) -> Optional[np.ndarray]:
        """Get embeddings for text using transformer model"""
        if not self.model or not self.tokenizer:
            return None
        
        try:
            # Tokenize and encode
            inputs = self.tokenizer(
                text,
                return_tensors='pt',
                max_length=self.max_length,
                truncation=True,
                padding=True
            )
            
            # Get embeddings
            with torch.no_grad():
                outputs = self.model(**inputs)
                # Use mean pooling of last hidden states
                embeddings = outputs.last_hidden_state.mean(dim=1)
                return embeddings.numpy().flatten()
        
        except Exception as e:
            self.logger.error(f"Error getting embeddings: {e}")
            return None
    
    def calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity using transformer embeddings"""
        if not self.model:
            return self._fallback_similarity(text1, text2)
        
        try:
            emb1 = self.get_embeddings(text1)
            emb2 = self.get_embeddings(text2)
            
            if emb1 is None or emb2 is None:
                return self._fallback_similarity(text1, text2)
            
            # Cosine similarity
            similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
            return float(similarity)
        
        except Exception as e:
            self.logger.error(f"Error calculating similarity: {e}")
            return self._fallback_similarity(text1, text2)
    
    def _fallback_similarity(self, text1: str, text2: str) -> float:
        """Fallback similarity calculation using basic text matching"""
        # Convert to lowercase and split into words
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        # Jaccard similarity
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def extract_entities(self, text: str) -> List[Dict]:
        """Extract named entities and key phrases"""
        entities = []
        
        # Simple pattern-based entity extraction
        patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'url': r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
            'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            'date': r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b'
        }
        
        for entity_type, pattern in patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entities.append({
                    'type': entity_type,
                    'text': match.group(),
                    'start': match.start(),
                    'end': match.end()
                })
        
        return entities
    
    def generate_query_expansion(self, query: str) -> List[str]:
        """Generate expanded queries for better matching"""
        expanded_queries = [query]
        
        # Simple expansion techniques
        words = query.lower().split()
        
        # Add synonyms and variations
        expansions = {
            'how': ['what is the way to', 'what are the steps to', 'guide for'],
            'what': ['define', 'explain', 'tell me about'],
            'why': ['reason for', 'cause of', 'explanation for'],
            'when': ['time for', 'schedule for', 'timing of'],
            'where': ['location of', 'place for', 'find'],
            'fix': ['solve', 'repair', 'troubleshoot', 'resolve'],
            'error': ['problem', 'issue', 'bug', 'exception'],
            'install': ['setup', 'configure', 'add', 'enable']
        }
        
        for word in words:
            if word in expansions:
                for expansion in expansions[word]:
                    new_query = query.replace(word, expansion, 1)
                    if new_query != query:
                        expanded_queries.append(new_query)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_queries = []
        for q in expanded_queries:
            if q not in seen:
                seen.add(q)
                unique_queries.append(q)
        
        return unique_queries[:5]  # Limit to 5 expansions
    
    def rank_answers(self, question: str, answers: List[Dict]) -> List[Tuple[Dict, float]]:
        """Rank answers using advanced scoring"""
        if not answers:
            return []
        
        scored_answers = []
        
        for answer in answers:
            # Combine title and content for matching
            answer_text = f"{answer.get('title', '')} {answer.get('content', '')}"
            
            # Calculate multiple similarity scores
            semantic_score = self.calculate_semantic_similarity(question, answer_text)
            
            # Title matching bonus
            title_score = self.calculate_semantic_similarity(question, answer.get('title', ''))
            
            # Content length factor (prefer comprehensive answers)
            content_length = len(answer.get('content', ''))
            length_factor = min(1.0, content_length / 500)  # Normalize to 500 chars
            
            # Entity matching bonus
            question_entities = self.extract_entities(question)
            answer_entities = self.extract_entities(answer_text)
            
            entity_match_score = 0.0
            if question_entities and answer_entities:
                q_entity_texts = {e['text'].lower() for e in question_entities}
                a_entity_texts = {e['text'].lower() for e in answer_entities}
                common_entities = q_entity_texts.intersection(a_entity_texts)
                entity_match_score = len(common_entities) / max(len(q_entity_texts), 1)
            
            # Combined score with weights
            final_score = (
                semantic_score * 0.5 +
                title_score * 0.2 +
                length_factor * 0.1 +
                entity_match_score * 0.2
            )
            
            scored_answers.append((answer, final_score))
        
        # Sort by score (descending)
        scored_answers.sort(key=lambda x: x[1], reverse=True)
        
        return scored_answers
    
    def preprocess_text_advanced(self, text: str) -> str:
        """Advanced text preprocessing for better matching"""
        if not text:
            return ""
        
        # Basic cleaning
        text = re.sub(r'\s+', ' ', text)  # Multiple spaces to single
        text = re.sub(r'[^\w\s]', ' ', text)  # Remove punctuation
        text = text.lower().strip()
        
        # Remove common stop words (basic set)
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'this', 'that', 'these', 'those', 'is', 'are',
            'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do',
            'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might'
        }
        
        words = text.split()
        filtered_words = [word for word in words if word not in stop_words and len(word) > 1]
        
        return ' '.join(filtered_words)
    
    def get_answer_confidence(self, question: str, answer: Dict, score: float) -> Dict:
        """Get detailed confidence metrics for an answer"""
        answer_text = f"{answer.get('title', '')} {answer.get('content', '')}"
        
        confidence_metrics = {
            'overall_score': score,
            'confidence_level': 'low',
            'semantic_similarity': self.calculate_semantic_similarity(question, answer_text),
            'title_relevance': self.calculate_semantic_similarity(question, answer.get('title', '')),
            'content_length_score': min(1.0, len(answer.get('content', '')) / 500),
            'entity_matches': len(self.extract_entities(question))
        }
        
        # Determine confidence level
        if score >= 0.8:
            confidence_metrics['confidence_level'] = 'very_high'
        elif score >= 0.6:
            confidence_metrics['confidence_level'] = 'high'
        elif score >= 0.4:
            confidence_metrics['confidence_level'] = 'medium'
        elif score >= 0.2:
            confidence_metrics['confidence_level'] = 'low'
        else:
            confidence_metrics['confidence_level'] = 'very_low'
        
        return confidence_metrics