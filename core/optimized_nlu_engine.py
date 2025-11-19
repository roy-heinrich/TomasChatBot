"""
Optimized NLU Engine with Caching
High-performance Natural Language Understanding with Redis caching
"""
import logging
import json
import hashlib
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from nlu_engine import NLUEngine, NLUResult

logger = logging.getLogger(__name__)

class OptimizedNLUEngine(NLUEngine):
    """NLU Engine with Redis caching and performance optimizations"""
    
    def __init__(self, redis_client=None):
        super().__init__()
        self.redis = redis_client
        self.cache_ttl = 1800  # 30 minutes cache for NLU results
        self.redis_available = False
        
        # Initialize Redis connection
        self._initialize_redis()
        
        # Pre-compile regex patterns for better performance
        self._compile_patterns()
    
    def _initialize_redis(self):
        """Initialize Redis connection for NLU caching"""
        if not self.redis:
            try:
                import redis
                import os
                
                if os.environ.get('REDIS_URL'):
                    self.redis = redis.from_url(os.environ.get('REDIS_URL'), decode_responses=True)
                    self.redis.ping()
                    self.redis_available = True
                    logger.info("✅ NLU Redis cache initialized")
                else:
                    logger.info("⚠️ No Redis URL - NLU caching disabled")
            except Exception as e:
                logger.warning(f"⚠️ NLU Redis not available: {e}")
                self.redis_available = False
    
    def _compile_patterns(self):
        """Pre-compile regex patterns for better performance"""
        import re
        
        # Pre-compile commonly used patterns
        self.compiled_patterns = {
            # More specific emergency patterns - only direct medical emergencies (removed standalone "emergency")
            'emergency_keywords': re.compile(r'\b(?:heart attack|stroke|bleeding|unconscious|dying|ambulance|911|urgent medical|medical emergency|can\'t breathe|not breathing|choking|i\'m having|i am having|need urgent|critical condition)\b', re.IGNORECASE),
            # Safety inquiry patterns - should NOT trigger emergency (comprehensive matching)
            'safety_inquiry_patterns': re.compile(r'\b(?:fire drill|earthquake drill|safety drill|emergency drill|evacuation drill|drill|safety|preparedness|protocol|procedure|emergency procedures|safety procedures|emergency drills|fire drills|earthquake drills|safety drills|evacuation drills|conduct.*drill|practice.*drill|have.*drill)\b', re.IGNORECASE),
            'greeting_patterns': re.compile(r'\b(?:h+i+|h+e+l+l+o+|h+e+y+|good morning|good afternoon|good noon|good evening|good day|good night|greetings|kumusta|kamusta|magandang umaga|magandang hapon|magandang gabi|maayong aga|maayong hapon|maayong gab-i|magandang araw|maayong adlaw|maayong gabii|maayong buntag|hiya|howdy|wassup|what\'s up|yo|hey there|hello there|hi there|morning|afternoon|noon|evening|night)\b', re.IGNORECASE),
            'gratitude_patterns': re.compile(r'\b(?:thank you|thanks|thank u|thx|ty|tysm|salamat|maraming salamat|damo nga salamat|salamat gid)\b', re.IGNORECASE),
            'question_patterns': re.compile(r'\b(?:what|who|when|where|why|how|which|can|could|would|should|is|are|do|does|did)\b', re.IGNORECASE),
            'name_patterns': re.compile(r'\b(?:i\'m|im|i am|my name is|call me)\s+(\w+)\b', re.IGNORECASE),
            'grade_patterns': re.compile(r'\b(?:grade|g)\s*(\d+)\b', re.IGNORECASE),
            'contact_patterns': re.compile(r'\b(?:contact|speak|talk|call|message|admin)\b', re.IGNORECASE)
        }
    
    def _create_nlu_cache_key(self, user_input: str, context: Dict = None) -> str:
        """Create cache key for NLU results"""
        # Normalize input for consistent caching
        normalized_input = user_input.lower().strip()
        
        # Include context if provided (skip datetime objects)
        context_str = ""
        if context:
            # Clean context of datetime objects before serializing
            clean_context = self._clean_context_for_caching(context)
            context_str = json.dumps(clean_context, sort_keys=True)
        
        # Create hash
        key_string = f"{normalized_input}:{context_str}"
        query_hash = hashlib.md5(key_string.encode()).hexdigest()
        return f"nlu:{query_hash}"
    
    def _clean_context_for_caching(self, context: Dict) -> Dict:
        """Clean context by converting datetime objects to strings"""
        clean_context = {}
        for key, value in context.items():
            if isinstance(value, datetime):
                clean_context[key] = value.isoformat()
            elif isinstance(value, dict):
                clean_context[key] = self._clean_context_for_caching(value)
            elif isinstance(value, list):
                clean_context[key] = [
                    item.isoformat() if isinstance(item, datetime) else item
                    for item in value
                ]
            else:
                clean_context[key] = value
        return clean_context
    
    def _get_nlu_from_cache(self, cache_key: str) -> Optional[NLUResult]:
        """Get NLU result from cache"""
        if not self.redis_available:
            return None
        
        try:
            cached_data = self.redis.get(cache_key)
            if cached_data:
                logger.info(f"🚀 NLU Cache HIT for: {cache_key[:20]}...")
                data = json.loads(cached_data)
                # Reconstruct NLUResult from cached data
                from nlu_engine import Intent
                from entity_extractor import ExtractedEntity
                
                intent = Intent(data['intent']) if data['intent'] else None
                entities = [ExtractedEntity(entity_type=e['type'], value=e['value'], confidence=e.get('confidence', 0.8)) for e in data['entities']] if data['entities'] else []
                
                result = NLUResult(
                    intent=intent,
                    confidence=data['confidence'],
                    entities=entities,
                    is_multi_question=data.get('is_multi_question', False),
                    questions=data.get('questions', None)
                )
                return result
        except Exception as e:
            logger.warning(f"NLU cache get error: {e}")
        
        return None
    
    def _store_nlu_in_cache(self, cache_key: str, result: NLUResult) -> bool:
        """Store NLU result in cache"""
        if not self.redis_available:
            return False
        
        try:
            # Convert NLUResult to dict for caching
            data = {
                'intent': result.intent.value if result.intent else None,
                'confidence': result.confidence,
                'entities': [{'type': e.type, 'value': e.value} for e in result.entities] if result.entities else [],
                'is_emergency': getattr(result, 'is_emergency', False),
                'is_multi_question': result.is_multi_question,
                'questions': result.questions,
                'language': getattr(result, 'language', 'en')
            }
            
            self.redis.setex(cache_key, self.cache_ttl, json.dumps(data))
            logger.info(f"💾 NLU Cached result for: {cache_key[:20]}...")
            return True
        except Exception as e:
            logger.warning(f"NLU cache store error: {e}")
            return False
    
    async def analyze_intent(self, user_input: str, context: Dict = None) -> NLUResult:
        """Optimized intent analysis with caching"""
        # Create cache key
        cache_key = self._create_nlu_cache_key(user_input, context)
        
        # Try to get from cache first
        cached_result = self._get_nlu_from_cache(cache_key)
        if cached_result:
            return cached_result
        
        # Cache miss - perform analysis
        logger.info(f"💾 NLU Cache MISS for: {user_input[:50]}...")
        
        # Use optimized analysis
        result = await self._analyze_intent_optimized(user_input, context)
        
        # Store in cache
        self._store_nlu_in_cache(cache_key, result)
        
        # 🚨 AUTOMATIC: Invalidate related NLU caches for grade queries
        if 'grade' in user_input.lower():
            self._invalidate_grade_nlu_cache(user_input)
        
        return result
    
    def _invalidate_grade_nlu_cache(self, user_input: str):
        """Invalidate NLU cache entries for grade-related queries"""
        if not self.redis_available:
            return
        
        try:
            import re
            # Extract grade from input
            grade_match = re.search(r'grade\s*(\d+)', user_input.lower())
            if grade_match:
                grade_num = grade_match.group(1)
                
                # Get all NLU cache keys
                keys = self.redis.keys('nlu:*')
                grade_keys = [key for key in keys if f'grade {grade_num}' in key.lower()]
                
                if grade_keys:
                    self.redis.delete(*grade_keys)
                    logger.info(f"🗑️ Invalidated {len(grade_keys)} NLU cache entries for Grade {grade_num}")
        except Exception as e:
            logger.warning(f"NLU cache invalidation failed: {e}")
    
    async def _analyze_intent_optimized(self, user_input: str, context: Dict = None) -> NLUResult:
        """Optimized intent analysis with pre-compiled patterns"""
        # Use pre-compiled patterns for faster matching
        user_lower = user_input.lower()
        
        # PRIORITY: Check for safety inquiries FIRST (before emergency detection)
        if self.compiled_patterns['safety_inquiry_patterns'].search(user_lower):
            from nlu_engine import Intent
            return NLUResult(
                intent=Intent.SAFETY_INQUIRY,  # Safety inquiries are their own category
                confidence=0.9,
                entities=[]
            )
        
        # Quick emergency check using compiled pattern (only after safety check)
        if self.compiled_patterns['emergency_keywords'].search(user_lower):
            return await self._quick_emergency_detection(user_input, context)
        
        # Quick greeting check
        if self.compiled_patterns['greeting_patterns'].search(user_lower):
            return await self._quick_greeting_detection(user_input, context)
        
        # Quick gratitude check
        if self.compiled_patterns['gratitude_patterns'].search(user_lower):
            from nlu_engine import Intent
            return NLUResult(
                intent=Intent.APPRECIATION,
                confidence=0.9,
                entities=[]
            )
        
        # Quick contact escalation check
        if self.compiled_patterns['contact_patterns'].search(user_lower):
            return await self._quick_contact_detection(user_input, context)
        
        # Fall back to full analysis for complex cases
        return await super()._analyze_single_intent(user_input, context)
    
    async def _quick_emergency_detection(self, user_input: str, context: Dict = None) -> NLUResult:
        """Fast emergency detection using compiled patterns"""
        from nlu_engine import Intent
        
        user_lower = user_input.lower()
        
        # CRITICAL: Double-check for safety inquiries (should not be emergencies)
        if self.compiled_patterns['safety_inquiry_patterns'].search(user_lower):
            return NLUResult(
                intent=Intent.SAFETY_INQUIRY,  # Safety inquiries are their own category
                confidence=0.9,
                entities=[]
            )
        
        # Check for figurative expressions first
        figurative_expressions = [
            "dying to know", "dying laughing", "gonna die laughing", "dying of laughter",
            "dying of", "dying from", "dying with", "almost died", "nearly died"
        ]
        
        is_figurative = False
        for expr in figurative_expressions:
            if expr in user_lower:
                # logger.info(f"🎭 OptimizedNLU: Figurative 'dying' expression detected: '{expr}' in '{user_input}'")
                is_figurative = True
                break
        
        # Also check for "dying" + context words
        if "dying" in user_lower and not is_figurative:
            figurative_contexts = ["laughing", "laugh", "know", "curiosity", "funny", "joke", "amused", "hilarious"]
            for context in figurative_contexts:
                if context in user_lower:
                    # logger.info(f"🎭 OptimizedNLU: Figurative 'dying' with context '{context}' detected in: '{user_input}'")
                    is_figurative = True
                    break
        
        if is_figurative:
            # Skip emergency detection for figurative expressions
            return NLUResult(
                intent=Intent.UNKNOWN,
                confidence=0.3,
                entities=[]
            )
        
        # Use compiled pattern for faster matching
        emergency_match = self.compiled_patterns['emergency_keywords'].search(user_lower)
        
        if emergency_match:
            return NLUResult(
                intent=Intent.EMERGENCY,
                confidence=0.95,
                entities=[]
            )
        
        # Fall back to full analysis
        return await super()._analyze_single_intent(user_input, context)
    
    async def _quick_greeting_detection(self, user_input: str, context: Dict = None) -> NLUResult:
        """Fast greeting detection using compiled patterns"""
        from nlu_engine import Intent
        import re
        
        user_lower = user_input.lower()
        
        # Check if this is a greeting + question combination
        if self._is_greeting_with_question(user_lower):
            # Don't return greeting intent, let other intents be detected
            # Fall back to full analysis for complex cases
            return await super()._analyze_single_intent(user_input, context)
        
        # 🚨 CRITICAL FIX: Check for name introduction FIRST before elongated greeting check
        # This ensures "hello, my name is Heinz" is recognized as greeting_with_name, not greeting_excited
        name_match = self.compiled_patterns['name_patterns'].search(user_lower)
        
        if name_match:
            from entity_extractor import ExtractedEntity
            return NLUResult(
                intent=Intent.GREETING_WITH_NAME,
                confidence=0.90,
                entities=[ExtractedEntity(entity_type="name", value=name_match.group(1), confidence=0.9)]
            )
        
        # Check for elongated greetings (hi, hii, hiii, hiiii, etc.)
        # Only check this AFTER we've ruled out name introductions
        elongated_greeting_pattern = r'\b(h+i+|h+e+l+l+o+|h+e+y+)\b'
        if re.search(elongated_greeting_pattern, user_lower):
            return NLUResult(
                intent=Intent.GREETING_EXCITED,
                confidence=0.9,
                entities=[]
            )
        
        return NLUResult(
            intent=Intent.GREETING_SIMPLE,
            confidence=0.85,
            entities=[]
        )
    
    async def _quick_contact_detection(self, user_input: str, context: Dict = None) -> NLUResult:
        """Fast contact escalation detection"""
        from nlu_engine import Intent
        
        return NLUResult(
            intent=Intent.CONTACT_ESCALATION,
            confidence=0.80,
            entities=[]
        )
    
    def clear_nlu_cache(self, pattern: str = None) -> bool:
        """Clear NLU cache entries"""
        if not self.redis_available:
            return False
        
        try:
            if pattern:
                keys = self.redis.keys(f"nlu:{pattern}")
                if keys:
                    self.redis.delete(*keys)
                    logger.info(f"🗑️ Cleared {len(keys)} NLU cache entries")
            else:
                keys = self.redis.keys("nlu:*")
                if keys:
                    self.redis.delete(*keys)
                    logger.info(f"🗑️ Cleared all NLU cache entries")
            return True
        except Exception as e:
            logger.error(f"NLU cache clear error: {e}")
            return False
    
    def get_nlu_cache_stats(self) -> Dict[str, Any]:
        """Get NLU cache statistics"""
        if not self.redis_available:
            return {"nlu_cache_available": False}
        
        try:
            keys = self.redis.keys("nlu:*")
            return {
                "nlu_cache_available": True,
                "cached_intents": len(keys),
                "cache_ttl": self.cache_ttl
            }
        except Exception as e:
            return {"nlu_cache_available": False, "error": str(e)}
