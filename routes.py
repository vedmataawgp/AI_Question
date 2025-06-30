from flask import render_template, request, redirect, url_for, flash, session, jsonify
from flask_socketio import emit
from app import app, db, socketio
from models import Category, ContentItem, Question, FileUpload
from nlp_processor import NLPProcessor
from file_processor import FileProcessor
from analytics import AnalyticsManager
import os
import logging
from datetime import datetime
import uuid

# Initialize processors
nlp_processor = NLPProcessor()
file_processor = FileProcessor()
analytics_manager = AnalyticsManager()

@app.route('/')
def index():
    """Main user interface"""
    return render_template('user/index.html')

@app.route('/ask', methods=['GET', 'POST'])
def ask_question():
    """Handle user questions with advanced features"""
    if request.method == 'POST':
        question_text = request.form.get('question', '').strip()
        target_language = request.form.get('language', 'en')
        
        if not question_text:
            flash('Please enter a question.', 'error')
            return redirect(url_for('ask_question'))
        
        # Get or create session ID
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())
        
        try:
            # Multi-language processing
            multilang_info = app.multilang_processor.process_multilang_query(
                question_text, target_language
            )
            
            # Detect language and get response template
            detected_lang = multilang_info['detected_language']
            response_template = multilang_info['response_template']
            normalized_question = multilang_info['normalized_question']
            
            # Get all content items for processing
            content_items = ContentItem.query.all()
            
            if not content_items:
                flash(response_template['no_results'], 'warning')
                return render_template('user/question.html', 
                                     question=question_text, 
                                     answers=[],
                                     language_info=multilang_info)
            
            # Prepare content for NLP processing
            content_data = []
            for item in content_items:
                content_data.append({
                    'id': item.id,
                    'title': item.title,
                    'content': item.content,
                    'category': item.category.name,
                    'category_id': item.category.id
                })
            
            # Check if question is in Hindi and use specialized extraction
            detected_lang = app.multilang_processor.detect_language(question_text)
            use_hindi_extractor = detected_lang in ['hi', 'hindi'] or any(
                char in question_text for char in 'कखगघचछजझटठडढतथदधनपफबभमयरलवशषसहा'
            )
            
            matches = []
            
            if use_hindi_extractor and hasattr(app, 'hindi_extractor'):
                # Use Hindi content extractor for paragraph-level extraction
                for content_item in content_data:
                    relevant_paragraphs = app.hindi_extractor.extract_relevant_paragraphs(
                        question_text, content_item['content'], max_paragraphs=3
                    )
                    
                    if relevant_paragraphs:
                        # Format the extracted paragraphs into a comprehensive answer
                        formatted_answer = app.hindi_extractor.format_answer_with_paragraphs(
                            relevant_paragraphs, question_text
                        )
                        
                        # Create modified content item with extracted relevant content
                        modified_item = content_item.copy()
                        modified_item['content'] = formatted_answer['answer']
                        modified_item['original_content'] = content_item['content']
                        modified_item['extracted_paragraphs'] = len(relevant_paragraphs)
                        modified_item['total_words'] = formatted_answer['total_words']
                        
                        matches.append((modified_item, formatted_answer['confidence']))
                
                # Sort by confidence
                matches.sort(key=lambda x: x[1], reverse=True)
                matches = matches[:5]  # Take top 5
            
            # Use advanced transformer NLP if Hindi extractor didn't find enough or as fallback
            if len(matches) < 2:
                if hasattr(app, 'transformer_nlp') and app.transformer_nlp:
                    try:
                        transformer_matches = app.transformer_nlp.rank_answers(normalized_question, content_data)
                        # Avoid duplicates if we already have Hindi extracted content
                        for match in transformer_matches:
                            if not any(existing[0]['id'] == match[0]['id'] for existing in matches):
                                matches.append(match)
                    except Exception as e:
                        logging.warning(f"Transformer NLP failed, falling back: {e}")
                        nlp_processor.build_content_index(content_data)
                        traditional_matches = nlp_processor.find_best_answers(normalized_question, top_k=5)
                        for match in traditional_matches:
                            if not any(existing[0]['id'] == match[0]['id'] for existing in matches):
                                matches.append(match)
                else:
                    # Fallback to basic NLP
                    nlp_processor.build_content_index(content_data)
                    traditional_matches = nlp_processor.find_best_answers(normalized_question, top_k=5)
                    for match in traditional_matches:
                        if not any(existing[0]['id'] == match[0]['id'] for existing in matches):
                            matches.append(match)
            
            # Enhance with external knowledge
            if hasattr(app, 'external_knowledge'):
                try:
                    enhanced_matches = app.external_knowledge.enhance_answer_with_external_knowledge(
                        normalized_question, [match[0] for match in matches[:3]]
                    )
                    
                    # Convert enhanced matches back to (item, score) format
                    enhanced_scored = []
                    for item in enhanced_matches:
                        if item.get('is_external', False):
                            enhanced_scored.append((item, item.get('confidence', 0.7)))
                        else:
                            # Find original score
                            for match, score in matches:
                                if match.get('id') == item.get('id'):
                                    enhanced_scored.append((match, score))
                                    break
                    
                    matches = enhanced_scored
                except Exception as e:
                    logging.warning(f"External knowledge enhancement failed: {e}")
            
            # Save question to database
            best_answer_id = None
            confidence_score = 0.0
            
            if matches:
                best_match = matches[0]
                best_answer_id = best_match[0].get('id')
                confidence_score = best_match[1]
            
            question = Question(
                question_text=question_text,
                session_id=session['session_id'],
                best_answer_id=best_answer_id,
                confidence_score=confidence_score
            )
            
            db.session.add(question)
            db.session.commit()
            
            # Update analytics
            analytics_manager.update_daily_analytics()
            
            # Prepare answers for display
            answers = []
            for match, score in matches:
                if score > 0.1:  # Only show answers with reasonable confidence
                    answer_data = {
                        'title': match['title'],
                        'content': match['content'],
                        'category': match['category'],
                        'confidence': round(score * 100, 1),
                        'is_external': match.get('is_external', False),
                        'source': match.get('source', 'Internal'),
                        'url': match.get('url', '')
                    }
                    
                    # Get detailed confidence metrics if transformer NLP is available
                    if hasattr(app, 'transformer_nlp') and app.transformer_nlp:
                        try:
                            confidence_details = app.transformer_nlp.get_answer_confidence(
                                normalized_question, match, score
                            )
                            answer_data['confidence_details'] = confidence_details
                        except:
                            pass
                    
                    answers.append(answer_data)
            
            return render_template('user/question.html', 
                                 question=question_text, 
                                 answers=answers,
                                 question_id=question.id,
                                 language_info=multilang_info,
                                 response_template=response_template)
            
        except Exception as e:
            logging.error(f"Error processing question: {e}")
            flash('An error occurred while processing your question. Please try again.', 'error')
            return render_template('user/question.html', question=question_text, answers=[])
    
    # GET request - show form with language support
    supported_languages = []
    if hasattr(app, 'multilang_processor'):
        supported_languages = app.multilang_processor.get_supported_languages()
    
    return render_template('user/question.html', supported_languages=supported_languages)

