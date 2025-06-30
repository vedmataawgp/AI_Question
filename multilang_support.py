"""
Multi-language support for questions and answers
Handles translation and language detection for international users
"""

import logging
import re
from typing import Dict, List, Optional, Tuple
import json

# Simple language detection and translation without external APIs
class MultiLanguageProcessor:
    """Multi-language processor for Q&A system"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Language patterns for basic detection
        self.language_patterns = {
            'spanish': {
                'keywords': ['qué', 'cómo', 'por qué', 'cuándo', 'dónde', 'quién', 'cuál', 'es', 'son', 'está', 'estoy', 'tiene', 'hay'],
                'common_words': ['el', 'la', 'los', 'las', 'de', 'del', 'en', 'con', 'para', 'por', 'que', 'se', 'no', 'un', 'una'],
                'code': 'es'
            },
            'french': {
                'keywords': ['qu\'est-ce', 'comment', 'pourquoi', 'quand', 'où', 'qui', 'quel', 'quelle', 'est', 'sont', 'avoir', 'être'],
                'common_words': ['le', 'la', 'les', 'de', 'du', 'des', 'en', 'avec', 'pour', 'par', 'que', 'qui', 'ne', 'un', 'une'],
                'code': 'fr'
            },
            'german': {
                'keywords': ['was', 'wie', 'warum', 'wann', 'wo', 'wer', 'welche', 'ist', 'sind', 'haben', 'sein'],
                'common_words': ['der', 'die', 'das', 'den', 'dem', 'des', 'ein', 'eine', 'und', 'oder', 'aber', 'in', 'auf', 'mit'],
                'code': 'de'
            },
            'italian': {
                'keywords': ['che cosa', 'come', 'perché', 'quando', 'dove', 'chi', 'quale', 'è', 'sono', 'avere', 'essere'],
                'common_words': ['il', 'la', 'lo', 'gli', 'le', 'di', 'del', 'della', 'in', 'con', 'per', 'da', 'che', 'un', 'una'],
                'code': 'it'
            },
            'portuguese': {
                'keywords': ['o que', 'como', 'por que', 'quando', 'onde', 'quem', 'qual', 'é', 'são', 'ter', 'ser'],
                'common_words': ['o', 'a', 'os', 'as', 'de', 'do', 'da', 'em', 'com', 'para', 'por', 'que', 'não', 'um', 'uma'],
                'code': 'pt'
            },
            'russian': {
                'keywords': ['что', 'как', 'почему', 'когда', 'где', 'кто', 'какой', 'это', 'быть', 'иметь'],
                'common_words': ['в', 'на', 'с', 'по', 'для', 'от', 'до', 'и', 'или', 'но', 'не', 'я', 'ты', 'он', 'она'],
                'code': 'ru'
            },
            'chinese': {
                'keywords': ['什么', '如何', '为什么', '什么时候', '在哪里', '谁', '哪个', '是', '有', '会'],
                'common_words': ['的', '了', '在', '是', '我', '有', '他', '这', '个', '们', '中', '到', '和', '地'],
                'code': 'zh'
            },
            'japanese': {
                'keywords': ['何', 'どう', 'なぜ', 'いつ', 'どこ', '誰', 'どの', 'です', 'である', 'ある'],
                'common_words': ['の', 'に', 'は', 'を', 'が', 'で', 'と', 'から', 'まで', 'より', 'も', 'か', 'な', 'よ'],
                'code': 'ja'
            }
        }
        
        # Basic translation dictionaries for common question patterns
        self.translations = {
            'en': {
                'question_patterns': {
                    'how_to': 'how to',
                    'what_is': 'what is',
                    'why_does': 'why does',
                    'when_should': 'when should',
                    'where_can': 'where can'
                }
            },
            'es': {
                'question_patterns': {
                    'how_to': 'cómo',
                    'what_is': 'qué es',
                    'why_does': 'por qué',
                    'when_should': 'cuándo debería',
                    'where_can': 'dónde puedo'
                }
            },
            'fr': {
                'question_patterns': {
                    'how_to': 'comment',
                    'what_is': 'qu\'est-ce que',
                    'why_does': 'pourquoi',
                    'when_should': 'quand devrais',
                    'where_can': 'où puis-je'
                }
            },
            'de': {
                'question_patterns': {
                    'how_to': 'wie',
                    'what_is': 'was ist',
                    'why_does': 'warum',
                    'when_should': 'wann sollte',
                    'where_can': 'wo kann'
                }
            }
        }
    
    def detect_language(self, text: str) -> str:
        """Detect language of input text"""
        if not text:
            return 'en'
        
        text_lower = text.lower()
        scores = {}
        
        # Score each language based on keyword and common word matches
        for lang_name, patterns in self.language_patterns.items():
            score = 0
            
            # Check keywords
            for keyword in patterns['keywords']:
                if keyword in text_lower:
                    score += 3
            
            # Check common words
            for word in patterns['common_words']:
                if f' {word} ' in f' {text_lower} ':
                    score += 1
            
            scores[patterns['code']] = score
        
        # Return language with highest score, default to English
        if scores:
            best_lang = max(scores.items(), key=lambda x: x[1])
            return best_lang[0] if best_lang[1] > 0 else 'en'
        
        return 'en'
    
    def get_supported_languages(self) -> List[Dict]:
        """Get list of supported languages"""
        languages = [
            {'code': 'en', 'name': 'English', 'native_name': 'English'},
            {'code': 'es', 'name': 'Spanish', 'native_name': 'Español'},
            {'code': 'fr', 'name': 'French', 'native_name': 'Français'},
            {'code': 'de', 'name': 'German', 'native_name': 'Deutsch'},
            {'code': 'it', 'name': 'Italian', 'native_name': 'Italiano'},
            {'code': 'pt', 'name': 'Portuguese', 'native_name': 'Português'},
            {'code': 'ru', 'name': 'Russian', 'native_name': 'Русский'},
            {'code': 'zh', 'name': 'Chinese', 'native_name': '中文'},
            {'code': 'ja', 'name': 'Japanese', 'native_name': '日本語'}
        ]
        return languages
    
    def normalize_question(self, question: str, source_lang: str = None) -> str:
        """Normalize question to improve matching across languages"""
        if not source_lang:
            source_lang = self.detect_language(question)
        
        # Basic normalization
        normalized = question.lower().strip()
        
        # Remove language-specific articles and common words that don't affect meaning
        if source_lang in self.language_patterns:
            common_words = self.language_patterns[source_lang]['common_words']
            words = normalized.split()
            filtered_words = []
            
            for word in words:
                # Keep question words and content words, filter out articles/prepositions
                if word not in common_words[:10]:  # Keep only major articles/prepositions
                    filtered_words.append(word)
            
            normalized = ' '.join(filtered_words)
        
        return normalized
    
    def get_language_specific_suggestions(self, lang_code: str) -> List[str]:
        """Get language-specific question suggestions"""
        suggestions = {
            'en': [
                "How to fix login issues?",
                "What is the setup process?",
                "Why is the system slow?",
                "When should I update?",
                "Where can I find documentation?"
            ],
            'es': [
                "¿Cómo solucionar problemas de acceso?",
                "¿Qué es el proceso de configuración?",
                "¿Por qué el sistema es lento?",
                "¿Cuándo debería actualizar?",
                "¿Dónde puedo encontrar documentación?"
            ],
            'fr': [
                "Comment résoudre les problèmes de connexion?",
                "Qu'est-ce que le processus de configuration?",
                "Pourquoi le système est-il lent?",
                "Quand devrais-je mettre à jour?",
                "Où puis-je trouver la documentation?"
            ],
            'de': [
                "Wie kann ich Anmeldeprobleme beheben?",
                "Was ist der Einrichtungsprozess?",
                "Warum ist das System langsam?",
                "Wann sollte ich aktualisieren?",
                "Wo finde ich die Dokumentation?"
            ]
        }
        
        return suggestions.get(lang_code, suggestions['en'])
    
    def extract_question_intent(self, question: str, lang_code: str = None) -> Dict:
        """Extract intent from question in any language"""
        if not lang_code:
            lang_code = self.detect_language(question)
        
        question_lower = question.lower()
        
        # Intent patterns for different languages
        intent_patterns = {
            'how_to': {
                'en': ['how to', 'how do i', 'how can i', 'steps to', 'guide to'],
                'es': ['cómo', 'como hacer', 'pasos para', 'guía para'],
                'fr': ['comment', 'comment faire', 'étapes pour', 'guide pour'],
                'de': ['wie', 'wie kann ich', 'schritte zu', 'anleitung für']
            },
            'what_is': {
                'en': ['what is', 'what are', 'define', 'explain'],
                'es': ['qué es', 'qué son', 'definir', 'explicar'],
                'fr': ['qu\'est-ce que', 'que sont', 'définir', 'expliquer'],
                'de': ['was ist', 'was sind', 'definieren', 'erklären']
            },
            'troubleshoot': {
                'en': ['fix', 'solve', 'troubleshoot', 'error', 'problem', 'issue'],
                'es': ['solucionar', 'arreglar', 'error', 'problema'],
                'fr': ['réparer', 'résoudre', 'erreur', 'problème'],
                'de': ['reparieren', 'lösen', 'fehler', 'problem']
            },
            'where': {
                'en': ['where', 'location', 'find'],
                'es': ['dónde', 'ubicación', 'encontrar'],
                'fr': ['où', 'emplacement', 'trouver'],
                'de': ['wo', 'standort', 'finden']
            },
            'when': {
                'en': ['when', 'time', 'schedule'],
                'es': ['cuándo', 'tiempo', 'horario'],
                'fr': ['quand', 'temps', 'horaire'],
                'de': ['wann', 'zeit', 'zeitplan']
            }
        }
        
        detected_intents = []
        
        for intent, patterns in intent_patterns.items():
            lang_patterns = patterns.get(lang_code, patterns.get('en', []))
            for pattern in lang_patterns:
                if pattern in question_lower:
                    detected_intents.append(intent)
                    break
        
        return {
            'detected_language': lang_code,
            'intents': detected_intents,
            'primary_intent': detected_intents[0] if detected_intents else 'general'
        }
    
    def get_multilang_response_template(self, lang_code: str) -> Dict:
        """Get response templates for different languages"""
        templates = {
            'en': {
                'no_results': "No matching answers found. Try rephrasing your question.",
                'multiple_results': "Found {count} relevant answers:",
                'confidence_high': "High confidence match",
                'confidence_medium': "Medium confidence match",
                'confidence_low': "Low confidence match",
                'feedback_helpful': "Was this helpful?",
                'yes': "Yes",
                'no': "No"
            },
            'es': {
                'no_results': "No se encontraron respuestas. Intenta reformular tu pregunta.",
                'multiple_results': "Se encontraron {count} respuestas relevantes:",
                'confidence_high': "Coincidencia de alta confianza",
                'confidence_medium': "Coincidencia de confianza media",
                'confidence_low': "Coincidencia de baja confianza",
                'feedback_helpful': "¿Fue esto útil?",
                'yes': "Sí",
                'no': "No"
            },
            'fr': {
                'no_results': "Aucune réponse trouvée. Essayez de reformuler votre question.",
                'multiple_results': "{count} réponses pertinentes trouvées:",
                'confidence_high': "Correspondance de haute confiance",
                'confidence_medium': "Correspondance de confiance moyenne",
                'confidence_low': "Correspondance de faible confiance",
                'feedback_helpful': "Cela a-t-il été utile?",
                'yes': "Oui",
                'no': "Non"
            },
            'de': {
                'no_results': "Keine passenden Antworten gefunden. Versuchen Sie, Ihre Frage umzuformulieren.",
                'multiple_results': "{count} relevante Antworten gefunden:",
                'confidence_high': "Hohe Vertrauensübereinstimmung",
                'confidence_medium': "Mittlere Vertrauensübereinstimmung",
                'confidence_low': "Niedrige Vertrauensübereinstimmung",
                'feedback_helpful': "War das hilfreich?",
                'yes': "Ja",
                'no': "Nein"
            }
        }
        
        return templates.get(lang_code, templates['en'])
    
    def process_multilang_query(self, question: str, target_lang: str = None) -> Dict:
        """Process a multi-language query and return structured information"""
        detected_lang = self.detect_language(question)
        target_lang = target_lang or detected_lang
        
        # Extract intent and normalize
        intent_info = self.extract_question_intent(question, detected_lang)
        normalized_question = self.normalize_question(question, detected_lang)
        
        # Get response template
        response_template = self.get_multilang_response_template(target_lang)
        
        return {
            'original_question': question,
            'detected_language': detected_lang,
            'target_language': target_lang,
            'normalized_question': normalized_question,
            'intent_info': intent_info,
            'response_template': response_template,
            'suggestions': self.get_language_specific_suggestions(detected_lang)
        }