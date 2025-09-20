"""
🛠️ FIXED: Name Extraction Logic Enhancement
===========================================

🐛 ISSUE IDENTIFIED:
The NLU system was extracting adjectives and emotional words as names:
• "Hello! I am super excited!" → extracted "Super" as name 😅
• "Hi again! I am back..." → extracted "Back" as name

🔧 SOLUTION IMPLEMENTED:
Enhanced the _extract_name_from_query() method with:

1. EXPANDED EXCLUSION LIST:
   - Emotional words: super, excited, happy, sad, tired, etc.
   - Descriptive words: back, again, returning, new, etc.
   - Intensifiers: really, very, so, quite, pretty, extremely

2. CONTEXT-AWARE FILTERING:
   - Detects when words appear in adjective contexts
   - Example: "am super excited" → recognizes "super" as adjective

3. SMARTER PATTERN MATCHING:
   - Still captures real names: "Hello, my name is Sarah" ✅
   - Filters out false positives: "I am super excited" ❌

✅ RESULTS:
• "Hello! I am super excited!" → No name extracted (correct!)
• "Hi, I am John" → Extracts "John" (correct!)
• "Hello, my name is Sarah" → Extracts "Sarah" (correct!)
• "I am back to ask questions" → No name extracted (correct!)

🎯 IMPACT:
Users now get appropriate greetings instead of:
❌ "Good evening, Super! Nice to meet you!"
✅ "Good evening! Nice to meet you! I'm TOMAS..."

The NLU system is now much more intelligent about distinguishing 
between actual name introductions and emotional expressions! 🧠✨
"""