@app.route('/feedback', methods=['POST'])
def feedback():
    """Handle user feedback on answers"""
    question_id = request.form.get('question_id')
    was_helpful = request.form.get('helpful') == 'yes'
    
    if question_id:
        question = Question.query.get(question_id)
        if question:
            question.was_helpful = was_helpful
            db.session.commit()
            flash('Thank you for your feedback!', 'success')
    
    return redirect(url_for('index'))

# Admin Routes
@app.route('/admin')
def admin_dashboard():
    """Admin dashboard"""
    stats = analytics_manager.get_dashboard_stats()
    return render_template('admin/dashboard.html', stats=stats)

@app.route('/admin/categories')
def admin_categories():
    """Manage categories"""
    categories = Category.query.all()
    return render_template('admin/categories.html', categories=categories)

@app.route('/admin/categories/add', methods=['POST'])
def add_category():
    """Add new category"""
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    
    if not name:
        flash('Category name is required.', 'error')
        return redirect(url_for('admin_categories'))
    
    # Check if category already exists
    existing = Category.query.filter_by(name=name).first()
    if existing:
        flash('Category already exists.', 'error')
        return redirect(url_for('admin_categories'))
    
    category = Category(name=name, description=description)
    db.session.add(category)
    db.session.commit()
    
    flash('Category added successfully.', 'success')
    return redirect(url_for('admin_categories'))

