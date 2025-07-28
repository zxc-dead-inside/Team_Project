import random
import string

import validators


class ShortCodeGenerator:
    BASE62_CHARS = string.ascii_letters + string.digits
    
    def __init__(self, length: int = 6):
        self.length = length
    
    def generate_random(self, length: int | None = None) -> str:
        """Generate a random short code"""
        code_length = length or self.length
        return ''.join(random.choices(self.BASE62_CHARS, k=code_length))
    
    def encode_id(self, id: int) -> str:
        """Convert integer ID to base62 string"""
        if id == 0:
            return self.BASE62_CHARS[0]
        
        result = []
        base = len(self.BASE62_CHARS)
        
        while id > 0:
            result.append(self.BASE62_CHARS[id % base])
            id //= base
        
        return ''.join(reversed(result))
    
    def decode_id(self, code: str) -> int:
        """Convert base62 string back to integer ID"""
        base = len(self.BASE62_CHARS)
        result = 0
        
        for char in code:
            result = result * base + self.BASE62_CHARS.index(char)
        
        return result

def is_valid_url(url: str) -> bool:
    """Validate URL and check for security issues"""
    if not validators.url(url):
        return False
    
    # Security checks - block internal/private networks
    blocked_patterns = [
        'localhost', '127.0.0.1', '0.0.0.0', '10.', '192.168.', '172.',
        'file://', 'ftp://', 'javascript:', 'data:'
    ]
    
    url_lower = url.lower()
    return not any(pattern in url_lower for pattern in blocked_patterns)