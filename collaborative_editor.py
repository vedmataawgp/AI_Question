"""
Real-time Collaborative Content Editing System
Enables multiple users to edit content simultaneously with conflict resolution
"""

import logging
import json
import time
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from flask_socketio import SocketIO, emit, join_room, leave_room
import uuid

class CollaborativeEditor:
    """Real-time collaborative editing system"""
    
    def __init__(self, socketio: SocketIO):
        self.logger = logging.getLogger(__name__)
        self.socketio = socketio
        
        # Active editing sessions
        self.active_sessions = {}  # content_id -> session_data
        self.user_sessions = {}    # user_id -> content_id
        self.edit_history = {}     # content_id -> list of edits
        
        # Setup SocketIO event handlers
        self._setup_socketio_handlers()
    
    def _setup_socketio_handlers(self):
        """Setup SocketIO event handlers for collaborative editing"""
        
        @self.socketio.on('join_edit_session')
        def handle_join_session(data):
            """User joins an editing session"""
            content_id = data.get('content_id')
            user_id = data.get('user_id', str(uuid.uuid4()))
            user_name = data.get('user_name', f'User_{user_id[:8]}')
            
            if not content_id:
                emit('error', {'message': 'Content ID required'})
                return
            
            # Join the room for this content
            join_room(f'content_{content_id}')
            
            # Initialize session if not exists
            if content_id not in self.active_sessions:
                self.active_sessions[content_id] = {
                    'users': {},
                    'current_content': '',
                    'version': 0,
                    'locked_sections': {},
                    'created_at': datetime.now()
                }
            
            # Add user to session
            self.active_sessions[content_id]['users'][user_id] = {
                'name': user_name,
                'joined_at': datetime.now(),
                'cursor_position': 0,
                'selection': {'start': 0, 'end': 0},
                'is_active': True
            }
            
            self.user_sessions[user_id] = content_id
            
            # Notify other users
            emit('user_joined', {
                'user_id': user_id,
                'user_name': user_name,
                'active_users': list(self.active_sessions[content_id]['users'].keys())
            }, room=f'content_{content_id}')
            
            # Send current state to the new user
            emit('session_state', {
                'content': self.active_sessions[content_id]['current_content'],
                'version': self.active_sessions[content_id]['version'],
                'active_users': {
                    uid: {'name': udata['name'], 'cursor_position': udata['cursor_position']}
                    for uid, udata in self.active_sessions[content_id]['users'].items()
                }
            })
            
            self.logger.info(f"User {user_name} joined editing session for content {content_id}")
        
        @self.socketio.on('leave_edit_session')
        def handle_leave_session(data):
            """User leaves an editing session"""
            user_id = data.get('user_id')
            
            if user_id in self.user_sessions:
                content_id = self.user_sessions[user_id]
                
                # Remove user from session
                if (content_id in self.active_sessions and 
                    user_id in self.active_sessions[content_id]['users']):
                    
                    user_name = self.active_sessions[content_id]['users'][user_id]['name']
                    del self.active_sessions[content_id]['users'][user_id]
                    
                    # Notify other users
                    emit('user_left', {
                        'user_id': user_id,
                        'user_name': user_name,
                        'active_users': list(self.active_sessions[content_id]['users'].keys())
                    }, room=f'content_{content_id}')
                    
                    # Clean up empty sessions
                    if not self.active_sessions[content_id]['users']:
                        del self.active_sessions[content_id]
                
                del self.user_sessions[user_id]
                leave_room(f'content_{content_id}')
        
        @self.socketio.on('content_edit')
        def handle_content_edit(data):
            """Handle real-time content edits"""
            user_id = data.get('user_id')
            content_id = data.get('content_id')
            edit_data = data.get('edit')
            
            if not all([user_id, content_id, edit_data]):
                emit('error', {'message': 'Missing required data'})
                return
            
            if content_id not in self.active_sessions:
                emit('error', {'message': 'Session not found'})
                return
            
            session = self.active_sessions[content_id]
            
            # Apply operational transformation
            transformed_edit = self._apply_operational_transform(
                edit_data, session['version'], content_id
            )
            
            if transformed_edit:
                # Update content
                session['current_content'] = self._apply_edit(
                    session['current_content'], transformed_edit
                )
                session['version'] += 1
                
                # Record edit in history
                if content_id not in self.edit_history:
                    self.edit_history[content_id] = []
                
                self.edit_history[content_id].append({
                    'user_id': user_id,
                    'edit': transformed_edit,
                    'timestamp': datetime.now(),
                    'version': session['version']
                })
                
                # Broadcast edit to other users
                emit('content_updated', {
                    'edit': transformed_edit,
                    'version': session['version'],
                    'user_id': user_id,
                    'content': session['current_content']
                }, room=f'content_{content_id}', include_self=False)
        
        @self.socketio.on('cursor_update')
        def handle_cursor_update(data):
            """Handle cursor position updates"""
            user_id = data.get('user_id')
            content_id = data.get('content_id')
            cursor_position = data.get('cursor_position', 0)
            selection = data.get('selection', {'start': 0, 'end': 0})
            
            if (content_id in self.active_sessions and 
                user_id in self.active_sessions[content_id]['users']):
                
                # Update user cursor info
                self.active_sessions[content_id]['users'][user_id]['cursor_position'] = cursor_position
                self.active_sessions[content_id]['users'][user_id]['selection'] = selection
                
                # Broadcast to other users
                emit('cursor_moved', {
                    'user_id': user_id,
                    'cursor_position': cursor_position,
                    'selection': selection
                }, room=f'content_{content_id}', include_self=False)
        
        @self.socketio.on('lock_section')
        def handle_lock_section(data):
            """Handle section locking for exclusive editing"""
            user_id = data.get('user_id')
            content_id = data.get('content_id')
            section_start = data.get('start')
            section_end = data.get('end')
            
            if content_id in self.active_sessions:
                session = self.active_sessions[content_id]
                
                # Check if section is already locked
                for lock_id, lock_data in session['locked_sections'].items():
                    if (lock_data['start'] <= section_start <= lock_data['end'] or
                        lock_data['start'] <= section_end <= lock_data['end']):
                        emit('lock_failed', {
                            'message': 'Section already locked',
                            'locked_by': lock_data['user_id']
                        })
                        return
                
                # Create lock
                lock_id = str(uuid.uuid4())
                session['locked_sections'][lock_id] = {
                    'user_id': user_id,
                    'start': section_start,
                    'end': section_end,
                    'created_at': datetime.now()
                }
                
                # Notify all users
                emit('section_locked', {
                    'lock_id': lock_id,
                    'user_id': user_id,
                    'start': section_start,
                    'end': section_end
                }, room=f'content_{content_id}')
        
        @self.socketio.on('unlock_section')
        def handle_unlock_section(data):
            """Handle section unlocking"""
            user_id = data.get('user_id')
            content_id = data.get('content_id')
            lock_id = data.get('lock_id')
            
            if (content_id in self.active_sessions and 
                lock_id in self.active_sessions[content_id]['locked_sections']):
                
                lock_data = self.active_sessions[content_id]['locked_sections'][lock_id]
                
                # Only the lock owner can unlock
                if lock_data['user_id'] == user_id:
                    del self.active_sessions[content_id]['locked_sections'][lock_id]
                    
                    # Notify all users
                    emit('section_unlocked', {
                        'lock_id': lock_id,
                        'user_id': user_id
                    }, room=f'content_{content_id}')
    
    def _apply_operational_transform(self, edit: Dict, current_version: int, content_id: str) -> Optional[Dict]:
        """Apply operational transformation to resolve conflicts"""
        if content_id not in self.edit_history:
            return edit
        
        # Get edits since the edit was created
        concurrent_edits = [
            h for h in self.edit_history[content_id]
            if h['version'] > edit.get('base_version', current_version)
        ]
        
        transformed_edit = edit.copy()
        
        for concurrent_edit in concurrent_edits:
            transformed_edit = self._transform_edit_against_edit(
                transformed_edit, concurrent_edit['edit']
            )
        
        return transformed_edit
    
    def _transform_edit_against_edit(self, edit1: Dict, edit2: Dict) -> Dict:
        """Transform one edit against another using operational transformation"""
        # Simple operational transformation for text edits
        if edit1['type'] == 'insert' and edit2['type'] == 'insert':
            if edit2['position'] <= edit1['position']:
                edit1['position'] += len(edit2['text'])
        
        elif edit1['type'] == 'delete' and edit2['type'] == 'insert':
            if edit2['position'] <= edit1['position']:
                edit1['position'] += len(edit2['text'])
        
        elif edit1['type'] == 'insert' and edit2['type'] == 'delete':
            if edit2['position'] <= edit1['position']:
                edit1['position'] -= edit2['length']
                if edit1['position'] < edit2['position']:
                    edit1['position'] = edit2['position']
        
        elif edit1['type'] == 'delete' and edit2['type'] == 'delete':
            if edit2['position'] <= edit1['position']:
                if edit2['position'] + edit2['length'] <= edit1['position']:
                    edit1['position'] -= edit2['length']
                else:
                    # Overlapping deletes - adjust accordingly
                    overlap = min(edit1['position'] + edit1['length'], 
                                edit2['position'] + edit2['length']) - max(edit1['position'], edit2['position'])
                    if overlap > 0:
                        edit1['length'] -= overlap
                        edit1['position'] = edit2['position']
        
        return edit1
    
    def _apply_edit(self, content: str, edit: Dict) -> str:
        """Apply an edit to content"""
        if edit['type'] == 'insert':
            position = edit['position']
            text = edit['text']
            return content[:position] + text + content[position:]
        
        elif edit['type'] == 'delete':
            position = edit['position']
            length = edit['length']
            return content[:position] + content[position + length:]
        
        elif edit['type'] == 'replace':
            position = edit['position']
            length = edit['length']
            text = edit['text']
            return content[:position] + text + content[position + length:]
        
        return content
    
    def get_session_info(self, content_id: str) -> Optional[Dict]:
        """Get information about an editing session"""
        if content_id not in self.active_sessions:
            return None
        
        session = self.active_sessions[content_id]
        return {
            'content_id': content_id,
            'active_users': len(session['users']),
            'version': session['version'],
            'created_at': session['created_at'].isoformat(),
            'users': {
                uid: {
                    'name': udata['name'],
                    'joined_at': udata['joined_at'].isoformat(),
                    'is_active': udata['is_active']
                }
                for uid, udata in session['users'].items()
            },
            'locked_sections': len(session['locked_sections'])
        }
    
    def save_content(self, content_id: str) -> Optional[str]:
        """Save the current content of an editing session"""
        if content_id not in self.active_sessions:
            return None
        
        return self.active_sessions[content_id]['current_content']
    
    def get_edit_history(self, content_id: str, limit: int = 50) -> List[Dict]:
        """Get edit history for content"""
        if content_id not in self.edit_history:
            return []
        
        history = self.edit_history[content_id]
        return [
            {
                'user_id': edit['user_id'],
                'edit_type': edit['edit']['type'],
                'timestamp': edit['timestamp'].isoformat(),
                'version': edit['version']
            }
            for edit in history[-limit:]
        ]
    
    def cleanup_expired_sessions(self, max_age_hours: int = 24):
        """Clean up old inactive sessions"""
        current_time = datetime.now()
        expired_sessions = []
        
        for content_id, session in self.active_sessions.items():
            session_age = current_time - session['created_at']
            if session_age.total_seconds() > max_age_hours * 3600:
                expired_sessions.append(content_id)
        
        for content_id in expired_sessions:
            del self.active_sessions[content_id]
            if content_id in self.edit_history:
                # Keep history but limit it
                self.edit_history[content_id] = self.edit_history[content_id][-100:]
        
        self.logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
    
    def get_active_sessions_count(self) -> int:
        """Get number of active editing sessions"""
        return len(self.active_sessions)
    
    def get_total_active_users(self) -> int:
        """Get total number of active users across all sessions"""
        total_users = 0
        for session in self.active_sessions.values():
            total_users += len(session['users'])
        return total_users