@app.route('/admin/categories/edit/<int:category_id>', methods=['POST'])
def edit_category(category_id):
    """Edit category"""
    category = Category.query.get_or_404(category_id)
    
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    
    if not name:
        flash('Category name is required.', 'error')
        return redirect(url_for('admin_categories'))
    
    # Check if name conflicts with another category
    existing = Category.query.filter(Category.name == name, Category.id != category_id).first()
    if existing:
        flash('Category name already exists.', 'error')
        return redirect(url_for('admin_categories'))
    
    category.name = name
    category.description = description
    db.session.commit()
    
    flash('Category updated successfully.', 'success')
    return redirect(url_for('admin_categories'))

@app.route('/admin/categories/delete/<int:category_id>', methods=['POST'])
def delete_category(category_id):
    """Delete category"""
    category = Category.query.get_or_404(category_id)
    
    # Check if category has content items
    if category.content_items:
        flash('Cannot delete category with content items. Please move or delete content first.', 'error')
        return redirect(url_for('admin_categories'))
    
    db.session.delete(category)
    db.session.commit()
    
    flash('Category deleted successfully.', 'success')
    return redirect(url_for('admin_categories'))

@app.route('/admin/content')
def admin_content():
    """Manage content"""
    page = request.args.get('page', 1, type=int)
    category_id = request.args.get('category', type=int)
    
    query = ContentItem.query
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    content_items = query.order_by(ContentItem.created_at.desc())\
                         .paginate(page=page, per_page=20, error_out=False)
    
    categories = Category.query.all()
    
    return render_template('admin/content.html', 
                         content_items=content_items, 
                         categories=categories,
                         selected_category=category_id)

@app.route('/admin/content/add', methods=['POST'])
def add_content():
    """Add new content item"""
    title = request.form.get('title', '').strip()
    content = request.form.get('content', '').strip()
    category_id = request.form.get('category_id', type=int)
    
    if not all([title, content, category_id]):
        flash('All fields are required.', 'error')
        return redirect(url_for('admin_content'))
    
    # Verify category exists
    category = Category.query.get(category_id)
    if not category:
        flash('Selected category does not exist.', 'error')
        return redirect(url_for('admin_content'))
    
    # Preprocess content for NLP
    processed_content = nlp_processor.preprocess_text(f"{title} {content}")
    
    content_item = ContentItem(
        title=title,
        content=content,
        category_id=category_id,
        processed_content=processed_content
    )
    
    db.session.add(content_item)
    db.session.commit()
    
    flash('Content added successfully.', 'success')
    return redirect(url_for('admin_content'))

@app.route('/admin/content/edit/<int:content_id>', methods=['POST'])
def edit_content(content_id):
    """Edit content item"""
    content_item = ContentItem.query.get_or_404(content_id)
    
    title = request.form.get('title', '').strip()
    content = request.form.get('content', '').strip()
    category_id = request.form.get('category_id', type=int)
    
    if not all([title, content, category_id]):
        flash('All fields are required.', 'error')
        return redirect(url_for('admin_content'))
    
    # Verify category exists
    category = Category.query.get(category_id)
    if not category:
        flash('Selected category does not exist.', 'error')
        return redirect(url_for('admin_content'))
    
    # Update content
    content_item.title = title
    content_item.content = content
    content_item.category_id = category_id
    content_item.processed_content = nlp_processor.preprocess_text(f"{title} {content}")
    content_item.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    flash('Content updated successfully.', 'success')
    return redirect(url_for('admin_content'))

