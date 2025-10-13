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
        # SQL injection patterns - context-aware to reduce false positives
        self.sql_patterns = [
            # Context-aware SQL keywords (require SQL context, not standalone words)
            r"(\bSELECT\s+.*\s+FROM\b)",  # SELECT ... FROM (SQL context)
            r"(\bINSERT\s+INTO\b)",       # INSERT INTO (SQL context)
            r"(\bINSERT\s+.*\s+VALUES\b)", # INSERT ... VALUES (SQL context)
            r"(\bUPDATE\s+.*\s+SET\b)",   # UPDATE ... SET (SQL context)
            r"(\bDELETE\s+FROM\b)",        # DELETE FROM (SQL context)
            r"(\bDROP\s+(TABLE|DATABASE|INDEX|VIEW)\b)",  # DROP with object type
            r"(\bCREATE\s+(TABLE|DATABASE|INDEX|VIEW)\b)", # CREATE with object type
            r"(\bALTER\s+(TABLE|DATABASE)\b)",             # ALTER with object type
            r"(\bEXEC\s*\()",             # EXEC( (stored procedure)
            r"(\bUNION\s+SELECT\b)",      # UNION SELECT (SQL injection pattern)
            r"(\bSCRIPT\s*\()",           # SCRIPT( (potentially malicious)
            
            # Boolean-based SQL injection - Enhanced patterns
            r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
            r"(\b(OR|AND)\s+'.*'\s*=\s*'.*')",
            r"(\bOR\s+1\s*=\s*1\b)",
            r"(\bAND\s+1\s*=\s*1\b)",
            r"(\bOR\s+'.*'\s*=\s*'.*'\b)",
            r"(\bAND\s+'.*'\s*=\s*'.*'\b)",
            
            # Simple boolean patterns (SQL injection specific)
            r"(\d+'\s*=\s*'\d+)",  # '1'='1'
            r"(\d+'\s*OR\s*'\d+)",  # '1' OR '1'
            r"(\d+'\s*AND\s*'\d+)",  # '1' AND '1'
            r"(\d+'\s*=\s*'\d+'\s*OR)",  # '1'='1' OR
            r"(\d+'\s*=\s*'\d+'\s*AND)",  # '1'='1' AND
            r"(\d+'\s*OR\s*'\d+'\s*=\s*'\d+)",  # '1' OR '1'='1'
            r"(\d+'\s*AND\s*'\d+'\s*=\s*'\d+)",  # '1' AND '1'='1'
            
            # Classic SQL injection patterns
            r"(\d+'\s*=\s*'\d+'\s*OR\s*'\d+'\s*=\s*'\d+)",  # '1'='1' OR '1'='1'
            r"(\d+'\s*=\s*'\d+'\s*AND\s*'\d+'\s*=\s*'\d+)",  # '1'='1' AND '1'='1'
            
            # Union-based SQL injection
            r"(\bUNION\s+ALL\s+SELECT\b)",
            
            # Stored procedures and functions
            r"(\bEXECUTE\s*\()",
            
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
        
        # Skip checking if it's clearly HTML content (chatbot responses)
        if any(html_indicator in text_lower for html_indicator in [
            '<a href=', '<div', '<span', '<p>', '<br>', 'style=', 'target=',
            'background-color:', 'color:', 'padding:', 'border-radius:'
        ]):
            return False
        
        # Skip checking if it contains common English contexts for SQL keywords
        english_contexts = [
            'select from', 'select option', 'select menu', 'select button',
            'click select', 'please select', 'you can select', 'select achievements',
            'select the', 'select a', 'select an', 'select your', 'select one',
            'drop down', 'drop off', 'drop by', 'drop in',
            'create account', 'create profile', 'create new', 'create a',
            'insert coin', 'insert card', 'insert here', 'insert your', 'insert a',
            'update your', 'update profile', 'update information', 'update settings',
            'delete your', 'delete account', 'delete file', 'delete message'
        ]
        
        if any(context in text_lower for context in english_contexts):
            return False
        
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