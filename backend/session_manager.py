"""
Session management for maintaining consistent entities across process modifications.
"""

import time
import uuid
import random
import re
from typing import Dict, Any, Optional, List, Tuple
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
            'request_count': 0,
            'entities': None,  # Will store {users, items, suppliers} once generated
            'entity_constraints': None  # Will store user-specified constraints
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
        Reset a session (generates new seed and clears entities).
        
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
            self.sessions[session_id]['entities'] = None  # Clear stored entities
            self.sessions[session_id]['entity_constraints'] = None  # Clear constraints
            logger.info(f"Reset session {session_id[:8]}... with new seed {new_seed} and cleared entities")
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
    
    def store_entities(self, session_id: str, users: List[str], items: List[Dict], suppliers: List[str]):
        """
        Store generated entities for a session.
        
        Args:
            session_id: Session ID
            users: List of user IDs
            items: List of item dictionaries
            suppliers: List of supplier IDs
        """
        if session_id in self.sessions:
            self.sessions[session_id]['entities'] = {
                'users': users,
                'items': items,
                'suppliers': suppliers
            }
            logger.info(f"Stored entities for session {session_id[:8]}...: "
                       f"{len(users)} users, {len(items)} items, {len(suppliers)} suppliers")
    
    def get_entities(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get stored entities for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            Dict with users, items, suppliers or None if not stored
        """
        if session_id in self.sessions:
            return self.sessions[session_id].get('entities')
        return None
    
    def store_entity_constraints(self, session_id: str, constraints: Dict[str, Any]):
        """
        Store user-specified entity constraints for a session.
        
        Args:
            session_id: Session ID
            constraints: Dictionary with entity constraints from user input
        """
        if session_id in self.sessions:
            self.sessions[session_id]['entity_constraints'] = constraints
            logger.info(f"Stored entity constraints for session {session_id[:8]}...: {constraints}")
    
    def get_entity_constraints(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get stored entity constraints for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            Dict with entity constraints or None if not stored
        """
        if session_id in self.sessions:
            return self.sessions[session_id].get('entity_constraints')
        return None
    
    @staticmethod
    def extract_entity_info_from_prompt(prompt: str) -> Dict[str, Any]:
        """
        Extract entity information (users, items, suppliers) from user prompt.
        
        Args:
            prompt: User's natural language prompt
            
        Returns:
            Dictionary with extracted entity information
        """
        constraints = {}
        prompt_lower = prompt.lower()
        
        # Extract user information
        user_patterns = [
            r'user[s]?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:,\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)*)',  # "users John, Jane"
            r'customer[s]?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:,\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)*)',  # "customers Alice, Bob"
            r'(\d+)\s+users?',  # "3 users"
            r'(\d+)\s+customers?',  # "2 customers"
        ]
        
        for pattern in user_patterns:
            match = re.search(pattern, prompt, re.IGNORECASE)
            if match:
                if match.group(1).isdigit():
                    constraints['num_users'] = int(match.group(1))
                    logger.debug(f"Extracted user count: {constraints['num_users']}")
                else:
                    # Extract names
                    names = [name.strip() for name in match.group(1).split(',')]
                    constraints['user_names'] = names
                    constraints['num_users'] = len(names)
                    logger.debug(f"Extracted user names: {names}")
                break
        
        # Extract item information
        item_patterns = [
            r'item[s]?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:,\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)*)',  # "items Laptop, Phone"
            r'product[s]?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:,\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)*)',  # "products Monitor, Keyboard"
            r'(\d+)\s+items?',  # "5 items"
            r'(\d+)\s+products?',  # "3 products"
        ]
        
        for pattern in item_patterns:
            match = re.search(pattern, prompt, re.IGNORECASE)
            if match:
                if match.group(1).isdigit():
                    constraints['num_items'] = int(match.group(1))
                    logger.debug(f"Extracted item count: {constraints['num_items']}")
                else:
                    # Extract item names
                    names = [name.strip() for name in match.group(1).split(',')]
                    constraints['item_names'] = names
                    constraints['num_items'] = len(names)
                    logger.debug(f"Extracted item names: {names}")
                break
        
        # Extract supplier information
        supplier_patterns = [
            r'supplier[s]?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:,\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)*)',  # "suppliers Acme, GlobalTech"
            r'vendor[s]?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:,\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)*)',  # "vendors FastShip, QuickSupply"
            r'(\d+)\s+suppliers?',  # "2 suppliers"
            r'(\d+)\s+vendors?',  # "3 vendors"
        ]
        
        for pattern in supplier_patterns:
            match = re.search(pattern, prompt, re.IGNORECASE)
            if match:
                if match.group(1).isdigit():
                    constraints['num_suppliers'] = int(match.group(1))
                    logger.debug(f"Extracted supplier count: {constraints['num_suppliers']}")
                else:
                    # Extract supplier names
                    names = [name.strip() for name in match.group(1).split(',')]
                    constraints['supplier_names'] = names
                    constraints['num_suppliers'] = len(names)
                    logger.debug(f"Extracted supplier names: {names}")
                break
        
        return constraints if constraints else None


# Global session manager instance
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Get the global session manager instance."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager

