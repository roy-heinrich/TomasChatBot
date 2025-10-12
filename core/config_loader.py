#!/usr/bin/env python3
"""
Configuration Loader
Loads and manages configuration for fuzzy matching and entity extraction
"""

import json
import os
from typing import Dict, Any, Optional
from pathlib import Path

class ConfigLoader:
    """Configuration loader with fallback defaults"""
    
    def __init__(self, config_file: str = "config/fuzzy_matching_config.json"):
        self.config_file = config_file
        self._config: Optional[Dict[str, Any]] = None
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file with fallback defaults"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
            else:
                self._config = self._get_default_config()
        except Exception as e:
            print(f"Warning: Could not load config file {self.config_file}: {e}")
            self._config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "fuzzy_matching": {
                "base_threshold": 0.8,
                "dynamic_thresholds": {
                    "short_words_length": 4,
                    "short_words_threshold": 0.9,
                    "medium_words_length": 6,
                    "medium_words_threshold": 0.85,
                    "same_length_boost": 0.05,
                    "length_difference_threshold": 3,
                    "length_difference_penalty": 0.1,
                    "min_threshold": 0.7,
                    "max_threshold": 0.95
                },
                "validation": {
                    "meaning_preserving_words": [
                        "start", "end", "begin", "finish", "time", "when", "where", "what", "how"
                    ],
                    "academic_subjects": [
                        "art", "math", "science", "english", "filipino", "music", "pe"
                    ],
                    "problematic_patterns": [
                        {
                            "original_pattern": "start",
                            "candidate_pattern": "art",
                            "context": "time does the class"
                        },
                        {
                            "original_pattern": "end",
                            "candidate_pattern": "and",
                            "context": "class"
                        }
                    ]
                },
                "vocabulary": {
                    "school_terms": [
                        "school", "activities", "available", "principal", "enrollment",
                        "student", "students", "teacher", "teachers", "education",
                        "program", "programs", "schedule", "hours", "location", "address",
                        "grade", "grades", "class", "classes", "subject", "subjects",
                        "event", "events", "celebration", "month", "year", "semester",
                        "curriculum", "academic", "extracurricular", "sports", "music",
                        "art", "science", "mathematics", "english", "filipino", "history",
                        "social", "studies", "physical", "education", "computer", "technology",
                        "support", "aide", "learning", "assistance", "help"
                    ],
                    "common_query_words": [
                        "start", "end", "begin", "finish", "time", "when", "where", "what", "how"
                    ],
                    "emergency_keywords": [
                        "heart", "attack", "stroke", "emergency", "medical", "ambulance",
                        "bleeding", "unconscious", "dying", "pain", "injury", "accident"
                    ]
                }
            },
            "entity_extraction": {
                "validation": {
                    "problematic_patterns": {
                        "art": ["start", "starts", "starting", "part", "parts", "party", "parties"],
                        "math": ["match", "matches", "matching", "path", "paths"],
                        "science": ["since", "conscience"],
                        "pe": ["person", "people", "personal"]
                    },
                    "context_validation": {
                        "time_contexts": ["time", "when", "start", "end", "begin", "finish"],
                        "class_contexts": ["class", "subject", "course", "lesson", "period"],
                        "require_class_context_for_subjects": True
                    }
                }
            },
            "monitoring": {
                "alert_thresholds": {
                    "response_time_ms": 10000,
                    "error_rate": 0.1,
                    "false_positive_rate": 0.05
                },
                "time_windows": {
                    "1min": "1 minute",
                    "5min": "5 minutes",
                    "15min": "15 minutes",
                    "1hour": "1 hour"
                },
                "max_metrics": 10000,
                "background_check_interval_seconds": 60
            }
        }
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value using dot notation (e.g., 'fuzzy_matching.base_threshold')"""
        if self._config is None:
            return default
        
        keys = key_path.split('.')
        value = self._config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_fuzzy_matching_config(self) -> Dict[str, Any]:
        """Get fuzzy matching configuration"""
        return self.get('fuzzy_matching', {})
    
    def get_entity_extraction_config(self) -> Dict[str, Any]:
        """Get entity extraction configuration"""
        return self.get('entity_extraction', {})
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """Get monitoring configuration"""
        return self.get('monitoring', {})
    
    def get_vocabulary(self) -> Dict[str, list]:
        """Get vocabulary configuration"""
        vocab_config = self.get('fuzzy_matching.vocabulary', {})
        return {
            'school_terms': vocab_config.get('school_terms', []),
            'common_query_words': vocab_config.get('common_query_words', []),
            'emergency_keywords': vocab_config.get('emergency_keywords', [])
        }
    
    def get_problematic_patterns(self) -> Dict[str, list]:
        """Get problematic patterns for entity extraction"""
        return self.get('entity_extraction.validation.problematic_patterns', {})
    
    def get_validation_patterns(self) -> list:
        """Get validation patterns for fuzzy matching"""
        return self.get('fuzzy_matching.validation.problematic_patterns', [])
    
    def reload_config(self):
        """Reload configuration from file"""
        self._load_config()
    
    def save_config(self, config: Dict[str, Any], filename: str = None):
        """Save configuration to file"""
        if filename is None:
            filename = self.config_file
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        self._config = config

# Global configuration instance
config_loader = ConfigLoader()

def get_config(key_path: str, default: Any = None) -> Any:
    """Convenience function to get configuration"""
    return config_loader.get(key_path, default)

def get_fuzzy_matching_config() -> Dict[str, Any]:
    """Convenience function to get fuzzy matching configuration"""
    return config_loader.get_fuzzy_matching_config()

def get_entity_extraction_config() -> Dict[str, Any]:
    """Convenience function to get entity extraction configuration"""
    return config_loader.get_entity_extraction_config()
