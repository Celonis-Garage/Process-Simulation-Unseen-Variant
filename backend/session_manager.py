"""
Session management for maintaining consistent entities across process modifications.
"""

import time
import uuid
import random
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages user sessions to maintain consistent entities (users, items, suppliers) throughout a design session."""
    
    def __init__(self, session_timeout: int = 3600):
        """
        Initialize session manager.
        
        Args:
            session_timeout: Session timeout in seconds (default: 1 hour)
        """
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.session_timeout = session_timeout
        logger.info(f"SessionManager initialized with {session_timeout}s timeout")
    
    def create_session(self) -> str:
        """
        Create a new session and return session ID.
        
        Returns:
            str: Unique session ID
        """
        session_id = str(uuid.uuid4())
        # Generate a fixed seed for this session
        seed = random.randint(0, 2**31 - 1)
        
        self.sessions[session_id] = {
            'seed': seed,
            'created_at': time.time(),
            'last_access': time.time(),
            'request_count': 0
        }
        
        logger.info(f"Created session {session_id[:8]}... with seed {seed}")
        return session_id
    
    def get_session_seed(self, session_id: Optional[str]) -> int:
        """
        Get the fixed seed for a session. Creates session if doesn't exist.
        
        Args:
            session_id: Session ID (optional, creates new if None)
            
        Returns:
            int: Session seed
        """
        # If no session_id provided or session doesn't exist, create new
        if not session_id or session_id not in self.sessions:
            if session_id:
                logger.warning(f"Session {session_id[:8]}... not found, creating new")
            session_id = self.create_session()
        
        # Update last access time
        session = self.sessions[session_id]
        session['last_access'] = time.time()
        session['request_count'] += 1
        
        return session['seed']
    
    def reset_session(self, session_id: str) -> str:
        """
        Reset a session (generates new seed but keeps same session_id).
        
        Args:
            session_id: Session ID to reset
            
        Returns:
            str: Session ID (same as input)
        """
        if session_id in self.sessions:
            # Generate new seed for the session
            new_seed = random.randint(0, 2**31 - 1)
            self.sessions[session_id]['seed'] = new_seed
            self.sessions[session_id]['last_access'] = time.time()
            self.sessions[session_id]['request_count'] = 0
            logger.info(f"Reset session {session_id[:8]}... with new seed {new_seed}")
        else:
            # Session doesn't exist, create new
            logger.warning(f"Attempted to reset non-existent session {session_id[:8]}..., creating new")
            session_id = self.create_session()
        
        return session_id
    
    def delete_session(self, session_id: str):
        """
        Delete a session.
        
        Args:
            session_id: Session ID to delete
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Deleted session {session_id[:8]}...")
    
    def cleanup_expired_sessions(self):
        """Remove sessions that have expired."""
        current_time = time.time()
        expired = []
        
        for session_id, session_data in self.sessions.items():
            if current_time - session_data['last_access'] > self.session_timeout:
                expired.append(session_id)
        
        for session_id in expired:
            del self.sessions[session_id]
            logger.info(f"Cleaned up expired session {session_id[:8]}...")
        
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session information.
        
        Args:
            session_id: Session ID
            
        Returns:
            Session info dict or None if not found
        """
        return self.sessions.get(session_id)
    
    def get_active_session_count(self) -> int:
        """Get number of active sessions."""
        return len(self.sessions)


# Global session manager instance
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Get the global session manager instance."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager

