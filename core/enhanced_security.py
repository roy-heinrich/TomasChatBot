"""
Enhanced Security Module for TOMAS Chatbot
Comprehensive input validation and error protection
"""
import re
import logging
import html
from typing import Dict, List, Tuple, Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class EnhancedSecurityValidator:
    """Enhanced security validation with comprehensive input protection"""
    
    def __init__(self):
        # SQL injection patterns (from existing security.py)
        self.sql_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\b)",
            r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
            r"(\bOR\s+1\s*=\s*1\b)",
            r"(\bAND\s+1\s*=\s*1\b)",
            r"(\d+'\s*=\s*'\d+)",
            r"(\bUNION\s+SELECT\b)",
            r"(\bDROP\s+TABLE\b)",
            r"(\bINSERT\s+INTO\b)",
            r"(\bDELETE\s+FROM\b)",
            r"(\bUPDATE\s+.*\s+SET\b)",
            r"(\bEXEC\s*\()",
            r"(\bEXECUTE\s*\()",
            r"(\bSCRIPT\s*\()",
            r"(--|\#|\/\*|\*\/)",
            r"(\bSLEEP\s*\()",
            r"(\bWAITFOR\s+DELAY\b)",
            r"(\bBENCHMARK\s*\()",
            r"(\bINFORMATION_SCHEMA\b)",
            r"(\bSYSOBJECTS\b)",
            r"(\bSYSCOLUMNS\b)",
            r"(\bSYSUSERS\b)",
            r"(\bCONCAT\s*\()",
            r"(\bSUBSTRING\s*\()",
            r"(\bASCII\s*\()",
            r"(\bCHAR\s*\()",
            r"(\bLENGTH\s*\()",
            r"(\bCOUNT\s*\()",
            r"(\bEXTRACTVALUE\s*\()",
            r"(\bUPDATEXML\s*\()",
            r"(\bXP_CMDSHELL\b)",
            r"(\bLIKE\s+'.*%'.*OR\b)",
            r"(\bRLIKE\s+'.*'.*OR\b)",
            r"(\bLOAD_FILE\s*\()",
            r"(\bINTO\s+OUTFILE\b)",
            r"(\bINTO\s+DUMPFILE\b)",
            r"(\bLOAD\s+DATA\s+INFILE\b)",
            r"(\bOR\s+'.*'\s*LIKE\s*'.*'\b)",
            r"(\bAND\s+'.*'\s*LIKE\s*'.*'\b)",
            r"(\bOR\s+'.*'\s*RLIKE\s*'.*'\b)",
            r"(\bAND\s+'.*'\s*RLIKE\s*'.*'\b)",
            r"(\b0x[0-9a-fA-F]+\b)",
            r"(\bBINARY\s+'.*'\b)",
            r"(\b@@VERSION\b)",
            r"(\b@@DATABASE\b)",
            r"(\b@@HOSTNAME\b)",
            r"(\bUSER\s*\(\s*\)\b)",
            r"(\bDATABASE\s*\(\s*\)\b)",
            r"(\bGRANT\s+.*\s+TO\b)",
            r"(\bREVOKE\s+.*\s+FROM\b)",
            r"(\bCREATE\s+USER\b)",
            r"(\bDROP\s+USER\b)",
            r"(\bXP_CMDSHELL\b)",
            r"(\bSP_EXECUTESQL\b)",
            r"(\bEXEC\s+SP_\b)",
        ]
        
        # XSS patterns
        self.xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>",
            r"<object[^>]*>",
            r"<embed[^>]*>",
            r"<link[^>]*>",
            r"<meta[^>]*>",
            r"<style[^>]*>.*?</style>",
            r"expression\s*\(",
            r"url\s*\(",
            r"@import",
            r"vbscript:",
            r"data:text/html",
            r"data:application/javascript",
        ]
        
        # Command injection patterns - more specific to avoid false positives
        self.command_patterns = [
            # Dangerous system commands
            r"(\brm\s+-rf\s+/)",
            r"(\bdel\s+/s\s+c:\\)",
            r"(\bformat\s+c:\s+/q)",
            r"(\bchmod\s+777\s+)",
            r"(\bchown\s+root\s+)",
            r"(\bkill\s+-9\s+)",
            r"(\bkillall\s+)",
            r"(\bshutdown\s+-h\s+now)",
            r"(\breboot\s+-f)",
            r"(\bhalt\s+-f)",
            r"(\bpoweroff\s+-f)",
            
            # File system manipulation
            r"(\bmkdir\s+/tmp/\w+)",
            r"(\btouch\s+/tmp/\w+)",
            r"(\becho\s+.*\s*>\s*/etc/)",
            r"(\bcat\s+.*\s*>\s*/etc/)",
            
            # Network tools with malicious intent
            r"(\bwget\s+.*\s+-O\s+/tmp/)",
            r"(\bcurl\s+.*\s+-o\s+/tmp/)",
            r"(\bnc\s+-l\s+-p\s+)",
            r"(\btelnet\s+.*\s+)",
            r"(\bssh\s+.*\s+.*\s+)",
            r"(\bftp\s+.*\s+)",
            r"(\bnetcat\s+-l\s+-p\s+)",
            r"(\bsocat\s+.*\s+)",
            
            # Script execution
            r"(\bperl\s+-e\s+.*\s+)",
            r"(\bpython\s+-c\s+.*\s+)",
            r"(\bruby\s+-e\s+.*\s+)",
            r"(\bphp\s+-r\s+.*\s+)",
            r"(\bnode\s+-e\s+.*\s+)",
            r"(\bbash\s+-c\s+.*\s+)",
            r"(\bsh\s+-c\s+.*\s+)",
            r"(\bcmd\s+/c\s+.*\s+)",
            r"(\bpowershell\s+-Command\s+.*\s+)",
            
            # Windows-specific dangerous commands
            r"(\bwscript\s+.*\s+)",
            r"(\bcscript\s+.*\s+)",
            r"(\breg\s+add\s+.*\s+)",
            r"(\breg\s+delete\s+.*\s+)",
            r"(\bsc\s+create\s+.*\s+)",
            r"(\bsc\s+delete\s+.*\s+)",
            r"(\bnet\s+user\s+.*\s+.*\s+)",
            r"(\bnet\s+localgroup\s+.*\s+.*\s+)",
            r"(\btaskkill\s+/f\s+)",
            r"(\bschtasks\s+/create\s+)",
            r"(\bwmic\s+.*\s+)",
            r"(\bdiskpart\s+)",
            r"(\bbcdedit\s+.*\s+)",
            r"(\bregsvr32\s+.*\s+)",
            r"(\brundll32\s+.*\s+)",
            r"(\bmsiexec\s+.*\s+)",
            
            # System information gathering (potentially malicious)
            r"(\bwhoami\s+)",
            r"(\buname\s+-a)",
            r"(\bhostname\s+)",
            # Removed 'who' pattern - too broad, causes false positives
            r"(\bfinger\s+.*\s+)",
            r"(\blast\s+.*\s+)",
            r"(\bhistory\s+.*\s+)",
            r"(\bpasswd\s+.*\s+)",
            r"(\bsu\s+.*\s+)",
            r"(\bsudo\s+.*\s+)",
        ]
        
        # Null byte patterns
        self.null_byte_patterns = [
            r"\x00",
            r"%00",
            r"\0",
            r"\\0",
        ]
        
        # Path traversal patterns
        self.path_traversal_patterns = [
            r"\.\./",
            r"\.\.\\",
            r"\.\.%2f",
            r"\.\.%5c",
            r"%2e%2e%2f",
            r"%2e%2e%5c",
            r"\.\.%252f",
            r"\.\.%255c",
            r"\.\.%c0%af",
            r"\.\.%c1%9c",
            r"\.\.%c0%2f",
            r"\.\.%c1%af",
        ]
        
        # Compile all patterns for better performance
        self.compiled_sql_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.sql_patterns]
        self.compiled_xss_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.xss_patterns]
        self.compiled_command_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.command_patterns]
        self.compiled_null_byte_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.null_byte_patterns]
        self.compiled_path_traversal_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.path_traversal_patterns]
        
        # Input length limits
        self.max_input_length = 1000
        self.max_query_length = 500
        self.max_conversation_history = 50
        
        # Character restrictions - more permissive for school context
        self.allowed_chars_pattern = re.compile(r'^[a-zA-Z0-9\s\.\,\!\?\;\:\-\(\)\'\"\@\#\$\%\&\*\+\=\[\]\{\}\|\~\`\<\>\/\\\_\u00c0-\u017f\u0100-\u024f\u1e00-\u1eff\u1f00-\u1fff\u2000-\u206f\u2070-\u209f\u20a0-\u20cf\u2100-\u214f\u2150-\u218f\u2190-\u21ff\u2200-\u22ff\u2300-\u23ff\u2400-\u243f\u2440-\u245f\u2460-\u24ff\u2500-\u257f\u2580-\u259f\u25a0-\u25ff\u2600-\u26ff\u2700-\u27bf\u27c0-\u27ef\u27f0-\u27ff\u2800-\u28ff\u2900-\u297f\u2980-\u29ff\u2a00-\u2aff\u2b00-\u2bff\u2c00-\u2c5f\u2c60-\u2c7f\u2c80-\u2cff\u2d00-\u2d2f\u2d30-\u2d7f\u2d80-\u2dff\u2e00-\u2e7f\u2e80-\u2eff\u2f00-\u2fff\u3000-\u303f\u3040-\u309f\u30a0-\u30ff\u3100-\u312f\u3130-\u318f\u3190-\u319f\u31a0-\u31bf\u31c0-\u31ef\u31f0-\u31ff\u3200-\u32ff\u3300-\u33ff\u3400-\u4dbf\u4dc0-\u4dff\u4e00-\u9fff\uf900-\ufaff\ufb00-\ufb4f\ufb50-\ufdff\ufe00-\ufe0f\ufe10-\ufe1f\ufe20-\ufe2f\ufe30-\ufe4f\ufe50-\ufe6f\ufe70-\ufeff\uff00-\uffef\ufff0-\uffff]+$')
    
    def validate_input(self, text: str, input_type: str = "query") -> Tuple[bool, str, Dict[str, Any]]:
        """
        Comprehensive input validation
        
        Args:
            text: Input text to validate
            input_type: Type of input (query, conversation_history, etc.)
            
        Returns:
            Tuple of (is_valid, error_message, validation_details)
        """
        validation_details = {
            "input_length": len(text) if text else 0,
            "input_type": input_type,
            "checks_performed": [],
            "threats_detected": []
        }
        
        try:
            # 1. Basic input validation
            if not text or not isinstance(text, str):
                return False, "Empty or invalid input", validation_details
            
            # 2. Length validation
            max_length = self.max_query_length if input_type == "query" else self.max_input_length
            if len(text) > max_length:
                validation_details["threats_detected"].append("input_too_long")
                return False, f"Input too long (max {max_length} characters)", validation_details
            
            validation_details["checks_performed"].append("length_check")
            
            # 3. Character validation (relaxed for school context)
            # Only check for truly dangerous characters
            dangerous_chars = ['\x00', '\x01', '\x02', '\x03', '\x04', '\x05', '\x06', '\x07', '\x08', '\x0b', '\x0c', '\x0e', '\x0f']
            if any(char in text for char in dangerous_chars):
                validation_details["threats_detected"].append("invalid_characters")
                return False, "Input contains dangerous characters", validation_details
            
            validation_details["checks_performed"].append("character_check")
            
            # 4. SQL injection check
            if self._check_sql_injection(text):
                validation_details["threats_detected"].append("sql_injection")
                return False, "SQL injection attempt detected", validation_details
            
            validation_details["checks_performed"].append("sql_injection_check")
            
            # 5. XSS check
            if self._check_xss(text):
                validation_details["threats_detected"].append("xss")
                return False, "XSS attempt detected", validation_details
            
            validation_details["checks_performed"].append("xss_check")
            
            # 6. Command injection check
            if self._check_command_injection(text):
                validation_details["threats_detected"].append("command_injection")
                return False, "Command injection attempt detected", validation_details
            
            validation_details["checks_performed"].append("command_injection_check")
            
            # 7. Null byte check
            if self._check_null_bytes(text):
                validation_details["threats_detected"].append("null_bytes")
                return False, "Null byte injection detected", validation_details
            
            validation_details["checks_performed"].append("null_byte_check")
            
            # 8. Path traversal check
            if self._check_path_traversal(text):
                validation_details["threats_detected"].append("path_traversal")
                return False, "Path traversal attempt detected", validation_details
            
            validation_details["checks_performed"].append("path_traversal_check")
            
            # 9. HTML encoding check
            if self._check_html_encoding(text):
                validation_details["threats_detected"].append("html_encoding")
                return False, "Suspicious HTML encoding detected", validation_details
            
            validation_details["checks_performed"].append("html_encoding_check")
            
            # 10. URL validation (if contains URLs)
            if self._check_malicious_urls(text):
                validation_details["threats_detected"].append("malicious_url")
                return False, "Malicious URL detected", validation_details
            
            validation_details["checks_performed"].append("url_check")
            
            return True, "Input is valid", validation_details
            
        except Exception as e:
            logger.error(f"Input validation error: {e}")
            return False, "Validation failed", validation_details
    
    def _check_sql_injection(self, text: str) -> bool:
        """Check for SQL injection patterns"""
        if not text:
            return False
        
        text_lower = text.lower()
        
        # Skip checking if it's clearly HTML content (chatbot responses)
        if any(html_indicator in text_lower for html_indicator in [
            '<a href=', '<div', '<span', '<p>', '<br>', 'style=', 'target=',
            'background-color:', 'color:', 'padding:', 'border-radius:'
        ]):
            return False
        
        for pattern in self.compiled_sql_patterns:
            if pattern.search(text_lower):
                logger.warning(f"SQL injection attempt detected: {text[:100]}...")
                return True
        
        return False
    
    def _check_xss(self, text: str) -> bool:
        """Check for XSS patterns"""
        if not text:
            return False
        
        for pattern in self.compiled_xss_patterns:
            if pattern.search(text):
                logger.warning(f"XSS attempt detected: {text[:100]}...")
                return True
        
        return False
    
    def _check_command_injection(self, text: str) -> bool:
        """Check for command injection patterns"""
        if not text:
            return False
        
        text_lower = text.lower()
        
        for pattern in self.compiled_command_patterns:
            if pattern.search(text_lower):
                logger.warning(f"Command injection attempt detected: {text[:100]}...")
                return True
        
        return False
    
    def _check_null_bytes(self, text: str) -> bool:
        """Check for null byte injection"""
        if not text:
            return False
        
        for pattern in self.compiled_null_byte_patterns:
            if pattern.search(text):
                logger.warning(f"Null byte injection detected: {text[:100]}...")
                return True
        
        return False
    
    def _check_path_traversal(self, text: str) -> bool:
        """Check for path traversal patterns"""
        if not text:
            return False
        
        for pattern in self.compiled_path_traversal_patterns:
            if pattern.search(text):
                logger.warning(f"Path traversal attempt detected: {text[:100]}...")
                return True
        
        return False
    
    def _check_html_encoding(self, text: str) -> bool:
        """Check for suspicious HTML encoding"""
        if not text:
            return False
        
        # Check for excessive HTML entities
        html_entity_count = text.count('&')
        if html_entity_count > len(text) * 0.3:  # More than 30% HTML entities
            logger.warning(f"Excessive HTML encoding detected: {text[:100]}...")
            return True
        
        # Check for suspicious HTML entity patterns
        suspicious_patterns = [
            r'&#x[0-9a-fA-F]+;',
            r'&#[0-9]+;',
            r'&[a-zA-Z]+;',
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, text):
                logger.warning(f"Suspicious HTML encoding detected: {text[:100]}...")
                return True
        
        return False
    
    def _check_malicious_urls(self, text: str) -> bool:
        """Check for malicious URLs"""
        if not text:
            return False
        
        # Extract URLs from text
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, text)
        
        for url in urls:
            try:
                parsed = urlparse(url)
                
                # Check for suspicious domains (only truly malicious ones)
                suspicious_domains = [
                    'malicious.com', 'phishing.com', 'virus.com', 'malware.com',
                    'hack.com', 'exploit.com', 'backdoor.com'
                ]
                
                if any(domain in parsed.netloc.lower() for domain in suspicious_domains):
                    logger.warning(f"Suspicious URL detected: {url}")
                    return True
                
                # Check for suspicious schemes
                if parsed.scheme not in ['http', 'https']:
                    logger.warning(f"Suspicious URL scheme detected: {url}")
                    return True
                
            except Exception:
                logger.warning(f"Invalid URL detected: {url}")
                return True
        
        return False
    
    def sanitize_input(self, text: str) -> str:
        """Sanitize input by removing dangerous characters"""
        if not text:
            return ""
        
        # HTML encode special characters
        sanitized = html.escape(text)
        
        # Remove null bytes
        sanitized = sanitized.replace('\x00', '')
        sanitized = sanitized.replace('%00', '')
        sanitized = sanitized.replace('\\0', '')
        
        # Remove path traversal sequences
        for pattern in self.path_traversal_patterns:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
        
        return sanitized
    
    def validate_conversation_history(self, conversation_history: List[Dict]) -> Tuple[bool, str]:
        """Validate conversation history"""
        if not isinstance(conversation_history, list):
            return False, "Conversation history must be a list"
        
        if len(conversation_history) > self.max_conversation_history:
            return False, f"Too many messages in conversation history (max {self.max_conversation_history})"
        
        for i, message in enumerate(conversation_history):
            if not isinstance(message, dict):
                return False, f"Message {i} must be a dictionary"
            
            if 'content' not in message:
                return False, f"Message {i} missing 'content' field"
            
            content = message['content']
            is_valid, error_msg, _ = self.validate_input(content, "conversation_history")
            if not is_valid:
                return False, f"Message {i}: {error_msg}"
        
        return True, "Conversation history is valid"

# Global enhanced security validator instance
enhanced_security = EnhancedSecurityValidator()
