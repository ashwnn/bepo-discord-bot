import secrets
import time

class ConfirmationManager:
    def __init__(self):
        self.pending = {}

    def create(self, user_id: int, action_type: str, **metadata) -> str:
        """
        Create a confirmation token
        
        Args:
            user_id: Discord user ID
            action_type: Type of action to confirm
            **metadata: Additional metadata (e.g., server_name)
            
        Returns:
            Confirmation token
        """
        token = secrets.token_urlsafe(16)
        self.pending[token] = {
            "user_id": user_id,
            "action_type": action_type,
            "timestamp": time.time(),
            **metadata
        }
        return token

    def consume(self, token: str):
        """Consume a token (returns action data or None if invalid/expired)"""
        action = self.pending.pop(token, None)
        if action and (time.time() - action["timestamp"]) < 120:
            return action
        return None

confirmation_manager = ConfirmationManager()
