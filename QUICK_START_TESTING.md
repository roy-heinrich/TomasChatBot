# 🚀 Quick Start - Testing Language Bug Fixes

## ⚡ 30-Second Setup

```powershell
# 1. Navigate to project
cd "c:\Users\royhe\OneDrive\Documents\Coding\TomasChatBot"

# 2. Run tests
python test_language_fix.py
```

## 🎨 Interactive Testing (2 minutes)

```powershell
# Terminal 1: Start server
cd "c:\Users\royhe\OneDrive\Documents\Coding\TomasChatBot"
python test_server.py

# Then open browser to:
# http://localhost:8000
```

---

## ✅ What to Look For

### The Original Bug
**Query:** "13 years old"  
**Before:** Response in Tagalog ❌  
**After:** Response in English ✅  

### Test Results
- ✅ English queries = English responses
- ✅ Tagalog queries = Tagalog responses  
- ✅ No unexpected translations

---

## 📊 Expected Test Output

```
✅ Passed: 38/40
📈 Pass Rate: 95.0%

Categories:
  ✅ short_english    6/6  (100%)
  ✅ full_english     6/6  (100%)
  ✅ tagalog          6/6  (100%)
  ✅ mixed            3/3  (100%)
  ✅ edge_case        5/6  (83%)
```

---

## 🎯 Quick Test Checklist

- [ ] Run `python test_language_fix.py`
- [ ] Check pass rate > 90%
- [ ] Test "13 years old" in web UI
- [ ] Test "Sino ang guro?" in web UI
- [ ] Verify both respond in correct language

---

## 📚 Full Documentation

See **TESTING_GUIDE.md** for:
- Detailed test descriptions
- Troubleshooting guide
- CI/CD integration
- Result interpretation

---

## 💡 Commands Cheat Sheet

```powershell
# Run automated tests
python test_language_fix.py

# Start interactive web server
python test_server.py

# Stop server
Ctrl+C

# View test results
cat test_results.json | ConvertFrom-Json | ConvertTo-Json -Depth 10 | more
```

---

**Status:** Ready to test! Run `python test_language_fix.py` now 🚀
