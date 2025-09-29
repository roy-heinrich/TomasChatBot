"""
SQL Injection Protection for TOMAS Chatbot
==========================================

Simple, focused security module that only blocks SQL injection attempts.
No dashboard, no complex monitoring - just pure SQL injection protection.
"""

import re
import logging
from typing import List

logger = logging.getLogger(__name__)

class SQLInjectionProtector:
    """Simple SQL injection protection focused only on blocking malicious SQL patterns"""
    
    def __init__(self):
        # SQL injection patterns - comprehensive but focused
        self.sql_patterns = [
            # Basic SQL keywords
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\b)",
            
            # Boolean-based SQL injection
            r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
            r"(\b(OR|AND)\s+'.*'\s*=\s*'.*')",
            r"(\bOR\s+1\s*=\s*1\b)",
            r"(\bAND\s+1\s*=\s*1\b)",
            r"(\bOR\s+'.*'\s*=\s*'.*'\b)",
            r"(\bAND\s+'.*'\s*=\s*'.*'\b)",
            
            # Union-based SQL injection
            r"(\bUNION\s+SELECT\b)",
            r"(\bUNION\s+ALL\s+SELECT\b)",
            
            # Table manipulation
            r"(\bDROP\s+TABLE\b)",
            r"(\bINSERT\s+INTO\b)",
            r"(\bDELETE\s+FROM\b)",
            r"(\bUPDATE\s+.*\s+SET\b)",
            
            # Stored procedures and functions
            r"(\bEXEC\s*\()",
            r"(\bEXECUTE\s*\()",
            r"(\bSCRIPT\s*\()",
            
            # SQL comments
            r"(--|\#|\/\*|\*\/)",
            
            # Time-based SQL injection
            r"(\bSLEEP\s*\()",
            r"(\bWAITFOR\s+DELAY\b)",
            r"(\bBENCHMARK\s*\()",
            
            # Information gathering
            r"(\bINFORMATION_SCHEMA\b)",
            r"(\bSYSOBJECTS\b)",
            r"(\bSYSCOLUMNS\b)",
            r"(\bSYSUSERS\b)",
            
            # Database-specific patterns
            r"(\bCONCAT\s*\()",
            r"(\bSUBSTRING\s*\()",
            r"(\bASCII\s*\()",
            r"(\bCHAR\s*\()",
            r"(\bLENGTH\s*\()",
            r"(\bCOUNT\s*\()",
            
            # Error-based SQL injection
            r"(\bEXTRACTVALUE\s*\()",
            r"(\bUPDATEXML\s*\()",
            r"(\bXP_CMDSHELL\b)",
            
            # Blind SQL injection
            r"(\bLIKE\s+'.*%'.*OR\b)",
            r"(\bRLIKE\s+'.*'.*OR\b)",
            
            # Advanced patterns
            r"(\bLOAD_FILE\s*\()",
            r"(\bINTO\s+OUTFILE\b)",
            r"(\bINTO\s+DUMPFILE\b)",
            r"(\bLOAD\s+DATA\s+INFILE\b)",
            
            # Common SQL injection techniques
            r"(\bOR\s+'.*'\s*LIKE\s*'.*'\b)",
            r"(\bAND\s+'.*'\s*LIKE\s*'.*'\b)",
            r"(\bOR\s+'.*'\s*RLIKE\s*'.*'\b)",
            r"(\bAND\s+'.*'\s*RLIKE\s*'.*'\b)",
            
            # Hexadecimal and binary
            r"(\b0x[0-9a-fA-F]+\b)",
            r"(\bBINARY\s+'.*'\b)",
            
            # Database version detection
            r"(\b@@VERSION\b)",
            r"(\b@@DATABASE\b)",
            r"(\b@@HOSTNAME\b)",
            r"(\bUSER\s*\(\s*\)\b)",
            r"(\bDATABASE\s*\(\s*\)\b)",
            
            # Privilege escalation
            r"(\bGRANT\s+.*\s+TO\b)",
            r"(\bREVOKE\s+.*\s+FROM\b)",
            r"(\bCREATE\s+USER\b)",
            r"(\bDROP\s+USER\b)",
            
            # System commands (if SQL injection leads to command execution)
            r"(\bXP_CMDSHELL\b)",
            r"(\bSP_EXECUTESQL\b)",
            r"(\bEXEC\s+SP_\b)",
        ]
        
        # Compile patterns for better performance
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.sql_patterns]
    
    def is_sql_injection(self, text: str) -> bool:
        """Check if text contains SQL injection patterns"""
        if not text or not isinstance(text, str):
            return False
        
        text_lower = text.lower()
        
        # Check against all compiled patterns
        for pattern in self.compiled_patterns:
            if pattern.search(text_lower):
                logger.warning(f"SQL injection attempt detected: {text[:100]}...")
                return True
        
        return False
    
    def validate_request(self, request_data: dict) -> tuple[bool, str]:
        """Validate request data for SQL injection attempts"""
        try:
            # Check query field
            query = request_data.get("query", "")
            if self.is_sql_injection(query):
                return False, "SQL injection attempt detected in query"
            
            # Check conversation history
            conversation_history = request_data.get("conversation_history", [])
            if isinstance(conversation_history, list):
                for message in conversation_history:
                    if isinstance(message, dict):
                        content = message.get("content", "")
                        if self.is_sql_injection(content):
                            return False, "SQL injection attempt detected in conversation history"
            
            # Check other string fields
            for key, value in request_data.items():
                if isinstance(value, str) and self.is_sql_injection(value):
                    return False, f"SQL injection attempt detected in field: {key}"
            
            return True, "Request is safe"
            
        except Exception as e:
            logger.error(f"SQL injection validation error: {e}")
            return False, "Validation failed"

# Global SQL injection protector instance
sql_protector = SQLInjectionProtector()