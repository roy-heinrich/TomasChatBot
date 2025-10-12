#!/usr/bin/env python3
"""
Comprehensive Debug Logging System
Provides detailed logging for debugging entity extraction and fuzzy matching issues
"""

import logging
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class DebugEvent:
    """Structured debug event"""
    timestamp: str
    event_type: str
    query: str
    details: Dict[str, Any]
    severity: str = "INFO"

class DebugLogger:
    """Comprehensive debug logging system"""
    
    def __init__(self, log_file: str = "chatbot_debug.log", enable_console: bool = False):
        self.log_file = log_file
        self.enable_console = enable_console
        self.events: List[DebugEvent] = []
        
        # Setup logging
        self.logger = logging.getLogger('chatbot_debug')
        self.logger.setLevel(logging.DEBUG)
        
        # File handler
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler (optional)
        if enable_console:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            self.logger.addHandler(console_handler)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        if enable_console:
            console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
    
    def log_typo_correction(self, original_query: str, corrected_query: str, 
                           corrections: List[Dict[str, str]], confidence_scores: List[float]):
        """Log typo correction events"""
        event = DebugEvent(
            timestamp=datetime.now().isoformat(),
            event_type="TYPO_CORRECTION",
            query=original_query,
            details={
                "corrected_query": corrected_query,
                "corrections": corrections,
                "confidence_scores": confidence_scores,
                "changed": original_query != corrected_query
            },
            severity="INFO" if original_query == corrected_query else "WARNING"
        )
        self._log_event(event)
    
    def log_entity_extraction(self, query: str, entities: List[Dict], 
                             extraction_method: str, confidence_threshold: float):
        """Log entity extraction events"""
        event = DebugEvent(
            timestamp=datetime.now().isoformat(),
            event_type="ENTITY_EXTRACTION",
            query=query,
            details={
                "entities": entities,
                "extraction_method": extraction_method,
                "confidence_threshold": confidence_threshold,
                "entity_count": len(entities)
            },
            severity="INFO"
        )
        self._log_event(event)
    
    def log_fuzzy_match(self, original_word: str, candidate_word: str, 
                       similarity_score: float, threshold: float, 
                       context: str, decision: str):
        """Log fuzzy matching decisions"""
        event = DebugEvent(
            timestamp=datetime.now().isoformat(),
            event_type="FUZZY_MATCH",
            query=context,
            details={
                "original_word": original_word,
                "candidate_word": candidate_word,
                "similarity_score": similarity_score,
                "threshold": threshold,
                "decision": decision,
                "context": context
            },
            severity="WARNING" if decision == "CORRECT" and similarity_score < 0.9 else "INFO"
        )
        self._log_event(event)
    
    def log_validation_failure(self, validation_type: str, query: str, 
                              reason: str, details: Dict[str, Any]):
        """Log validation failures"""
        event = DebugEvent(
            timestamp=datetime.now().isoformat(),
            event_type="VALIDATION_FAILURE",
            query=query,
            details={
                "validation_type": validation_type,
                "reason": reason,
                "details": details
            },
            severity="WARNING"
        )
        self._log_event(event)
    
    def log_performance_metric(self, operation: str, duration: float, 
                              query: str, additional_metrics: Dict[str, Any] = None):
        """Log performance metrics"""
        event = DebugEvent(
            timestamp=datetime.now().isoformat(),
            event_type="PERFORMANCE",
            query=query,
            details={
                "operation": operation,
                "duration_ms": duration * 1000,
                "additional_metrics": additional_metrics or {}
            },
            severity="INFO"
        )
        self._log_event(event)
    
    def _log_event(self, event: DebugEvent):
        """Internal method to log events"""
        self.events.append(event)
        
        # Log to file
        log_message = f"[{event.event_type}] {event.query} - {json.dumps(event.details, ensure_ascii=False)}"
        
        if event.severity == "WARNING":
            self.logger.warning(log_message)
        elif event.severity == "ERROR":
            self.logger.error(log_message)
        else:
            self.logger.info(log_message)
    
    def export_events(self, filename: str = None) -> str:
        """Export all events to JSON file"""
        if filename is None:
            filename = f"debug_events_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        events_data = [asdict(event) for event in self.events]
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(events_data, f, indent=2, ensure_ascii=False)
        
        return filename
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics of logged events"""
        if not self.events:
            return {"total_events": 0}
        
        event_types = {}
        severity_counts = {}
        
        for event in self.events:
            event_types[event.event_type] = event_types.get(event.event_type, 0) + 1
            severity_counts[event.severity] = severity_counts.get(event.severity, 0) + 1
        
        return {
            "total_events": len(self.events),
            "event_types": event_types,
            "severity_counts": severity_counts,
            "time_range": {
                "start": self.events[0].timestamp,
                "end": self.events[-1].timestamp
            }
        }

# Global debug logger instance
debug_logger = DebugLogger()

def log_typo_correction(original_query: str, corrected_query: str, 
                       corrections: List[Dict[str, str]], confidence_scores: List[float]):
    """Convenience function for logging typo corrections"""
    debug_logger.log_typo_correction(original_query, corrected_query, corrections, confidence_scores)

def log_entity_extraction(query: str, entities: List[Dict], 
                         extraction_method: str, confidence_threshold: float):
    """Convenience function for logging entity extractions"""
    debug_logger.log_entity_extraction(query, entities, extraction_method, confidence_threshold)

def log_fuzzy_match(original_word: str, candidate_word: str, 
                   similarity_score: float, threshold: float, 
                   context: str, decision: str):
    """Convenience function for logging fuzzy matches"""
    debug_logger.log_fuzzy_match(original_word, candidate_word, similarity_score, threshold, context, decision)
