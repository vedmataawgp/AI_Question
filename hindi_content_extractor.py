"""
Hindi Content Extraction Module
Specialized for extracting specific relevant paragraphs from Hindi content
instead of returning full documents
"""

import re
from typing import List, Dict, Tuple
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class HindiContentExtractor:
    """
    Extract specific relevant paragraphs from Hindi content based on user questions
    """
    
    def __init__(self):
        # Hindi question keywords mapping
        self.hindi_keywords = {
            'how': ['कैसे', 'किस तरह', 'किस प्रकार', 'कैसे करें'],
            'what': ['क्या', 'कौन सा', 'कौन से', 'किस चीज़'],
            'when': ['कब', 'किस समय', 'कौन से समय'],
            'where': ['कहाँ', 'कहां', 'किस जगह', 'किस स्थान'],
            'why': ['क्यों', 'किस कारण', 'क्या वजह'],
            'who': ['कौन', 'किसने', 'किसका', 'किसकी']
        }
        
        # Common Hindi connectors and transition words
        self.connectors = [
            'इसके अलावा', 'इसके साथ', 'उदाहरण के लिए', 'जैसे कि', 
            'इसलिए', 'परंतु', 'लेकिन', 'तथा', 'और', 'या', 'अथवा'
        ]
        
        # Sentence endings in Hindi
        self.sentence_endings = ['।', '|', '.', '?', '!', '॥']
        
    def extract_relevant_paragraphs(self, question: str, content: str, max_paragraphs: int = 3) -> List[Dict]:
        """
        Extract specific relevant paragraphs from Hindi content based on question
        
        Args:
            question: User's question in Hindi/English
            content: Full content text in Hindi
            max_paragraphs: Maximum number of paragraphs to return
            
        Returns:
            List of relevant paragraph dictionaries with relevance scores
        """
        try:
            # Split content into paragraphs
            paragraphs = self._split_into_paragraphs(content)
            
            if not paragraphs:
                return []
            
            # Extract keywords from question
            question_keywords = self._extract_keywords(question)
            
            # Score each paragraph
            scored_paragraphs = []
            for i, paragraph in enumerate(paragraphs):
                score = self._calculate_relevance_score(question, paragraph, question_keywords)
                if score > 0.1:  # Only include paragraphs with meaningful relevance
                    scored_paragraphs.append({
                        'content': paragraph.strip(),
                        'relevance_score': score,
                        'paragraph_index': i,
                        'word_count': len(paragraph.split()),
                        'snippet': self._create_snippet(paragraph, question_keywords)
                    })
            
            # Sort by relevance score and return top paragraphs
            scored_paragraphs.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            # Apply additional filtering for quality
            filtered_paragraphs = self._filter_quality_paragraphs(scored_paragraphs[:max_paragraphs * 2])
            
            return filtered_paragraphs[:max_paragraphs]
            
        except Exception as e:
            logger.error(f"Error extracting Hindi paragraphs: {e}")
            return []
    
    def _split_into_paragraphs(self, content: str) -> List[str]:
        """Split content into meaningful paragraphs"""
        # First, split by double newlines (common paragraph separator)
        paragraphs = re.split(r'\n\s*\n', content.strip())
        
        # Further split long paragraphs by sentence endings
        refined_paragraphs = []
        for para in paragraphs:
            if len(para.split()) > 150:  # If paragraph is too long
                sentences = self._split_into_sentences(para)
                current_para = ""
                for sentence in sentences:
                    if len((current_para + " " + sentence).split()) <= 100:
                        current_para += " " + sentence if current_para else sentence
                    else:
                        if current_para:
                            refined_paragraphs.append(current_para.strip())
                        current_para = sentence
                if current_para:
                    refined_paragraphs.append(current_para.strip())
            else:
                refined_paragraphs.append(para.strip())
        
        # Filter out very short paragraphs
        return [p for p in refined_paragraphs if len(p.split()) >= 10]
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences using Hindi sentence endings"""
        # Create pattern for sentence endings
        pattern = '|'.join([re.escape(ending) for ending in self.sentence_endings])
        sentences = re.split(f'({pattern})', text)
        
        # Reconstruct sentences with their endings
        result = []
        for i in range(0, len(sentences) - 1, 2):
            if i + 1 < len(sentences):
                sentence = sentences[i] + sentences[i + 1]
                if sentence.strip():
                    result.append(sentence.strip())
        
        return result
    
    def _extract_keywords(self, question: str) -> List[str]:
        """Extract important keywords from the question"""
        # Remove common Hindi stop words
        stop_words = {
            'का', 'की', 'के', 'में', 'से', 'को', 'पर', 'है', 'हैं', 'था', 'थी', 'थे',
            'और', 'या', 'तथा', 'एक', 'यह', 'वह', 'इस', 'उस', 'ये', 'वे', 'सब',
            'कुछ', 'बहुत', 'सभी', 'जो', 'जिस', 'जिन', 'कि', 'तो', 'ही', 'भी',
            'the', 'is', 'are', 'was', 'were', 'and', 'or', 'in', 'on', 'at', 'to'
        }
        
        # Split question into words and filter
        words = re.findall(r'\b\w+\b', question.lower())
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Add question type indicators
        for q_type, indicators in self.hindi_keywords.items():
            for indicator in indicators:
                if indicator in question.lower():
                    keywords.append(indicator)
        
        return list(set(keywords))
    
    def _calculate_relevance_score(self, question: str, paragraph: str, question_keywords: List[str]) -> float:
        """Calculate relevance score between question and paragraph"""
        paragraph_lower = paragraph.lower()
        question_lower = question.lower()
        
        score = 0.0
        
        # Keyword matching
        keyword_matches = 0
        for keyword in question_keywords:
            if keyword in paragraph_lower:
                keyword_matches += 1
                # Give higher weight to exact matches
                score += 0.3
                # Additional points for multiple occurrences
                score += 0.1 * (paragraph_lower.count(keyword) - 1)
        
        # Keyword density bonus
        if keyword_matches > 0:
            keyword_density = keyword_matches / len(question_keywords)
            score += keyword_density * 0.5
        
        # Question type matching
        question_type_score = self._get_question_type_score(question_lower, paragraph_lower)
        score += question_type_score
        
        # Length factor (prefer medium-length paragraphs)
        word_count = len(paragraph.split())
        if 20 <= word_count <= 150:
            score += 0.2
        elif word_count > 150:
            score -= 0.1
        
        # Semantic proximity (simple word overlap)
        question_words = set(re.findall(r'\b\w+\b', question_lower))
        paragraph_words = set(re.findall(r'\b\w+\b', paragraph_lower))
        
        common_words = question_words.intersection(paragraph_words)
        if len(question_words) > 0:
            overlap_ratio = len(common_words) / len(question_words)
            score += overlap_ratio * 0.4
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _get_question_type_score(self, question: str, paragraph: str) -> float:
        """Calculate score based on question type matching"""
        score = 0.0
        
        # Check for question type indicators and corresponding answer patterns
        type_patterns = {
            'how': ['तरीका', 'विधि', 'प्रक्रिया', 'steps', 'method', 'process'],
            'what': ['परिभाषा', 'अर्थ', 'definition', 'meaning', 'है', 'होता'],
            'when': ['समय', 'तारीख', 'date', 'time', 'दिन', 'महीना'],
            'where': ['स्थान', 'जगह', 'location', 'place', 'address'],
            'why': ['कारण', 'वजह', 'reason', 'because', 'इसलिए'],
            'who': ['व्यक्ति', 'नाम', 'person', 'name', 'द्वारा']
        }
        
        for q_type, indicators in self.hindi_keywords.items():
            for indicator in indicators:
                if indicator in question:
                    # Check if paragraph contains relevant answer patterns
                    if q_type in type_patterns:
                        for pattern in type_patterns[q_type]:
                            if pattern in paragraph:
                                score += 0.3
                                break
                    break
        
        return score
    
    def _create_snippet(self, paragraph: str, keywords: List[str], max_length: int = 200) -> str:
        """Create a highlighted snippet from the paragraph"""
        snippet = paragraph[:max_length]
        if len(paragraph) > max_length:
            snippet += "..."
        
        # Highlight keywords (for display purposes)
        for keyword in keywords:
            if keyword in snippet.lower():
                # Create case-insensitive replacement
                pattern = re.compile(re.escape(keyword), re.IGNORECASE)
                snippet = pattern.sub(f"**{keyword}**", snippet)
        
        return snippet
    
    def _filter_quality_paragraphs(self, paragraphs: List[Dict]) -> List[Dict]:
        """Filter paragraphs for quality and diversity"""
        if not paragraphs:
            return []
        
        filtered = []
        used_content = set()
        
        for para in paragraphs:
            content = para['content']
            
            # Skip if too similar to already selected content
            is_duplicate = False
            for used in used_content:
                similarity = self._calculate_text_similarity(content, used)
                if similarity > 0.7:  # 70% similarity threshold
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                filtered.append(para)
                used_content.add(content)
        
        return filtered
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity between two texts"""
        words1 = set(re.findall(r'\b\w+\b', text1.lower()))
        words2 = set(re.findall(r'\b\w+\b', text2.lower()))
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def extract_context_paragraphs(self, main_paragraphs: List[Dict], full_content: str) -> List[Dict]:
        """
        Extract additional context paragraphs that might be useful
        """
        all_paragraphs = self._split_into_paragraphs(full_content)
        context_paragraphs = []
        
        for main_para in main_paragraphs:
            main_index = main_para['paragraph_index']
            
            # Get adjacent paragraphs for context
            for offset in [-1, 1]:
                context_index = main_index + offset
                if 0 <= context_index < len(all_paragraphs):
                    context_content = all_paragraphs[context_index]
                    if len(context_content.split()) >= 10:  # Minimum length
                        context_paragraphs.append({
                            'content': context_content.strip(),
                            'relevance_score': main_para['relevance_score'] * 0.5,  # Lower score
                            'paragraph_index': context_index,
                            'word_count': len(context_content.split()),
                            'is_context': True
                        })
        
        return context_paragraphs
    
    def format_answer_with_paragraphs(self, paragraphs: List[Dict], question: str) -> Dict:
        """
        Format the extracted paragraphs into a comprehensive answer
        """
        if not paragraphs:
            return {
                'answer': 'कोई प्रासंगिक जानकारी नहीं मिली।',
                'confidence': 0.0,
                'source_paragraphs': []
            }
        
        # Combine paragraphs into coherent answer
        answer_parts = []
        total_confidence = 0.0
        
        for i, para in enumerate(paragraphs):
            # Add paragraph number for reference
            paragraph_text = f"{i+1}. {para['content']}"
            answer_parts.append(paragraph_text)
            total_confidence += para['relevance_score']
        
        # Calculate average confidence
        avg_confidence = total_confidence / len(paragraphs)
        
        # Join paragraphs with proper spacing
        formatted_answer = '\n\n'.join(answer_parts)
        
        return {
            'answer': formatted_answer,
            'confidence': min(avg_confidence, 1.0),
            'source_paragraphs': len(paragraphs),
            'total_words': sum(para['word_count'] for para in paragraphs)
        }