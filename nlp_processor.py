import spacy
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re
from typing import List, Tuple, Dict

class NLPProcessor:
    """NLP processor for question matching and answer ranking"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.nlp = None
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 2),
            lowercase=True
        )
        self.content_vectors = None
        self.content_items_cache = []
        self._load_spacy_model()
    
    def _load_spacy_model(self):
        """Load spaCy model with fallback"""
        try:
            # Try to load the large English model first
            self.nlp = spacy.load("en_core_web_lg")
            self.logger.info("Loaded en_core_web_lg spaCy model")
        except OSError:
            try:
                # Fallback to medium model
                self.nlp = spacy.load("en_core_web_md")
                self.logger.info("Loaded en_core_web_md spaCy model")
            except OSError:
                try:
                    # Fallback to small model
                    self.nlp = spacy.load("en_core_web_sm")
                    self.logger.info("Loaded en_core_web_sm spaCy model")
                except OSError:
                    # Create a blank model as last resort
                    self.nlp = spacy.blank("en")
                    self.logger.warning("Using blank spaCy model - install en_core_web_sm for better results")
    
    def preprocess_text(self, text: str) -> str:
        """Preprocess text for better matching"""
        if not text:
            return ""
        
        # Basic cleaning
        text = re.sub(r'\s+', ' ', text)  # Multiple spaces to single space
        text = re.sub(r'[^\w\s]', ' ', text)  # Remove punctuation
        text = text.lower().strip()
        
        if self.nlp and hasattr(self.nlp, 'vocab'):
            # Use spaCy for advanced preprocessing
            doc = self.nlp(text)
            # Extract lemmatized tokens, excluding stop words and punctuation
            tokens = [token.lemma_ for token in doc 
                     if not token.is_stop and not token.is_punct and len(token.text) > 1]
            return ' '.join(tokens)
        else:
            # Basic preprocessing without spaCy
            return text
    
    def get_semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts using spaCy"""
        if not self.nlp or not hasattr(self.nlp, 'vocab'):
            return self._basic_similarity(text1, text2)
        
        try:
            doc1 = self.nlp(text1)
            doc2 = self.nlp(text2)
            
            # Check if the model has word vectors
            if doc1.has_vector and doc2.has_vector:
                return doc1.similarity(doc2)
            else:
                return self._basic_similarity(text1, text2)
        except Exception as e:
            self.logger.warning(f"Error calculating semantic similarity: {e}")
            return self._basic_similarity(text1, text2)
    
    def _basic_similarity(self, text1: str, text2: str) -> float:
        """Basic similarity calculation using TF-IDF and cosine similarity"""
        try:
            texts = [text1, text2]
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(texts)
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
            return float(similarity[0][0])
        except Exception as e:
            self.logger.warning(f"Error in basic similarity calculation: {e}")
            return 0.0
    
    def build_content_index(self, content_items: List[Dict]) -> None:
        """Build TF-IDF index for content items"""
        self.logger.info(f"Building content index for {len(content_items)} items")
        
        if not content_items:
            self.content_vectors = None
            self.content_items_cache = []
            return
        
        # Prepare content texts
        content_texts = []
        self.content_items_cache = []
        
        for item in content_items:
            # Combine title and content for better matching
            combined_text = f"{item.get('title', '')} {item.get('content', '')}"
            processed_text = self.preprocess_text(combined_text)
            content_texts.append(processed_text)
            self.content_items_cache.append(item)
        
        try:
            # Build TF-IDF vectors
            self.content_vectors = self.tfidf_vectorizer.fit_transform(content_texts)
            self.logger.info("Content index built successfully")
        except Exception as e:
            self.logger.error(f"Error building content index: {e}")
            self.content_vectors = None
            self.content_items_cache = []
    
    def find_best_answers(self, question: str, top_k: int = 5) -> List[Tuple[Dict, float]]:
        """Find best matching answers for a question"""
        if not self.content_vectors or not self.content_items_cache:
            self.logger.warning("Content index not built or empty")
            return []
        
        try:
            # Preprocess the question
            processed_question = self.preprocess_text(question)
            
            # Transform question using the same vectorizer
            question_vector = self.tfidf_vectorizer.transform([processed_question])
            
            # Calculate cosine similarities
            similarities = cosine_similarity(question_vector, self.content_vectors).flatten()
            
            # Get top-k most similar items
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            results = []
            for idx in top_indices:
                if similarities[idx] > 0.0:  # Only include items with some similarity
                    # Calculate additional semantic similarity if possible
                    semantic_score = self.get_semantic_similarity(
                        question, 
                        f"{self.content_items_cache[idx].get('title', '')} {self.content_items_cache[idx].get('content', '')}"
                    )
                    
                    # Combine TF-IDF and semantic scores
                    combined_score = (similarities[idx] * 0.7) + (semantic_score * 0.3)
                    
                    results.append((self.content_items_cache[idx], combined_score))
            
            self.logger.info(f"Found {len(results)} potential answers for question")
            return results
            
        except Exception as e:
            self.logger.error(f"Error finding best answers: {e}")
            return []
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text using spaCy"""
        if not self.nlp:
            return []
        
        try:
            doc = self.nlp(text)
            keywords = []
            
            # Extract named entities
            for ent in doc.ents:
                if ent.label_ in ['PERSON', 'ORG', 'PRODUCT', 'EVENT', 'WORK_OF_ART']:
                    keywords.append(ent.text)
            
            # Extract noun phrases
            for chunk in doc.noun_chunks:
                if len(chunk.text.split()) <= 3:  # Short noun phrases
                    keywords.append(chunk.text)
            
            # Extract important tokens
            for token in doc:
                if (token.pos_ in ['NOUN', 'PROPN', 'ADJ'] and 
                    not token.is_stop and 
                    len(token.text) > 2):
                    keywords.append(token.lemma_)
            
            # Remove duplicates and return
            return list(set(keywords))
            
        except Exception as e:
            self.logger.warning(f"Error extracting keywords: {e}")
            return []
