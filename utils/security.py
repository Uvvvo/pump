"""
Security module for the iPump application.
"""

import hashlib
import secrets
import string
from typing import Optional, Tuple
import logging
from datetime import datetime, timedelta

class SecurityManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.failed_attempts = {}
        self.lockout_duration = timedelta(minutes=30)
        self.max_attempts = 5
        
    def hash_password(self, password: str) -> str:
        """Hash a password using SHA-256."""
        salt = "ipump_salt_2024"  # In a production application an unpredictable salt should be used
        return hashlib.sha256((password + salt).encode()).hexdigest()

    def verify_password(self, password: str, hashed: str) -> bool:
        """Validate a password against a stored hash."""
        return self.hash_password(password) == hashed

    def generate_secure_token(self, length: int = 32) -> str:
        """Generate a random security token."""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    def check_login_attempt(self, username: str) -> Tuple[bool, Optional[str]]:
        """Check whether the user is allowed to attempt a login."""
        now = datetime.now()

        if username in self.failed_attempts:
            attempts, last_attempt = self.failed_attempts[username]

            if now - last_attempt < self.lockout_duration:
                if attempts >= self.max_attempts:
                    remaining_time = self.lockout_duration - (now - last_attempt)
                    return False, f"Account temporarily locked. Try again in {int(remaining_time.total_seconds() / 60)} minutes"
            else:
                # Reset the counter after the lockout duration ends
                del self.failed_attempts[username]

        return True, None

    def record_failed_attempt(self, username: str):
        """Record a failed login attempt."""
        now = datetime.now()

        if username in self.failed_attempts:
            attempts, _ = self.failed_attempts[username]
            self.failed_attempts[username] = (attempts + 1, now)
        else:
            self.failed_attempts[username] = (1, now)

        self.logger.warning(f"Failed login attempt for user: {username}")

    def reset_failed_attempts(self, username: str):
        """Clear any recorded failed login attempts."""
        if username in self.failed_attempts:
            del self.failed_attempts[username]

    def validate_input(self, input_str: str, max_length: int = 255) -> bool:
        """Validate user input."""
        if not input_str or len(input_str) > max_length:
            return False

        # Prevent dangerous characters
        dangerous_chars = [';', '"', "'", '<', '>', '|', '&', '$', '`']
        return not any(char in input_str for char in dangerous_chars)

# Expose a shared instance of the security manager
security_manager = SecurityManager()
