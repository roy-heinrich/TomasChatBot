#!/usr/bin/env python3
"""
Monitoring and Alerting System
Provides real-time monitoring of chatbot performance and alerts for issues
"""

import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import logging

@dataclass
class PerformanceMetric:
    """Performance metric data structure"""
    timestamp: str
    operation: str
    duration_ms: float
    success: bool
    error_message: Optional[str] = None
    additional_data: Dict[str, Any] = None

@dataclass
class Alert:
    """Alert data structure"""
    timestamp: str
    alert_type: str
    severity: str
    message: str
    details: Dict[str, Any]
    resolved: bool = False

class MonitoringSystem:
    """Comprehensive monitoring system for chatbot performance"""
    
    def __init__(self, alert_thresholds: Dict[str, float] = None):
        self.alert_thresholds = alert_thresholds or {
            'response_time_ms': 10000,  # 10 seconds
            'error_rate': 0.1,  # 10% error rate
            'false_positive_rate': 0.05,  # 5% false positive rate
        }
        
        # Performance metrics storage
        self.metrics: deque = deque(maxlen=10000)  # Keep last 10k metrics
        self.alerts: List[Alert] = []
        
        # Real-time counters
        self.counters = defaultdict(int)
        self.error_counts = defaultdict(int)
        self.false_positive_counts = defaultdict(int)
        
        # Time windows for analysis
        self.time_windows = {
            '1min': timedelta(minutes=1),
            '5min': timedelta(minutes=5),
            '15min': timedelta(minutes=15),
            '1hour': timedelta(hours=1),
        }
        
        # Alert handlers
        self.alert_handlers: List[Callable[[Alert], None]] = []
        
        # Setup logging
        self.logger = logging.getLogger('chatbot_monitoring')
        self.logger.setLevel(logging.INFO)
        
        # Start background monitoring
        self._start_background_monitoring()
    
    def record_metric(self, operation: str, duration_ms: float, success: bool = True, 
                     error_message: str = None, additional_data: Dict[str, Any] = None):
        """Record a performance metric"""
        metric = PerformanceMetric(
            timestamp=datetime.now().isoformat(),
            operation=operation,
            duration_ms=duration_ms,
            success=success,
            error_message=error_message,
            additional_data=additional_data or {}
        )
        
        self.metrics.append(metric)
        self.counters[f"{operation}_total"] += 1
        
        if not success:
            self.error_counts[operation] += 1
            self.counters[f"{operation}_errors"] += 1
        
        # Check for immediate alerts
        self._check_immediate_alerts(metric)
    
    def record_false_positive(self, operation: str, details: Dict[str, Any]):
        """Record a false positive detection"""
        self.false_positive_counts[operation] += 1
        self.counters[f"{operation}_false_positives"] += 1
        
        # Create alert for false positive
        alert = Alert(
            timestamp=datetime.now().isoformat(),
            alert_type="FALSE_POSITIVE",
            severity="WARNING",
            message=f"False positive detected in {operation}",
            details=details
        )
        
        self.alerts.append(alert)
        self._trigger_alert(alert)
    
    def record_entity_extraction(self, query: str, entities: List[Dict], 
                               extraction_time_ms: float, method: str):
        """Record entity extraction metrics"""
        self.record_metric(
            operation="entity_extraction",
            duration_ms=extraction_time_ms,
            success=True,
            additional_data={
                "query": query,
                "entity_count": len(entities),
                "method": method,
                "entities": entities
            }
        )
        
        # Check for potential false positives
        self._check_entity_false_positives(query, entities)
    
    def record_typo_correction(self, original_query: str, corrected_query: str, 
                             correction_time_ms: float, corrections: List[Dict]):
        """Record typo correction metrics"""
        self.record_metric(
            operation="typo_correction",
            duration_ms=correction_time_ms,
            success=True,
            additional_data={
                "original_query": original_query,
                "corrected_query": corrected_query,
                "corrections": corrections,
                "changed": original_query != corrected_query
            }
        )
        
        # Check for potential false positives
        self._check_typo_false_positives(original_query, corrected_query, corrections)
    
    def _check_entity_false_positives(self, query: str, entities: List[Dict]):
        """Check for potential false positives in entity extraction"""
        false_positive_patterns = [
            # Time-related false positives
            {"pattern": "start", "false_positive": "art", "context": "time does the class"},
            {"pattern": "end", "false_positive": "art", "context": "class"},
            {"pattern": "begin", "false_positive": "art", "context": "class"},
            {"pattern": "finish", "false_positive": "art", "context": "class"},
            
            # Subject-related false positives
            {"pattern": "match", "false_positive": "math", "context": "class"},
            {"pattern": "since", "false_positive": "science", "context": "class"},
            {"pattern": "person", "false_positive": "pe", "context": "class"},
        ]
        
        for entity in entities:
            if entity.get('entity_type') == 'academic_subject':
                entity_value = entity.get('value', '').lower()
                
                for pattern_info in false_positive_patterns:
                    if (pattern_info['false_positive'] == entity_value and 
                        pattern_info['pattern'] in query.lower() and
                        pattern_info['context'] in query.lower()):
                        
                        self.record_false_positive(
                            operation="entity_extraction",
                            details={
                                "query": query,
                                "entity": entity,
                                "pattern": pattern_info['pattern'],
                                "false_positive": pattern_info['false_positive']
                            }
                        )
                        break
    
    def _check_typo_false_positives(self, original_query: str, corrected_query: str, 
                                   corrections: List[Dict]):
        """Check for potential false positives in typo correction"""
        false_positive_patterns = [
            {"original": "start", "false_positive": "art", "context": "time does the class"},
            {"original": "end", "false_positive": "and", "context": "class"},
            {"original": "begin", "false_positive": "big", "context": "class"},
            {"original": "math", "false_positive": "match", "context": "class"},
            {"original": "science", "false_positive": "since", "context": "class"},
        ]
        
        for correction in corrections:
            original_word = correction.get('original', '').lower()
            corrected_word = correction.get('corrected', '').lower()
            
            for pattern_info in false_positive_patterns:
                if (pattern_info['original'] == original_word and 
                    pattern_info['false_positive'] == corrected_word and
                    pattern_info['context'] in original_query.lower()):
                    
                    self.record_false_positive(
                        operation="typo_correction",
                        details={
                            "original_query": original_query,
                            "corrected_query": corrected_query,
                            "correction": correction,
                            "pattern": pattern_info['original'],
                            "false_positive": pattern_info['false_positive']
                        }
                    )
                    break
    
    def _check_immediate_alerts(self, metric: PerformanceMetric):
        """Check for immediate alerts based on metrics"""
        # Response time alert
        if metric.duration_ms > self.alert_thresholds['response_time_ms']:
            alert = Alert(
                timestamp=metric.timestamp,
                alert_type="HIGH_RESPONSE_TIME",
                severity="WARNING",
                message=f"High response time: {metric.duration_ms:.2f}ms for {metric.operation}",
                details={"metric": asdict(metric)}
            )
            self.alerts.append(alert)
            self._trigger_alert(alert)
        
        # Error alert
        if not metric.success:
            alert = Alert(
                timestamp=metric.timestamp,
                alert_type="ERROR",
                severity="ERROR",
                message=f"Error in {metric.operation}: {metric.error_message}",
                details={"metric": asdict(metric)}
            )
            self.alerts.append(alert)
            self._trigger_alert(alert)
    
    def _start_background_monitoring(self):
        """Start background monitoring thread"""
        def monitor_loop():
            while True:
                try:
                    self._check_periodic_alerts()
                    time.sleep(60)  # Check every minute
                except Exception as e:
                    self.logger.error(f"Background monitoring error: {e}")
        
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
    
    def _check_periodic_alerts(self):
        """Check for periodic alerts (error rates, etc.)"""
        now = datetime.now()
        
        for window_name, window_duration in self.time_windows.items():
            cutoff_time = now - window_duration
            recent_metrics = [
                m for m in self.metrics 
                if datetime.fromisoformat(m.timestamp) > cutoff_time
            ]
            
            if recent_metrics:
                # Calculate error rate
                total_operations = len(recent_metrics)
                error_operations = len([m for m in recent_metrics if not m.success])
                error_rate = error_operations / total_operations if total_operations > 0 else 0
                
                # Check error rate threshold
                if error_rate > self.alert_thresholds['error_rate']:
                    alert = Alert(
                        timestamp=now.isoformat(),
                        alert_type="HIGH_ERROR_RATE",
                        severity="CRITICAL",
                        message=f"High error rate in {window_name}: {error_rate:.2%}",
                        details={
                            "window": window_name,
                            "error_rate": error_rate,
                            "total_operations": total_operations,
                            "error_operations": error_operations
                        }
                    )
                    self.alerts.append(alert)
                    self._trigger_alert(alert)
    
    def _trigger_alert(self, alert: Alert):
        """Trigger alert handlers"""
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                self.logger.error(f"Alert handler error: {e}")
        
        # Log alert
        self.logger.warning(f"ALERT [{alert.severity}] {alert.alert_type}: {alert.message}")
    
    def add_alert_handler(self, handler: Callable[[Alert], None]):
        """Add an alert handler"""
        self.alert_handlers.append(handler)
    
    def get_performance_summary(self, window: str = "5min") -> Dict[str, Any]:
        """Get performance summary for a time window"""
        if window not in self.time_windows:
            raise ValueError(f"Invalid window: {window}")
        
        cutoff_time = datetime.now() - self.time_windows[window]
        recent_metrics = [
            m for m in self.metrics 
            if datetime.fromisoformat(m.timestamp) > cutoff_time
        ]
        
        if not recent_metrics:
            return {"total_operations": 0}
        
        # Calculate statistics
        total_operations = len(recent_metrics)
        successful_operations = len([m for m in recent_metrics if m.success])
        error_rate = (total_operations - successful_operations) / total_operations
        
        response_times = [m.duration_ms for m in recent_metrics]
        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)
        min_response_time = min(response_times)
        
        # Operation breakdown
        operation_counts = defaultdict(int)
        for metric in recent_metrics:
            operation_counts[metric.operation] += 1
        
        return {
            "window": window,
            "total_operations": total_operations,
            "successful_operations": successful_operations,
            "error_rate": error_rate,
            "avg_response_time_ms": avg_response_time,
            "max_response_time_ms": max_response_time,
            "min_response_time_ms": min_response_time,
            "operation_breakdown": dict(operation_counts),
            "false_positives": dict(self.false_positive_counts),
            "alerts_count": len([a for a in self.alerts if not a.resolved])
        }
    
    def export_metrics(self, filename: str = None) -> str:
        """Export metrics to JSON file"""
        if filename is None:
            filename = f"chatbot_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        data = {
            "metrics": [asdict(m) for m in self.metrics],
            "alerts": [asdict(a) for a in self.alerts],
            "counters": dict(self.counters),
            "export_timestamp": datetime.now().isoformat()
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return filename

# Global monitoring instance
monitoring_system = MonitoringSystem()

def record_metric(operation: str, duration_ms: float, success: bool = True, 
                 error_message: str = None, additional_data: Dict[str, Any] = None):
    """Convenience function for recording metrics"""
    monitoring_system.record_metric(operation, duration_ms, success, error_message, additional_data)

def record_false_positive(operation: str, details: Dict[str, Any]):
    """Convenience function for recording false positives"""
    monitoring_system.record_false_positive(operation, details)