@app.route('/admin/content/delete/<int:content_id>', methods=['POST'])
def delete_content(content_id):
    """Delete content item"""
    content_item = ContentItem.query.get_or_404(content_id)
    
    db.session.delete(content_item)
    db.session.commit()
    
    flash('Content deleted successfully.', 'success')
    return redirect(url_for('admin_content'))

@app.route('/admin/upload', methods=['POST'])
def upload_file():
    """Handle file upload for bulk content import"""
    if 'file' not in request.files:
        flash('No file selected.', 'error')
        return redirect(url_for('admin_content'))
    
    file = request.files['file']
    category_id = request.form.get('category_id', type=int)
    
    if file.filename == '':
        flash('No file selected.', 'error')
        return redirect(url_for('admin_content'))
    
    if not category_id:
        flash('Please select a category.', 'error')
        return redirect(url_for('admin_content'))
    
    # Verify category exists
    category = Category.query.get(category_id)
    if not category:
        flash('Selected category does not exist.', 'error')
        return redirect(url_for('admin_content'))
    
    if file and file_processor.is_allowed_file(file.filename):
        try:
            # Save file
            filename, file_path = file_processor.save_uploaded_file(file, app.config['UPLOAD_FOLDER'])
            
            if not filename:
                flash('Error saving file.', 'error')
                return redirect(url_for('admin_content'))
            
            file_type = file_processor.get_file_type(filename)
            
            # Create file upload record
            file_upload = FileUpload(
                filename=filename,
                original_filename=file.filename,
                file_type=file_type,
                category_id=category_id
            )
            db.session.add(file_upload)
            db.session.commit()
            
            # Process file
            items, error_message = file_processor.process_file(file_path, file_type)
            
            if error_message:
                file_upload.error_message = error_message
                db.session.commit()
                flash(f'Error processing file: {error_message}', 'error')
                return redirect(url_for('admin_content'))
            
            # Create content items
            items_created = 0
            for item_data in items:
                if item_data.get('title') and item_data.get('content'):
                    processed_content = nlp_processor.preprocess_text(
                        f"{item_data['title']} {item_data['content']}"
                    )
                    
                    content_item = ContentItem(
                        title=item_data['title'][:200],  # Limit title length
                        content=item_data['content'],
                        category_id=category_id,
                        processed_content=processed_content
                    )
                    
                    db.session.add(content_item)
                    items_created += 1
            
            # Update file upload record
            file_upload.processed = True
            file_upload.items_created = items_created
            db.session.commit()
            
            # Clean up uploaded file
            try:
                os.remove(file_path)
            except:
                pass
            
            flash(f'File processed successfully. Created {items_created} content items.', 'success')
            
        except Exception as e:
            logging.error(f"Error processing uploaded file: {e}")
            flash('An error occurred while processing the file.', 'error')
    
    else:
        flash('Invalid file type. Allowed types: TXT, CSV, DOCX, DOC', 'error')
    
    return redirect(url_for('admin_content'))

@app.route('/admin/analytics')
def admin_analytics():
    """Analytics dashboard"""
    trends = analytics_manager.get_question_trends(days=30)
    recent_questions = analytics_manager.get_recent_questions(limit=20)
    
    return render_template('admin/analytics.html', 
                         trends=trends, 
                         recent_questions=recent_questions)

@app.route('/api/analytics/trends')
def api_analytics_trends():
    """API endpoint for analytics trends"""
    days = request.args.get('days', 30, type=int)
    trends = analytics_manager.get_question_trends(days=days)
    return jsonify(trends)

# Advanced Feature Routes

@app.route('/api/languages')
def api_supported_languages():
    """API endpoint for supported languages"""
    if hasattr(app, 'multilang_processor'):
        languages = app.multilang_processor.get_supported_languages()
        return jsonify(languages)
    return jsonify([])

@app.route('/api/language/detect', methods=['POST'])
def api_detect_language():
    """API endpoint for language detection"""
    data = request.get_json()
    text = data.get('text', '')
    
    if hasattr(app, 'multilang_processor') and text:
        detected = app.multilang_processor.detect_language(text)
        return jsonify({'detected_language': detected})
    
    return jsonify({'detected_language': 'en'})

