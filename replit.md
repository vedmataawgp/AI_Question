# Advanced Q&A System - AI-Powered Question Answering Platform

## Overview

This is an advanced Flask-based Q&A system that uses state-of-the-art Natural Language Processing (NLP) to match user questions with relevant content from a knowledge base. The system features transformer-based semantic understanding, multi-language support, real-time collaborative editing, external knowledge integration, and comprehensive analytics.

## System Architecture

### Backend Framework
- **Flask**: Web framework with SocketIO for real-time features
- **SQLAlchemy**: ORM for database operations with SQLite as the default database
- **Flask-SocketIO**: Real-time WebSocket communication for collaborative editing
- **Session-based tracking**: User sessions managed via Flask sessions with UUID generation

### Advanced NLP Engine
- **Multiple NLP Processors**: Layered approach with fallback mechanisms
  - **Transformer NLP**: Advanced semantic understanding using sentence transformers
  - **spaCy**: Primary NLP library for text processing (with fallback model loading)
  - **scikit-learn**: TF-IDF vectorization and cosine similarity for question matching
- **Multi-language Support**: Automatic language detection and multi-language processing
- **External Knowledge Integration**: Wikipedia and web search integration for enhanced answers

### Frontend Architecture
- **Server-side rendered templates**: Jinja2 templating with Bootstrap 5 dark theme
- **Real-time JavaScript**: Advanced UI with language detection and collaborative features
- **Bootstrap 5**: CSS framework with Replit dark theme customization
- **Feather Icons**: Icon library for consistent visual elements
- **Chart.js**: Data visualization for analytics
- **SocketIO Client**: Real-time collaborative editing interface

## Key Components

### Models (models.py)
- **Category**: Organizes content into logical groups
- **ContentItem**: Stores the knowledge base content with preprocessed text
- **Question**: Tracks user questions with confidence scores and session data
- **Analytics**: Daily analytics aggregation (referenced but not fully implemented in provided code)

### NLP Processor (nlp_processor.py)
- Handles text preprocessing and question matching
- Uses TF-IDF vectorization with cosine similarity
- Implements fallback loading for different spaCy models (lg → md → sm → blank)
- Supports n-gram analysis (1-2 grams) for better semantic matching

### File Processor (file_processor.py)
- Supports bulk content import from multiple formats
- Handles TXT, CSV, DOCX, and DOC files
- Includes file validation and secure filename handling
- Uses pandas for CSV processing and python-docx for document parsing

### Analytics Manager (analytics.py)
- Tracks daily usage metrics including question counts and confidence scores
- Identifies most asked categories and session statistics
- Provides data for admin dashboard reporting

## Data Flow

1. **User Question Flow**:
   - User submits question via web form
   - Session ID assigned/retrieved for tracking
   - Question preprocessed through NLP pipeline
   - TF-IDF matching against content database
   - Results ranked by confidence score
   - Response displayed with feedback options

2. **Content Management Flow**:
   - Admin uploads content via web interface or bulk file upload
   - Content categorized and stored in database
   - Text preprocessed for optimized matching
   - Analytics updated for tracking

3. **Analytics Flow**:
   - Daily aggregation of question and session metrics
   - Confidence score analysis and category trending
   - Dashboard visualization of system performance

## External Dependencies

### Python Packages
- **Flask ecosystem**: flask, flask-sqlalchemy
- **NLP libraries**: spacy, scikit-learn, numpy
- **File processing**: pandas, python-docx, werkzeug
- **Optional**: win32com (for .doc files on Windows)

### Frontend Dependencies
- **Bootstrap 5**: CSS framework and components
- **Feather Icons**: SVG icon library
- **Chart.js**: Data visualization for analytics

### spaCy Models
- Preferred: en_core_web_lg (large English model)
- Fallbacks: en_core_web_md, en_core_web_sm, blank model

## Deployment Strategy

### Database Configuration
- **Development**: SQLite with file-based storage
- **Production**: Configurable via DATABASE_URL environment variable
- **Connection pooling**: Enabled with 300-second recycle and pre-ping

### File Handling
- **Upload directory**: Configurable uploads folder
- **File size limit**: 16MB maximum
- **Security**: Secure filename validation and type checking

### Environment Configuration
- **Session secret**: Configurable via SESSION_SECRET environment variable
- **Debug mode**: Enabled for development, should be disabled in production
- **Proxy support**: ProxyFix middleware for deployment behind reverse proxies

## Changelog
- June 30, 2025. Initial setup

## User Preferences

Preferred communication style: Simple, everyday language.