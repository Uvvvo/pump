"""
وحدة الأمان لتطبيق iPump
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
        """تشفير كلمة المرور باستخدام SHA-256"""
        salt = "ipump_salt_2024"  # في التطبيق الحقيقي، يجب استخدام salt عشوائي
        return hashlib.sha256((password + salt).encode()).hexdigest()
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """التحقق من كلمة المرور"""
        return self.hash_password(password) == hashed
    
    def generate_secure_token(self, length: int = 32) -> str:
        """إنشاء رمز أمان عشوائي"""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def check_login_attempt(self, username: str) -> Tuple[bool, Optional[str]]:
        """التحقق من محاولات تسجيل الدخول"""
        now = datetime.now()
        
        if username in self.failed_attempts:
            attempts, last_attempt = self.failed_attempts[username]
            
            if now - last_attempt < self.lockout_duration:
                if attempts >= self.max_attempts:
                    remaining_time = self.lockout_duration - (now - last_attempt)
                    return False, f"الحساب مؤقتاً. حاول مرة أخرى بعد {int(remaining_time.total_seconds() / 60)} دقيقة"
            else:
                # إعادة تعيين العداد بعد انتهاء مدة القفل
                del self.failed_attempts[username]
        
        return True, None
    
    def record_failed_attempt(self, username: str):
        """تسجيل محاولة فاشلة"""
        now = datetime.now()
        
        if username in self.failed_attempts:
            attempts, _ = self.failed_attempts[username]
            self.failed_attempts[username] = (attempts + 1, now)
        else:
            self.failed_attempts[username] = (1, now)
        
        self.logger.warning(f"محاولة تسجيل دخول فاشلة للمستخدم: {username}")
    
    def reset_failed_attempts(self, username: str):
        """إعادة تعيين محاولات تسجيل الدخول الفاشلة"""
        if username in self.failed_attempts:
            del self.failed_attempts[username]
    
    def validate_input(self, input_str: str, max_length: int = 255) -> bool:
        """التحقق من صحة الإدخال"""
        if not input_str or len(input_str) > max_length:
            return False
        
        # منع الأحرف الخطرة
        dangerous_chars = [';', '"', "'", '<', '>', '|', '&', '$', '`']
        return not any(char in input_str for char in dangerous_chars)

# إنشاء نسخة عامة من مدير الأمان
security_manager = SecurityManager()