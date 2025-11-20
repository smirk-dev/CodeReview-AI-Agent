"""Session management for code review sessions.

This module provides session management capabilities for tracking
review sessions, maintaining state, and enabling session resumption.
"""

import uuid
from datetime import datetime
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages review sessions with state persistence.
    
    This class wraps the ADK InMemorySessionService to provide:
    - Session creation and retrieval
    - State management across agent interactions
    - Session history tracking
    - Session metadata management
    """
    
    def __init__(self, session_service):
        """Initialize the session manager.
        
        Args:
            session_service: ADK InMemorySessionService instance
        """
        self.session_service = session_service
        self.sessions: Dict[str, Dict] = {}
        logger.info("SessionManager initialized")
    
    def create_session(self) -> Dict:
        """Create a new review session.
        
        Returns:
            Dictionary containing session information
        """
        session_id = str(uuid.uuid4())
        session = {
            'id': session_id,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'status': 'active',
            'review_count': 0,
            'history': []
        }
        
        self.sessions[session_id] = session
        logger.info(f"Created new session: {session_id}")
        return session
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Retrieve a session by ID.
        
        Args:
            session_id: Unique session identifier
        
        Returns:
            Session dictionary or None if not found
        """
        session = self.sessions.get(session_id)
        if session:
            logger.info(f"Retrieved session: {session_id}")
        else:
            logger.warning(f"Session not found: {session_id}")
        return session
    
    def get_or_create_session(self, session_id: Optional[str] = None) -> Dict:
        """Get an existing session or create a new one.
        
        Args:
            session_id: Optional session ID to retrieve
        
        Returns:
            Session dictionary (existing or new)
        """
        if session_id:
            session = self.get_session(session_id)
            if session:
                logger.info(f"Resuming session: {session_id}")
                return session
        
        return self.create_session()
    
    def update_session(self, session_id: str, data: Dict) -> bool:
        """Update session with new data.
        
        Args:
            session_id: Session to update
            data: Data to add to session
        
        Returns:
            True if updated successfully, False otherwise
        """
        session = self.get_session(session_id)
        if not session:
            logger.error(f"Cannot update non-existent session: {session_id}")
            return False
        
        session['updated_at'] = datetime.now().isoformat()
        session['review_count'] += 1
        session['history'].append({
            'timestamp': datetime.now().isoformat(),
            'data': data
        })
        
        logger.info(f"Updated session: {session_id}")
        return True
    
    def close_session(self, session_id: str) -> bool:
        """Mark a session as closed.
        
        Args:
            session_id: Session to close
        
        Returns:
            True if closed successfully, False otherwise
        """
        session = self.get_session(session_id)
        if not session:
            logger.error(f"Cannot close non-existent session: {session_id}")
            return False
        
        session['status'] = 'closed'
        session['closed_at'] = datetime.now().isoformat()
        logger.info(f"Closed session: {session_id}")
        return True
    
    def list_sessions(self, status: Optional[str] = None) -> List[Dict]:
        """List all sessions, optionally filtered by status.
        
        Args:
            status: Optional status filter ('active', 'closed')
        
        Returns:
            List of session dictionaries
        """
        if status:
            sessions = [s for s in self.sessions.values() if s['status'] == status]
            logger.info(f"Listed {len(sessions)} sessions with status: {status}")
        else:
            sessions = list(self.sessions.values())
            logger.info(f"Listed all {len(sessions)} sessions")
        
        return sessions
    
    def get_session_history(self, session_id: str) -> List[Dict]:
        """Get the review history for a session.
        
        Args:
            session_id: Session ID
        
        Returns:
            List of historical review data
        """
        session = self.get_session(session_id)
        if not session:
            return []
        
        history = session.get('history', [])
        logger.info(f"Retrieved {len(history)} history items for session: {session_id}")
        return history
    
    def clear_old_sessions(self, days: int = 30) -> int:
        """Clear sessions older than specified days.
        
        Args:
            days: Age threshold in days
        
        Returns:
            Number of sessions cleared
        """
        from datetime import timedelta
        
        cutoff = datetime.now() - timedelta(days=days)
        to_remove = []
        
        for session_id, session in self.sessions.items():
            created_at = datetime.fromisoformat(session['created_at'])
            if created_at < cutoff:
                to_remove.append(session_id)
        
        for session_id in to_remove:
            del self.sessions[session_id]
        
        logger.info(f"Cleared {len(to_remove)} old sessions")
        return len(to_remove)
