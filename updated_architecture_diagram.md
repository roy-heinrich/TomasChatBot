# TOMAS Chatbot Architecture Diagram (Updated)

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                TOMAS CHATBOT SYSTEM                            │
│                         Advanced Multilingual AI Architecture                  │
│                              Production-Ready Deployment                       │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Core Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                    USER INTERFACE                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                │
│  │   Web Widget    │  │   Mobile App    │  │   Admin Panel   │                │
│  │   (PHP/HTML)    │  │   (React)       │  │   (PHP)         │                │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘                │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              FASTAPI APPLICATION                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                           app.py                                        │    │
│  │  • CORS Middleware (Production-ready)                                   │    │
│  │  • SQL Injection Protection Middleware                                 │    │
│  │  • Request Validation & Sanitization                                   │    │
│  │  • Health Monitoring & Metrics                                         │    │
│  │  • Admin Endpoints (/admin/logs, /admin/metrics)                       │    │
│  │  • Session Management (/clear-context)                                 │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              CHATBOT CORE ENGINE                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                      chatbot_refactored.py                             │    │
│  │  • Main ChatBot Class (Production Optimized)                           │    │
│  │  • Multi-Question Detection & Processing                               │    │
│  │  • Emergency Detection with Context Analysis                           │    │
│  │  • Typo Correction & Normalization                                    │    │
│  │  • Conversation Orchestration                                         │    │
│  │  • Response Generation with Fallback                                  │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              CORE MODULES                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │ Language    │  │    NLU      │  │   Entity    │  │  Database   │          │
│  │ Detector    │  │   Engine    │  │ Extractor   │  │   Search    │          │
│  │ (3 langs)   │  │ (40+ intents)│  │(Advanced)   │  │ (Scoring)   │          │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │ Response    │  │  Keyword    │  │  Memory     │  │  Context    │          │
│  │ Generator   │  │   Matcher   │  │  System     │  │   Aware     │          │
│  │ (Multi-AI)  │  │ (Fallback)  │  │(Persistent) │  │ Translation │          │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │ Emotional   │  │  Personal   │  │  Conversation│  │  Rate Limit │          │
│  │ Intelligence│  │  Response   │  │  Analyzer   │  │   Monitor   │          │
│  │ (Sentiment) │  │ Personalizer│  │ (Context)   │  │ (Security)  │          │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘          │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              AI PROVIDERS LAYER                                │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                        MultiProviderAI                                  │    │
│  │  • Intelligent Fallback System                                         │    │
│  │  • Rate Limit Management                                               │    │
│  │  • Provider Health Monitoring                                          │    │
│  │  • Token Efficiency Optimization                                       │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │   Groq      │  │   Cohere    │  │ HuggingFace │  │   Local AI   │          │
│  │  Provider   │  │   Provider   │  │  Provider   │  │   Provider   │          │
│  │ (Primary)    │  │ (Secondary)  │  │ (Tertiary)  │  │ (Fallback)   │          │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘          │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              DATA LAYER                                        │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                           SUPABASE                                      │    │
│  │  • chatbot_prompts table (School Information)                           │    │
│  │  • Real-time data access                                               │    │
│  │  • Advanced search with ImprovedScorer                                 │    │
│  │  • Semantic similarity matching                                        │    │
│  │  • Context-aware result ranking                                        │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## AI Provider Configuration (Updated)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              AI PROVIDER HIERARCHY                             │
│                                                                                 │
│  1. GROQ PROVIDER (Primary)                                                     │
│     • Model: llama-3.1-8b-instant                                             │
│     • API Key: GROQ_API_KEY                                                    │
│     • Rate Limits: 30 requests/minute                                          │
│     • Fallback: CohereProvider                                                 │
│     • Token Efficiency: Optimized prompts                                      │
│                                                                                 │
│  2. COHERE PROVIDER (Secondary)                                                 │
│     • Model: command-a-03-2025                                                 │
│     • API Key: COHERE_API_KEY                                                  │
│     • Rate Limits: 1000 requests/minute                                        │
│     • Fallback: HuggingFaceProvider                                            │
│                                                                                 │
│  3. HUGGING FACE PROVIDER (Tertiary)                                           │
│     • Model: deepseek-ai/DeepSeek-V3-0324                                      │
│     • API Key: HUGGINGFACE_API_KEY (optional)                                  │
│     │ Rate Limits: 1000 requests/day                                           │
│     • Fallback: LocalAIProvider                                               │
│                                                                                 │
│  4. LOCAL AI PROVIDER (Final Fallback)                                         │
│     • Model: deepseek-ai/DeepSeek-V3-0324                                      │
│     • API Key: HUGGINGFACE_API_KEY (optional)                                  │
│     • Rate Limits: Unlimited (free)                                            │
│     • Fallback: Context-aware keyword responses                                │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Core Features & Capabilities (Updated)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              CHATBOT FEATURES                                  │
│                                                                                 │
│  🌍 MULTILINGUAL SUPPORT                                                       │
│  • English (Primary)                                                           │
│  • Tagalog (Secondary)                                                         │
│  • Aklanon (Tertiary)                                                          │
│  • Mixed-language detection with confidence scoring                           │
│  • Context-aware translation with grammar preservation                       │
│  • Language-specific response formatting                                       │
│                                                                                 │
│  🧠 INTELLIGENT CONVERSATION                                                   │
│  • Natural Language Understanding (NLU) with 40+ intents                      │
│  • Advanced Entity Extraction (Names, Grades, Subjects, Relationships)         │
│  • Conversation Memory with persistent user profiles                          │
│  • Context Awareness across multi-turn conversations                          │
│  • Multi-question detection and structured processing                         │
│  • Emergency detection with context analysis                                  │
│                                                                                 │
│  🎯 SCHOOL-SPECIFIC FEATURES                                                   │
│  • Enrollment Information (Documents, Deadlines, Process)                     │
│  • Staff Directory with role-based queries                                    │
│  • Schedule Inquiries (Hours, Classes, Events)                                │
│  • Location Services (Address, Directions, Facilities)                      │
│  • Financial Information (Tuition, Fees, Scholarships)                       │
│  • Facilities Information (CR, Library, Cafeteria, etc.)                     │
│  • Grade Level Validation and Information                                    │
│                                                                                 │
│  🚨 SAFETY & SECURITY                                                          │
│  • Medical Emergency Detection with 911 protocols                             │
│  • SQL Injection Protection Middleware                                        │
│  • Rate Limiting and Abuse Prevention                                         │
│  • Input Validation and Sanitization                                          │
│  • Gibberish Detection with NLP patterns                                       │
│  • Context-aware emergency analysis                                           │
│                                                                                 │
│  💡 ADVANCED AI FEATURES                                                       │
│  • Emotional Intelligence with sentiment analysis                              │
│  • Response Personalization based on user profiles                            │
│  • Conversation Analysis with topic flow tracking                            │
│  • Multi-provider AI with intelligent fallback                                │
│  • Context-aware responses with memory integration                            │
│  • Typo correction and text normalization                                     │
│  • Semantic similarity matching for database search                           │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Data Flow (Updated)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              CONVERSATION FLOW                                 │
│                                                                                 │
│  User Input → Typo Correction → Language Detection → NLU Analysis              │
│       ↓                                                                         │
│  Entity Extraction → Emergency Check → Database Search → Context Analysis      │
│       ↓                                                                         │
│  Memory Update → Response Generation → Personalization → Translation          │
│       ↓                                                                         │
│  Multi-Question Processing → Response Splitting → User Output                  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Database Search System (Detailed)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              DATABASE SEARCH ENGINE                            │
│                                                                                 │
│  🔍 IMPROVED SCORER ALGORITHM                                                  │
│  • Exact Match: 100 points (highest priority)                                 │
│  • Keyword Match: 50 points                                                   │
│  • Word Overlap: 10 points per word                                           │
│  • Response Match: 5 points per word                                           │
│  • Length Bonus: 15 points (concise answers preferred)                        │
│  • Semantic Similarity: 80 points (fuzzy matching)                            │
│  • Intent Match: 40 points                                                    │
│                                                                                 │
│  🎯 CONTEXT-AWARE ENHANCEMENTS                                                 │
│  • Activity-specific boosting (school activities)                             │
│  • CR/Comfort Room queries with major boost                                    │
│  • Grade validation with special handling                                     │
│  • Emotional context enhancement for search queries                            │
│  • Intent-based search refinement                                              │
│                                                                                 │
│  📊 RESULT PROCESSING                                                          │
│  • Relevance ranking with confidence scores                                    │
│  • Context extraction for response generation                                  │
│  • Special handling for contact escalation queries                            │
│  • Fallback to keyword matching when needed                                   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Deployment Architecture (Updated)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              DEPLOYMENT OPTIONS                                │
│                                                                                 │
│  🚀 RENDER (Primary)                                                           │
│  • FastAPI + Uvicorn                                                           │
│  • Environment: Python 3.11                                                   │
│  • Auto-deployment from Git                                                    │
│  • Health monitoring with custom endpoints                                     │
│  • NLTK data path management                                                   │
│                                                                                 │
│  🚀 RAILWAY (Secondary)                                                        │
│  • FastAPI + Gunicorn                                                          │
│  • Environment: Python 3.11                                                   │
│  • Railway.json configuration                                                  │
│  • Health monitoring and metrics                                               │
│  • Optimized logging for production                                            │
│                                                                                 │
│  🚀 LOCAL DEVELOPMENT                                                          │
│  • FastAPI + Uvicorn                                                           │
│  • Environment: Python 3.11                                                   │
│  • NLTK data in local directory                                                │
│  • Development logging with debug information                                  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Security Features (Enhanced)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              SECURITY LAYERS                                   │
│                                                                                 │
│  🛡️ INPUT VALIDATION                                                           │
│  • SQL Injection Protection Middleware                                         │
│  • XSS Prevention in responses                                                 │
│  • Input Sanitization and validation                                           │
│  • Gibberish detection with NLP patterns                                       │
│                                                                                 │
│  🛡️ RATE LIMITING                                                              │
│  • Per-provider rate limits (Groq: 30/min, Cohere: 1000/min)                  │
│  • Global rate limiting for abuse prevention                                   │
│  • Rate limit monitoring and alerts                                           │
│                                                                                 │
│  🛡️ EMERGENCY DETECTION                                                        │
│  • Medical emergency detection with context analysis                           │
│  • Safety emergency detection for school incidents                            │
│  • Humor/sarcasm detection to prevent false positives                         │
│  • Standalone medical term validation                                         │
│  • Immediate 911 protocol activation                                          │
│                                                                                 │
│  🛡️ DATA PROTECTION                                                            │
│  • Encrypted API keys in environment variables                                 │
│  • Secure Supabase database connections                                       │
│  • Privacy-focused design with minimal data collection                        │
│  • Session management with context clearing                                   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Performance & Monitoring (Enhanced)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              PERFORMANCE FEATURES                              │
│                                                                                 │
│  ⚡ CACHING SYSTEM                                                              │
│  • Language detection cache with 83% hit rate                                  │
│  • Translation cache for repeated phrases                                      │
│  • Response cache for common queries                                            │
│  • NLTK data caching for faster initialization                                 │
│                                                                                 │
│  📊 MONITORING & METRICS                                                        │
│  • Health endpoints (/health, /admin/logs)                                     │
│  • Performance metrics (/admin/metrics)                                        │
│  • Error tracking and logging                                                  │
│  • Response time monitoring (<1.5s average)                                    │
│  • Cache hit rate monitoring                                                   │
│  • Provider health status tracking                                             │
│                                                                                 │
│  🔄 FALLBACK SYSTEM                                                             │
│  • Multi-provider AI with intelligent switching                               │
│  • Graceful degradation when providers fail                                   │
│  • Keyword matching fallback for critical queries                             │
│  • Offline capabilities with cached responses                                 │
│  • Error recovery with user-friendly messages                                 │
│                                                                                 │
│  🚀 OPTIMIZATION FEATURES                                                      │
│  • Token-efficient system prompts                                              │
│  • Reduced logging for production environments                                 │
│  • Database timeout optimization (15s)                                         │
│  • Memory-efficient conversation handling                                      │
│  • Async processing for better performance                                     │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Key Innovations & Technical Achievements

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              TECHNICAL INNOVATIONS                             │
│                                                                                 │
│  🎯 MULTI-QUESTION PROCESSING                                                  │
│  • Detects 2-5 questions in single input                                      │
│  • Structured response generation for each question                           │
│  • Context preservation across multiple questions                              │
│  • Intelligent question separation using NLP patterns                         │
│                                                                                 │
│  🧠 EMOTIONAL INTELLIGENCE                                                     │
│  • Real-time emotion detection (sad, happy, worried, etc.)                    │
│  • Sentiment analysis with confidence scoring                                  │
│  • Empathy level assessment for response adaptation                           │
│  • Support needs identification                                                │
│                                                                                 │
│  🌐 CONTEXT-AWARE TRANSLATION                                                   │
│  • Maintains conversation context during translation                          │
│  • Language-specific grammar preservation                                      │
│  • Cultural context awareness                                                  │
│  • Confidence scoring for translation quality                                 │
│                                                                                 │
│  🔍 ADVANCED DATABASE SEARCH                                                   │
│  • ImprovedScorer with weighted relevance scoring                             │
│  • Semantic similarity matching using difflib                                │
│  • Context-specific boosting for school topics                                │
│  • Intent-based search refinement                                              │
│                                                                                 │
│  🛡️ INTELLIGENT EMERGENCY DETECTION                                            │
│  • Context-aware analysis to prevent false positives                          │
│  • Humor and sarcasm detection                                                 │
│  • Standalone medical term validation                                          │
│  • Immediate safety protocol activation                                        │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Intent Classifications (Complete List)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              INTENT CLASSIFICATIONS                            │
│                                                                                 │
│  🚨 EMERGENCY INTENTS                                                           │
│  • EMERGENCY: Medical emergencies requiring immediate attention                │
│  • MEDICAL_EMERGENCY: Specific medical emergencies                            │
│  • SAFETY_EMERGENCY: School safety emergencies                                │
│                                                                                 │
│  👋 GREETING INTENTS                                                            │
│  • GREETING_SIMPLE: Basic greetings                                            │
│  • GREETING_WITH_NAME: Greetings with name introduction                        │
│  • GREETING_RETURNING_USER: Greeting for returning users                      │
│  • GREETING_EXCITED: Enthusiastic greetings                                    │
│  • GREETING_FORMAL: Formal/polite greetings                                    │
│  • GREETING_CASUAL: Casual greetings                                            │
│                                                                                 │
│  👤 INTRODUCTION INTENTS                                                        │
│  • NAME_INTRODUCTION: User introduces themselves                               │
│  • CHILD_INTRODUCTION: User introduces their child                            │
│  • NAME_QUERY: User asking about their own name                               │
│                                                                                 │
│  🏫 SCHOOL INFORMATION INTENTS                                                 │
│  • SCHOOL_INFO: General school information                                     │
│  • SCHOOL_OVERVIEW: School description/overview                               │
│  • GRADE_LEVELS: Questions about grades offered                                │
│  • SCHOOL_PROGRAMS: Academic programs and curriculum                          │
│  • FACILITIES_INQUIRY: Questions about school facilities                     │
│  • FINANCIAL_INQUIRY: Tuition, fees, payments                                 │
│                                                                                 │
│  📝 ENROLLMENT INTENTS                                                          │
│  • ENROLLMENT_INQUIRY: General enrollment questions                           │
│  • ENROLLMENT_DOCUMENTS: Document requirements                                 │
│  • ENROLLMENT_DEADLINE: Enrollment deadlines                                   │
│  • ENROLLMENT_PROCESS: Step-by-step enrollment process                        │
│                                                                                 │
│  📞 CONTACT INTENTS                                                             │
│  • STAFF_INQUIRY: Questions about teachers/staff                              │
│  • CONTACT_INFO: Contact information requests                                 │
│  • CONTACT_ESCALATION: Requests to speak to a person                          │
│                                                                                 │
│  💬 CONVERSATION FLOW INTENTS                                                   │
│  • FOLLOW_UP_QUESTION: Follow-up questions                                    │
│  • CLARIFICATION_REQUEST: Requests for more details                           │
│  • TOPIC_CONTINUATION: Continuing previous topics                              │
│  • COMPARISON_REQUEST: Comparing options/programs                             │
│  • LOCATION_INQUIRY: School location questions                                │
│  • SCHEDULE_INQUIRY: School hours/schedules                                   │
│                                                                                 │
│  😊 EMOTIONAL/SOCIAL INTENTS                                                    │
│  • EMOTIONAL_EXPRESSION: Expressing emotions                                  │
│  • APPRECIATION: Thank you messages                                           │
│  • HELP_REQUEST: General assistance requests                                  │
│  • CONFIRMATION: Yes/no responses                                             │
│  • DENIAL: User denying something                                             │
│  • CLARIFICATION: User clarifying meaning                                    │
│  • GOODBYE: User ending conversation                                          │
│                                                                                 │
│  ❓ FALLBACK INTENT                                                             │
│  • UNKNOWN: When intent cannot be determined                                  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Advanced NLP Capabilities

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              NLP CAPABILITIES                                  │
│                                                                                 │
│  🧠 INTENT CLASSIFICATION                                                       │
│  • 40+ intent types with confidence scoring                                    │
│  • Rule-based and AI-assisted classification                                   │
│  • Multilingual pattern matching (English, Tagalog, Aklanon)                  │
│  • Context-aware intent detection                                              │
│                                                                                 │
│  🔍 ENTITY EXTRACTION                                                           │
│  • Named entity recognition (person names, locations, etc.)                   │
│  • Relationship detection between entities                                     │
│  • Confidence scoring for extracted entities                                  │
│  • Context-aware entity extraction                                             │
│                                                                                 │
│  🌍 LANGUAGE DETECTION                                                          │
│  • Multi-language support (English, Tagalog, Aklanon)                         │
│  • Mixed-language input handling                                               │
│  • Context-aware language detection                                           │
│  • Confidence scoring for language detection                                  │
│                                                                                 │
│  💭 CONVERSATION ANALYSIS                                                       │
│  • Topic flow tracking across conversations                                   │
│  • Urgency level detection                                                     │
│  • User expertise assessment                                                   │
│  • Sentiment analysis and emotional state detection                           │
│                                                                                 │
│  🎭 EMOTIONAL INTELLIGENCE                                                     │
│  • Emotion detection (sad, happy, worried, etc.)                              │
│  • Sentiment scoring and analysis                                              │
│  • Empathy level assessment                                                    │
│  • Support needs identification                                                │
│                                                                                 │
│  🎨 RESPONSE PERSONALIZATION                                                    │
│  • User profile creation and management                                       │
│  • Conversation history analysis                                               │
│  • Dynamic tone adjustment                                                     │
│  • Formality level adaptation                                                  │
│                                                                                 │
│  🌐 CONTEXT-AWARE TRANSLATION                                                   │
│  • Maintains conversation context during translation                          │
│  • Confidence scoring for translation quality                                │
│  • Language-specific grammar handling                                         │
│  • Cultural context preservation                                              │
│                                                                                 │
│  ❓ MULTI-QUESTION PROCESSING                                                   │
│  • Detects multiple questions in single input                                 │
│  • Parses and structures responses for each question                          │
│  • Maintains context across multiple questions                                │
│  • Handles 2-5 questions per input                                            │
│                                                                                 │
│  🚨 EMERGENCY DETECTION                                                        │
│  • Medical emergency identification                                           │
│  • Safety protocol activation                                                 │
│  • Context-aware analysis                                                     │
│  • False positive reduction                                                   │
│                                                                                 │
│  ✏️ TEXT PREPROCESSING                                                          │
│  • Typo correction and normalization                                          │
│  • Stop word removal and stemming                                             │
│  • Text cleaning and sanitization                                             │
│  • Character encoding handling                                                │
│                                                                                 │
│  🔗 SEMANTIC SIMILARITY                                                        │
│  • Fuzzy matching using difflib                                               │
│  • Context-aware scoring                                                      │
│  • Relevance ranking                                                           │
│  • Similarity thresholds                                                       │
│                                                                                 │
│  🗣️ GIBBERISH DETECTION                                                         │
│  • Pattern recognition for nonsensical input                                  │
│  • Entropy analysis for randomness detection                                  │
│  • Language-specific validation                                               │
│  • Character diversity analysis                                               │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

This comprehensive architecture diagram represents a production-ready, multilingual chatbot system with advanced NLP capabilities, robust security measures, and intelligent fallback systems. It demonstrates sophisticated applied AI in education technology with comprehensive error handling, performance optimization, and real-world deployment considerations.
