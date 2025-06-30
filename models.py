from datetime import datetime
from app import db
from sqlalchemy import func

class Category(db.Model):
    """Category model for organizing content"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to content items
    content_items = db.relationship('ContentItem', backref='category', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Category {self.name}>'

class ContentItem(db.Model):
    """Content item model for storing text content"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Processed content for NLP
    processed_content = db.Column(db.Text)  # Preprocessed text for faster matching
    
    def __repr__(self):
        return f'<ContentItem {self.title}>'

class Question(db.Model):
    """Question model for tracking user questions"""
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.Text, nullable=False)
    session_id = db.Column(db.String(100), nullable=False)  # Session-based tracking
    asked_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Best matching answer
    best_answer_id = db.Column(db.Integer, db.ForeignKey('content_item.id'), nullable=True)
    best_answer = db.relationship('ContentItem', backref='matched_questions')
    
    # Confidence score of the match
    confidence_score = db.Column(db.Float, default=0.0)
    
    # User feedback (optional)
    was_helpful = db.Column(db.Boolean, nullable=True)
    
    def __repr__(self):
        return f'<Question {self.question_text[:50]}...>'

class Analytics(db.Model):
    """Analytics model for tracking system usage"""
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, default=datetime.utcnow().date())
    total_questions = db.Column(db.Integer, default=0)
    total_sessions = db.Column(db.Integer, default=0)
    avg_confidence_score = db.Column(db.Float, default=0.0)
    most_asked_category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    most_asked_category = db.relationship('Category', backref='analytics_records')
    
    # Unique constraint to ensure one record per day
    __table_args__ = (db.UniqueConstraint('date', name='unique_date'),)
    
    def __repr__(self):
        return f'<Analytics {self.date}>'

class FileUpload(db.Model):
    """File upload tracking model"""
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(10), nullable=False)  # CSV, TXT, DOCX, DOC
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed = db.Column(db.Boolean, default=False)
    items_created = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text)
    
    def __repr__(self):
        return f'<FileUpload {self.original_filename}>'
