"""
External Knowledge Base Integration
Connects to external sources like Wikipedia and web APIs for enhanced answers
"""

import logging
import requests
from typing import Dict, List, Optional, Tuple
import json
import re
from urllib.parse import quote_plus
from datetime import datetime, timedelta

try:
    import wikipedia
    WIKIPEDIA_AVAILABLE = True
except ImportError:
    WIKIPEDIA_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

class ExternalKnowledgeConnector:
    """Connector for external knowledge sources"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.cache = {}
        self.cache_duration = timedelta(hours=24)  # Cache for 24 hours
        
        # Configure Wikipedia
        if WIKIPEDIA_AVAILABLE:
            wikipedia.set_lang("en")
            wikipedia.set_rate_limiting(True)
    
    def search_wikipedia(self, query: str, max_results: int = 3) -> List[Dict]:
        """Search Wikipedia for relevant articles"""
        if not WIKIPEDIA_AVAILABLE:
            self.logger.warning("Wikipedia not available")
            return []
        
        try:
            # Check cache first
            cache_key = f"wiki_{query}"
            if cache_key in self.cache:
                cached_time, cached_result = self.cache[cache_key]
                if datetime.now() - cached_time < self.cache_duration:
                    return cached_result
            
            # Search Wikipedia
            search_results = wikipedia.search(query, results=max_results)
            articles = []
            
            for title in search_results:
                try:
                    page = wikipedia.page(title)
                    summary = wikipedia.summary(title, sentences=3)
                    
                    articles.append({
                        'title': page.title,
                        'summary': summary,
                        'url': page.url,
                        'source': 'Wikipedia',
                        'content': summary,
                        'category': 'External Knowledge'
                    })
                except wikipedia.exceptions.DisambiguationError as e:
                    # Take the first option from disambiguation
                    try:
                        page = wikipedia.page(e.options[0])
                        summary = wikipedia.summary(e.options[0], sentences=3)
                        articles.append({
                            'title': page.title,
                            'summary': summary,
                            'url': page.url,
                            'source': 'Wikipedia',
                            'content': summary,
                            'category': 'External Knowledge'
                        })
                    except:
                        continue
                except wikipedia.exceptions.PageError:
                    continue
                except Exception as e:
                    self.logger.warning(f"Error fetching Wikipedia page {title}: {e}")
                    continue
            
            # Cache the results
            self.cache[cache_key] = (datetime.now(), articles)
            
            return articles
            
        except Exception as e:
            self.logger.error(f"Error searching Wikipedia: {e}")
            return []
    
    def search_web_content(self, query: str, max_results: int = 3) -> List[Dict]:
        """Search for web content using free APIs"""
        results = []
        
        # Try different search approaches
        try:
            # Search for educational content
            educational_sources = self._search_educational_apis(query)
            results.extend(educational_sources[:max_results])
            
        except Exception as e:
            self.logger.warning(f"Error searching web content: {e}")
        
        return results
    
    def _search_educational_apis(self, query: str) -> List[Dict]:
        """Search educational and documentation APIs"""
        results = []
        
        # Search Stack Overflow API (no key required for basic search)
        try:
            stackoverflow_results = self._search_stackoverflow(query)
            results.extend(stackoverflow_results)
        except Exception as e:
            self.logger.warning(f"Stack Overflow search error: {e}")
        
        # Search GitHub API for documentation
        try:
            github_results = self._search_github_docs(query)
            results.extend(github_results)
        except Exception as e:
            self.logger.warning(f"GitHub search error: {e}")
        
        return results
    
    def _search_stackoverflow(self, query: str) -> List[Dict]:
        """Search Stack Overflow for programming questions"""
        try:
            url = "https://api.stackexchange.com/2.3/search/advanced"
            params = {
                'order': 'desc',
                'sort': 'relevance',
                'q': query,
                'site': 'stackoverflow',
                'pagesize': 3,
                'filter': 'withbody'
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                results = []
                
                for item in data.get('items', []):
                    if item.get('is_answered', False):
                        # Extract text from HTML body
                        body_text = self._extract_text_from_html(item.get('body', ''))
                        
                        results.append({
                            'title': item.get('title', 'Stack Overflow Answer'),
                            'content': body_text[:500] + '...' if len(body_text) > 500 else body_text,
                            'url': item.get('link', ''),
                            'source': 'Stack Overflow',
                            'category': 'Programming',
                            'score': item.get('score', 0)
                        })
                
                return results
            
        except Exception as e:
            self.logger.warning(f"Stack Overflow API error: {e}")
        
        return []
    
    def _search_github_docs(self, query: str) -> List[Dict]:
        """Search GitHub for documentation"""
        try:
            url = "https://api.github.com/search/code"
            params = {
                'q': f'{query} extension:md',
                'sort': 'indexed',
                'order': 'desc',
                'per_page': 3
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                results = []
                
                for item in data.get('items', []):
                    if 'README' in item.get('name', '').upper() or 'doc' in item.get('path', '').lower():
                        results.append({
                            'title': f"Documentation: {item.get('name', 'README')}",
                            'content': f"Found in {item.get('repository', {}).get('full_name', 'repository')}: {item.get('path', '')}",
                            'url': item.get('html_url', ''),
                            'source': 'GitHub',
                            'category': 'Documentation',
                            'repository': item.get('repository', {}).get('full_name', '')
                        })
                
                return results
            
        except Exception as e:
            self.logger.warning(f"GitHub API error: {e}")
        
        return []
    
    def _extract_text_from_html(self, html_content: str) -> str:
        """Extract clean text from HTML"""
        if not BS4_AVAILABLE:
            # Basic HTML tag removal
            text = re.sub(r'<[^>]+>', '', html_content)
            text = re.sub(r'&[a-zA-Z0-9#]+;', ' ', text)
            return text.strip()
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text and clean it up
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text
        except Exception:
            # Fallback to regex
            text = re.sub(r'<[^>]+>', '', html_content)
            return text.strip()
    
    def enhance_answer_with_external_knowledge(self, question: str, existing_answers: List[Dict]) -> List[Dict]:
        """Enhance existing answers with external knowledge"""
        enhanced_answers = existing_answers.copy()
        
        # Search external sources
        external_sources = []
        
        # Wikipedia search
        wiki_results = self.search_wikipedia(question, max_results=2)
        external_sources.extend(wiki_results)
        
        # Web content search
        web_results = self.search_web_content(question, max_results=2)
        external_sources.extend(web_results)
        
        # Add external sources as additional answers
        for source in external_sources:
            # Mark as external source
            source['is_external'] = True
            source['confidence'] = 0.7  # Default confidence for external sources
            enhanced_answers.append(source)
        
        return enhanced_answers
    
    def get_related_topics(self, topic: str) -> List[str]:
        """Get related topics for better search suggestions"""
        if not WIKIPEDIA_AVAILABLE:
            return []
        
        try:
            # Get Wikipedia page and extract links
            page = wikipedia.page(topic)
            
            # Get categories and related pages
            related = []
            
            # Extract some links from the content
            links = page.links[:10]  # First 10 links
            for link in links:
                if len(link.split()) <= 3:  # Short, likely relevant topics
                    related.append(link)
            
            return related[:5]  # Return top 5
            
        except Exception as e:
            self.logger.warning(f"Error getting related topics: {e}")
            return []
    
    def validate_external_source(self, source: Dict) -> bool:
        """Validate that external source is reliable"""
        trusted_domains = [
            'wikipedia.org',
            'stackoverflow.com',
            'github.com',
            'docs.python.org',
            'developer.mozilla.org',
            'w3schools.com',
            'medium.com'
        ]
        
        url = source.get('url', '')
        for domain in trusted_domains:
            if domain in url:
                return True
        
        return False
    
    def format_external_answer(self, source: Dict, confidence: float = 0.7) -> Dict:
        """Format external source as an answer"""
        return {
            'title': source.get('title', 'External Source'),
            'content': source.get('content', source.get('summary', '')),
            'category': source.get('category', 'External Knowledge'),
            'source': source.get('source', 'External'),
            'url': source.get('url', ''),
            'confidence': confidence,
            'is_external': True
        }
    
    def clear_cache(self):
        """Clear the knowledge cache"""
        self.cache.clear()
        self.logger.info("External knowledge cache cleared")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        current_time = datetime.now()
        valid_entries = 0
        expired_entries = 0
        
        for cache_time, _ in self.cache.values():
            if current_time - cache_time < self.cache_duration:
                valid_entries += 1
            else:
                expired_entries += 1
        
        return {
            'total_entries': len(self.cache),
            'valid_entries': valid_entries,
            'expired_entries': expired_entries,
            'cache_duration_hours': self.cache_duration.total_seconds() / 3600
        }