@app.route('/api/suggestions/<lang_code>')
def api_language_suggestions(lang_code):
    """API endpoint for language-specific suggestions"""
    if hasattr(app, 'multilang_processor'):
        suggestions = app.multilang_processor.get_language_specific_suggestions(lang_code)
        return jsonify(suggestions)
    return jsonify([])

@app.route('/api/external/search')
def api_external_search():
    """API endpoint for external knowledge search"""
    query = request.args.get('q', '')
    source = request.args.get('source', 'all')
    
    if not query:
        return jsonify({'results': []})
    
    results = []
    if hasattr(app, 'external_knowledge'):
        try:
            if source in ['all', 'wikipedia']:
                wiki_results = app.external_knowledge.search_wikipedia(query, max_results=3)
                results.extend(wiki_results)
            
            if source in ['all', 'web']:
                web_results = app.external_knowledge.search_web_content(query, max_results=3)
                results.extend(web_results)
        except Exception as e:
            logging.error(f"External search error: {e}")
    
    return jsonify({'results': results})

@app.route('/admin/collaborative')
def admin_collaborative():
    """Collaborative editing management"""
    if hasattr(app, 'collaborative_editor'):
        active_sessions = app.collaborative_editor.get_active_sessions_count()
        total_users = app.collaborative_editor.get_total_active_users()
        
        return render_template('admin/collaborative.html', 
                             active_sessions=active_sessions,
                             total_users=total_users)
    
    return render_template('admin/collaborative.html', 
                         active_sessions=0, 
                         total_users=0)

@app.route('/admin/content/edit/<int:content_id>/collaborative')
def collaborative_edit_content(content_id):
    """Start collaborative editing session for content"""
    content_item = ContentItem.query.get_or_404(content_id)
    
    return render_template('admin/collaborative_edit.html', 
                         content_item=content_item)

@app.route('/api/collaborative/session/<int:content_id>')
def api_collaborative_session_info(content_id):
    """API endpoint for collaborative session info"""
    if hasattr(app, 'collaborative_editor'):
        session_info = app.collaborative_editor.get_session_info(str(content_id))
        if session_info:
            return jsonify(session_info)
    
    return jsonify({'error': 'Session not found'}), 404

@app.route('/api/collaborative/save/<int:content_id>', methods=['POST'])
def api_collaborative_save(content_id):
    """API endpoint to save collaborative content"""
    if hasattr(app, 'collaborative_editor'):
        content = app.collaborative_editor.save_content(str(content_id))
        if content is not None:
            # Update the database
            content_item = ContentItem.query.get(content_id)
            if content_item:
                content_item.content = content
                content_item.updated_at = datetime.utcnow()
                db.session.commit()
                
                return jsonify({'success': True, 'message': 'Content saved successfully'})
    
    return jsonify({'error': 'Failed to save content'}), 400

@app.route('/api/transformer/analyze', methods=['POST'])
def api_transformer_analyze():
    """API endpoint for advanced transformer analysis"""
    data = request.get_json()
    text = data.get('text', '')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    result = {'analysis': {}}
    
    if hasattr(app, 'transformer_nlp') and app.transformer_nlp:
        try:
            # Extract entities
            entities = app.transformer_nlp.extract_entities(text)
            result['analysis']['entities'] = entities
            
            # Generate query expansions
            expansions = app.transformer_nlp.generate_query_expansion(text)
            result['analysis']['query_expansions'] = expansions
            
            # Get embeddings info (without actual vectors for API response)
            embeddings = app.transformer_nlp.get_embeddings(text)
            result['analysis']['has_embeddings'] = embeddings is not None
            if embeddings is not None:
                result['analysis']['embedding_dimension'] = len(embeddings)
        
        except Exception as e:
            logging.error(f"Transformer analysis error: {e}")
            result['error'] = str(e)
    else:
        result['analysis']['note'] = 'Advanced transformer features not available'
    
    return jsonify(result)

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500
