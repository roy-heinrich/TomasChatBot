# TOMAS Chatbot Processing Flowchart

## Main Processing Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              TOMAS CHATBOT FLOWCHART                          │
│                                                                                 │
│  ┌─────────────┐                                                               │
│  │   START     │                                                               │
│  │ User Input  │                                                               │
│  └─────┬───────┘                                                               │
│        │                                                                       │
│        ▼                                                                       │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                    ENHANCED SECURITY VALIDATION                        │   │
│  │  • SQL Injection Check (59+ patterns)                                 │   │
│  │  • XSS Prevention                                                     │   │
│  │  • Command Injection Detection                                        │   │
│  │  • Path Traversal Protection                                          │   │
│  │  • Null Byte Detection                                                │   │
│  │  • Malicious URL Check                                                │   │
│  └─────────────────┬───────────────────────────────────────────────────────┘   │
│                    │                                                           │
│                    ▼                                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                        INPUT PREPROCESSING                             │   │
│  │  • Typo Correction                                                     │   │
│  │  • Text Normalization                                                  │   │
│  │  • Character Encoding Handling                                         │   │
│  │  • Gibberish Detection                                                 │   │
│  └─────────────────┬───────────────────────────────────────────────────────┘   │
│                    │                                                           │
│                    ▼                                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                      LANGUAGE DETECTION                                │   │
│  │  • Multi-language Support (English, Tagalog, Aklanon)                 │   │
│  │  • Mixed-language Detection                                            │   │
│  │  • Confidence Scoring                                                  │   │
│  │  • Redis Cache Check (83% hit rate)                                   │   │
│  └─────────────────┬───────────────────────────────────────────────────────┘   │
│                    │                                                           │
│                    ▼                                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                    NLU ANALYSIS (OPTIMIZED)                            │   │
│  │  • Redis Cache Check (TTL: 30 minutes)                                │   │
│  │  • Intent Classification (40+ intents)                                │   │
│  │  • Confidence Scoring                                                  │   │
│  │  • Multi-question Detection (2-5 questions)                           │   │
│  │  • Emergency Detection with Context Analysis                          │   │
│  └─────────────────┬───────────────────────────────────────────────────────┘   │
│                    │                                                           │
│                    ▼                                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                    ENTITY EXTRACTION                                   │   │
│  │  • Named Entity Recognition                                            │   │
│  │  • Person Names, Grades, Subjects                                      │   │
│  │  • Relationship Detection                                              │   │
│  │  • Confidence Scoring                                                  │   │
│  └─────────────────┬───────────────────────────────────────────────────────┘   │
│                    │                                                           │
│                    ▼                                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                    EMERGENCY CHECK                                     │   │
│  │  • Medical Emergency Detection                                         │   │
│  │  • Safety Emergency Detection                                          │   │
│  │  • Context-aware Analysis                                              │   │
│  │  • Humor/Sarcasm Detection                                             │   │
│  └─────────────────┬───────────────────────────────────────────────────────┘   │
│                    │                                                           │
│                    ▼                                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                    DATABASE SEARCH                                     │   │
│  │  • Redis Cache Check (TTL: 1 hour)                                    │   │
│  │  • ImprovedScorer Algorithm                                            │   │
│  │  • Semantic Similarity Matching                                        │   │
│  │  • Context-specific Boosting                                           │   │
│  │  • Intent-based Refinement                                             │   │
│  └─────────────────┬───────────────────────────────────────────────────────┘   │
│                    │                                                           │
│                    ▼                                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                    CONTEXT ANALYSIS                                    │   │
│  │  • Conversation History Analysis                                       │   │
│  │  • Topic Flow Tracking                                                 │   │
│  │  • User Profile Integration                                            │   │
│  │  • Emotional State Detection                                           │   │
│  └─────────────────┬───────────────────────────────────────────────────────┘   │
│                    │                                                           │
│                    ▼                                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                    MEMORY UPDATE                                       │   │
│  │  • Conversation History Storage                                        │   │
│  │  • User Profile Updates                                                │   │
│  │  • Context Preservation                                                │   │
│  │  • Persistent Storage                                                  │   │
│  └─────────────────┬───────────────────────────────────────────────────────┘   │
│                    │                                                           │
│                    ▼                                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                    RESPONSE GENERATION                                 │   │
│  │  • Multi-provider AI (Groq, Cohere, HuggingFace, Local)               │   │
│  │  • Intelligent Fallback System                                         │   │
│  │  • Rate Limit Management                                               │   │
│  │  • Token Efficiency Optimization                                       │   │
│  └─────────────────┬───────────────────────────────────────────────────────┘   │
│                    │                                                           │
│                    ▼                                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                    RESPONSE PERSONALIZATION                            │   │
│  │  • User Profile-based Adaptation                                       │   │
│  │  • Emotional Intelligence Integration                                   │   │
│  │  • Tone and Formality Adjustment                                        │   │
│  │  • Cultural Context Awareness                                          │   │
│  └─────────────────┬───────────────────────────────────────────────────────┘   │
│                    │                                                           │
│                    ▼                                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                    TRANSLATION (if needed)                             │   │
│  │  • Context-aware Translation                                           │   │
│  │  • Grammar Preservation                                                │   │
│  │  • Cultural Context Maintenance                                        │   │
│  │  • Redis Cache Check                                                   │   │
│  └─────────────────┬───────────────────────────────────────────────────────┘   │
│                    │                                                           │
│                    ▼                                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                MULTI-QUESTION PROCESSING                               │   │
│  │  • Question Separation (2-5 questions)                                │   │
│  │  • Structured Response Generation                                      │   │
│  │  • Context Preservation across Questions                               │   │
│  │  • Response Splitting and Formatting                                   │   │
│  └─────────────────┬───────────────────────────────────────────────────────┘   │
│                    │                                                           │
│                    ▼                                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                    CACHE STORAGE                                       │   │
│  │  • Store NLU Results in Redis                                          │   │
│  │  • Store Database Results in Redis                                     │   │
│  │  • Store Translation Results in Redis                                  │   │
│  │  • Update Cache Statistics                                             │   │
│  └─────────────────┬───────────────────────────────────────────────────────┘   │
│                    │                                                           │
│                    ▼                                                           │
│  ┌─────────────┐                                                               │
│  │    END      │                                                               │
│  │ User Output │                                                               │
│  └─────────────┘                                                               │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Emergency Detection Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            EMERGENCY DETECTION FLOW                            │
│                                                                                 │
│  ┌─────────────┐                                                               │
│  │ Emergency   │                                                               │
│  │ Detected?   │                                                               │
│  └─────┬───────┘                                                               │
│        │                                                                       │
│        ▼                                                                       │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                    EMERGENCY VALIDATION                                │   │
│  │  • Context Analysis (prevent false positives)                         │   │
│  │  • Humor/Sarcasm Detection                                            │   │
│  │  • Standalone Medical Term Validation                                 │   │
│  │  • Safety Protocol Assessment                                         │   │
│  └─────────────────┬───────────────────────────────────────────────────────┘   │
│                    │                                                           │
│                    ▼                                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                    EMERGENCY RESPONSE                                  │   │
│  │  • Immediate 911 Protocol Activation                                   │   │
│  │  • Emergency Contact Information                                       │   │
│  │  • Safety Instructions                                                 │   │
│  │  • Crisis Support Resources                                            │   │
│  └─────────────────┬───────────────────────────────────────────────────────┘   │
│                    │                                                           │
│                    ▼                                                           │
│  ┌─────────────┐                                                               │
│  │ Emergency   │                                                               │
│  │ Output      │                                                               │
│  └─────────────┘                                                               │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Cache Management Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            CACHE MANAGEMENT FLOW                               │
│                                                                                 │
│  ┌─────────────┐                                                               │
│  │ Cache       │                                                               │
│  │ Request     │                                                               │
│  └─────┬───────┘                                                               │
│        │                                                                       │
│        ▼                                                                       │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                    REDIS AVAILABLE?                                    │   │
│  │  • Check Redis Connection                                              │   │
│  │  • Test Redis Ping                                                     │   │
│  │  • Validate Redis Response                                             │   │
│  └─────────────────┬───────────────────────────────────────────────────────┘   │
│                    │                                                           │
│                    ▼                                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                    CACHE HIT/MISS CHECK                                │   │
│  │  • Generate Cache Key (query + context hash)                          │   │
│  │  • Check TTL Expiration                                               │   │
│  │  • Validate Cache Entry                                               │   │
│  └─────────────────┬───────────────────────────────────────────────────────┘   │
│                    │                                                           │
│                    ▼                                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                    CACHE OPERATION                                     │   │
│  │  • HIT: Return cached result                                           │   │
│  │  • MISS: Execute operation, store in cache                            │   │
│  │  • FALLBACK: Use in-memory cache if Redis unavailable                 │   │
│  │  • UPDATE: Refresh cache statistics                                    │   │
│  └─────────────────┬───────────────────────────────────────────────────────┘   │
│                    │                                                           │
│                    ▼                                                           │
│  ┌─────────────┐                                                               │
│  │ Cache       │                                                               │
│  │ Result      │                                                               │
│  └─────────────┘                                                               │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## AI Provider Fallback Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          AI PROVIDER FALLBACK FLOW                             │
│                                                                                 │
│  ┌─────────────┐                                                               │
│  │ AI Request  │                                                               │
│  │ Generated   │                                                               │
│  └─────┬───────┘                                                               │
│        │                                                                       │
│        ▼                                                                       │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                    PRIMARY PROVIDER (GROQ)                             │   │
│  │  • Model: llama-3.1-8b-instant                                        │   │
│  │  • Rate Limit: 30 requests/minute                                     │   │
│  │  • Token Efficiency: Optimized                                        │   │
│  └─────────────────┬───────────────────────────────────────────────────────┘   │
│                    │                                                           │
│                    ▼                                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                    SUCCESS?                                            │   │
│  │  • Check Response Quality                                              │   │
│  │  • Validate Rate Limits                                               │   │
│  │  • Monitor Provider Health                                            │   │
│  └─────────────────┬───────────────────────────────────────────────────────┘   │
│                    │                                                           │
│                    ▼                                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                    SECONDARY PROVIDER (COHERE)                         │   │
│  │  • Model: command-a-03-2025                                           │   │
│  │  • Rate Limit: 1000 requests/minute                                   │   │
│  │  • Fallback: HuggingFace                                              │   │
│  └─────────────────┬───────────────────────────────────────────────────────┘   │
│                    │                                                           │
│                    ▼                                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                    SUCCESS?                                            │   │
│  │  • Check Response Quality                                              │   │
│  │  • Validate Rate Limits                                               │   │
│  │  • Monitor Provider Health                                            │   │
│  └─────────────────┬───────────────────────────────────────────────────────┘   │
│                    │                                                           │
│                    ▼                                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                    TERTIARY PROVIDER (HUGGINGFACE)                     │   │
│  │  • Model: deepseek-ai/DeepSeek-V3-0324                                │   │
│  │  • Rate Limit: 1000 requests/day                                      │   │
│  │  • Fallback: Local AI                                                 │   │
│  └─────────────────┬───────────────────────────────────────────────────────┘   │
│                    │                                                           │
│                    ▼                                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                    SUCCESS?                                            │   │
│  │  • Check Response Quality                                              │   │
│  │  • Validate Rate Limits                                               │   │
│  │  • Monitor Provider Health                                            │   │
│  └─────────────────┬───────────────────────────────────────────────────────┘   │
│                    │                                                           │
│                    ▼                                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                    FINAL FALLBACK (LOCAL AI)                           │   │
│  │  • Model: deepseek-ai/DeepSeek-V3-0324                                │   │
│  │  • Rate Limit: Unlimited (free)                                       │   │
│  │  • Fallback: Context-aware keyword responses                          │   │
│  └─────────────────┬───────────────────────────────────────────────────────┘   │
│                    │                                                           │
│                    ▼                                                           │
│  ┌─────────────┐                                                               │
│  │ AI Response │                                                               │
│  │ Generated   │                                                               │
│  └─────────────┘                                                               │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Multi-Question Processing Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        MULTI-QUESTION PROCESSING FLOW                          │
│                                                                                 │
│  ┌─────────────┐                                                               │
│  │ User Input  │                                                               │
│  │ Received    │                                                               │
│  └─────┬───────┘                                                               │
│        │                                                                       │
│        ▼                                                                       │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                    QUESTION DETECTION                                  │   │
│  │  • NLP Pattern Matching                                                │   │
│  │  • Question Mark Detection                                             │   │
│  │  • Interrogative Word Analysis                                         │   │
│  │  • Context-aware Question Separation                                   │   │
│  └─────────────────┬───────────────────────────────────────────────────────┘   │
│                    │                                                           │
│                    ▼                                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                    MULTIPLE QUESTIONS?                                 │   │
│  │  • Count Questions (2-5 supported)                                    │   │
│  │  • Validate Question Structure                                         │   │
│  │  • Check Question Relevance                                            │   │
│  └─────────────────┬───────────────────────────────────────────────────────┘   │
│                    │                                                           │
│                    ▼                                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                    QUESTION PROCESSING                                 │   │
│  │  • Process Each Question Individually                                  │   │
│  │  • Maintain Context Across Questions                                   │   │
│  │  • Generate Individual Responses                                       │   │
│  │  • Preserve Question Order                                             │   │
│  └─────────────────┬───────────────────────────────────────────────────────┘   │
│                    │                                                           │
│                    ▼                                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                    RESPONSE AGGREGATION                                │   │
│  │  • Combine Individual Responses                                        │   │
│  │  • Format Structured Output                                            │   │
│  │  • Add Question Labels/Numbering                                       │   │
│  │  • Maintain Coherent Flow                                              │   │
│  └─────────────────┬───────────────────────────────────────────────────────┘   │
│                    │                                                           │
│                    ▼                                                           │
│  ┌─────────────┐                                                               │
│  │ Structured  │                                                               │
│  │ Response    │                                                               │
│  │ Output      │                                                               │
│  └─────────────┘                                                               │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Key Features Highlighted in Flowcharts

### **Security & Validation**
- Enhanced security validation with 10+ threat types
- SQL injection protection (59+ patterns)
- XSS, command injection, and path traversal prevention
- Emergency detection with context analysis

### **Performance & Caching**
- Redis caching at multiple stages (NLU, Database, Translation)
- Intelligent cache hit/miss handling
- Fallback to in-memory cache when Redis unavailable
- TTL-based cache expiration

### **AI & Intelligence**
- Multi-provider AI with intelligent fallback
- Rate limit management and provider health monitoring
- Emotional intelligence and response personalization
- Context-aware translation and cultural adaptation

### **Processing Capabilities**
- Multi-question detection and processing (2-5 questions)
- Entity extraction and relationship detection
- Conversation memory and context preservation
- Emergency detection and crisis response

### **Error Handling & Fallbacks**
- Graceful degradation when providers fail
- Multiple fallback layers (Redis → In-Memory → Direct)
- Context-aware keyword responses as final fallback
- Comprehensive error recovery mechanisms

These flowcharts provide a comprehensive visual representation of how the TOMAS chatbot processes user input, handles emergencies, manages caching, and ensures reliable response generation through multiple fallback systems.
