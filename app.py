import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_socketio import SocketIO

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///qa_system.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Configure upload settings
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize SocketIO for real-time collaboration
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Initialize the app with the extension
db.init_app(app)

# Create upload directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

with app.app_context():
    # Import models and routes
    import models
    import routes
    
    # Create all tables
    db.create_all()
    
    # Initialize advanced processors
    from nlp_processor import NLPProcessor
    from transformer_nlp import TransformerNLP
    from multilang_support import MultiLanguageProcessor
    from external_knowledge import ExternalKnowledgeConnector
    from collaborative_editor import CollaborativeEditor
    from hindi_content_extractor import HindiContentExtractor
    
    # Initialize processors with fallback handling
    try:
        app.transformer_nlp = TransformerNLP()
        logging.info("Advanced transformer NLP initialized")
    except Exception as e:
        logging.warning(f"Transformer NLP initialization failed: {e}")
        app.transformer_nlp = None
    
    app.nlp_processor = NLPProcessor()
    app.multilang_processor = MultiLanguageProcessor()
    app.external_knowledge = ExternalKnowledgeConnector()
    app.collaborative_editor = CollaborativeEditor(socketio)
    app.hindi_extractor = HindiContentExtractor()
    
    logging.info("Advanced Q&A system initialized with all features")
