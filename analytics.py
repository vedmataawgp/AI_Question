from datetime import datetime, timedelta
from sqlalchemy import func, desc
from app import db
from models import Question, ContentItem, Category, Analytics
import logging

class AnalyticsManager:
    """Analytics manager for tracking and analyzing system usage"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def update_daily_analytics(self):
        """Update daily analytics record"""
        try:
            today = datetime.utcnow().date()
            
            # Get or create today's analytics record
            analytics = Analytics.query.filter_by(date=today).first()
            if not analytics:
                analytics = Analytics(date=today)
                db.session.add(analytics)
            
            # Calculate metrics for today
            today_questions = Question.query.filter(
                func.date(Question.asked_at) == today
            ).all()
            
            analytics.total_questions = len(today_questions)
            analytics.total_sessions = len(set(q.session_id for q in today_questions))
            
            # Calculate average confidence score
            if today_questions:
                avg_confidence = sum(q.confidence_score for q in today_questions) / len(today_questions)
                analytics.avg_confidence_score = avg_confidence
            
            # Find most asked category
            if today_questions:
                category_counts = {}
                for question in today_questions:
                    if question.best_answer and question.best_answer.category:
                        cat_id = question.best_answer.category.id
                        category_counts[cat_id] = category_counts.get(cat_id, 0) + 1
                
                if category_counts:
                    most_asked_cat_id = max(category_counts, key=category_counts.get)
                    analytics.most_asked_category_id = most_asked_cat_id
            
            db.session.commit()
            self.logger.info(f"Updated analytics for {today}")
            
        except Exception as e:
            self.logger.error(f"Error updating daily analytics: {e}")
            db.session.rollback()
    
    def get_dashboard_stats(self):
        """Get dashboard statistics"""
        try:
            # Total counts
            total_questions = Question.query.count()
            total_categories = Category.query.count()
            total_content_items = ContentItem.query.count()
            
            # Recent activity (last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_questions = Question.query.filter(
                Question.asked_at >= thirty_days_ago
            ).count()
            
            # Average confidence score
            avg_confidence = db.session.query(func.avg(Question.confidence_score)).scalar() or 0
            
            # Most active categories (by question count)
            category_stats = db.session.query(
                Category.name,
                func.count(Question.id).label('question_count')
            ).join(ContentItem, Category.id == ContentItem.category_id)\
             .join(Question, ContentItem.id == Question.best_answer_id)\
             .group_by(Category.id, Category.name)\
             .order_by(desc('question_count'))\
             .limit(5).all()
            
            return {
                'total_questions': total_questions,
                'total_categories': total_categories,
                'total_content_items': total_content_items,
                'recent_questions': recent_questions,
                'avg_confidence_score': round(avg_confidence, 2),
                'top_categories': [{'name': name, 'count': count} for name, count in category_stats]
            }
            
        except Exception as e:
            self.logger.error(f"Error getting dashboard stats: {e}")
            return {
                'total_questions': 0,
                'total_categories': 0,
                'total_content_items': 0,
                'recent_questions': 0,
                'avg_confidence_score': 0,
                'top_categories': []
            }
    
    def get_question_trends(self, days=30):
        """Get question trends over time"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Daily question counts
            daily_counts = db.session.query(
                func.date(Question.asked_at).label('date'),
                func.count(Question.id).label('count')
            ).filter(Question.asked_at >= start_date)\
             .group_by(func.date(Question.asked_at))\
             .order_by('date').all()
            
            # Category distribution
            category_dist = db.session.query(
                Category.name,
                func.count(Question.id).label('count')
            ).join(ContentItem, Category.id == ContentItem.category_id)\
             .join(Question, ContentItem.id == Question.best_answer_id)\
             .filter(Question.asked_at >= start_date)\
             .group_by(Category.id, Category.name)\
             .order_by(desc('count')).all()
            
            # Confidence score distribution
            confidence_ranges = [
                (0.0, 0.2, 'Very Low'),
                (0.2, 0.4, 'Low'),
                (0.4, 0.6, 'Medium'),
                (0.6, 0.8, 'High'),
                (0.8, 1.0, 'Very High')
            ]
            
            confidence_dist = []
            for min_score, max_score, label in confidence_ranges:
                count = Question.query.filter(
                    Question.asked_at >= start_date,
                    Question.confidence_score >= min_score,
                    Question.confidence_score < max_score
                ).count()
                confidence_dist.append({'label': label, 'count': count})
            
            return {
                'daily_counts': [{'date': str(date), 'count': count} for date, count in daily_counts],
                'category_distribution': [{'name': name, 'count': count} for name, count in category_dist],
                'confidence_distribution': confidence_dist
            }
            
        except Exception as e:
            self.logger.error(f"Error getting question trends: {e}")
            return {
                'daily_counts': [],
                'category_distribution': [],
                'confidence_distribution': []
            }
    
    def get_recent_questions(self, limit=50):
        """Get recent questions with details"""
        try:
            questions = Question.query.order_by(desc(Question.asked_at))\
                                     .limit(limit).all()
            
            result = []
            for q in questions:
                result.append({
                    'id': q.id,
                    'question': q.question_text,
                    'asked_at': q.asked_at.isoformat(),
                    'confidence_score': q.confidence_score,
                    'category': q.best_answer.category.name if q.best_answer else 'No match',
                    'was_helpful': q.was_helpful
                })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting recent questions: {e}")
            return []
