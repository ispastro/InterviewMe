# Groq API Rate Limit Solutions

## Problem
```
Rate limit reached for model `llama-3.3-70b-versatile`
Limit: 100,000 tokens/day
Used: 99,012 tokens
Requested: 4,096 tokens
```

## Root Cause
The interview conductor was hitting Groq's free tier rate limit, causing it to fall back to the same hardcoded question repeatedly.

---

## Solutions (Choose One)

### Option 1: Switch to Smaller, Faster Model (Recommended for Development)

**Model**: `llama-3.1-8b-instant`
- ✅ **10x more tokens**: 1,000,000 tokens/day
- ✅ **Faster responses**: ~2x faster
- ✅ **Lower cost**: Free tier
- ⚠️ **Slightly less capable**: But still excellent for interviews

**How to switch:**
```bash
# In backend/.env
GROQ_MODEL=llama-3.1-8b-instant
```

**Token Usage Comparison:**
| Model | Tokens/Day | Avg Interview Cost | Interviews/Day |
|-------|------------|-------------------|----------------|
| llama-3.3-70b-versatile | 100,000 | ~10,000 tokens | ~10 |
| llama-3.1-8b-instant | 1,000,000 | ~8,000 tokens | ~125 |

---

### Option 2: Upgrade to Groq Dev Tier

**Cost**: Pay-as-you-go
- ✅ **No daily limits**
- ✅ **Higher rate limits**
- ✅ **Keep using 70B model**

**How to upgrade:**
1. Go to https://console.groq.com/settings/billing
2. Add payment method
3. Upgrade to Dev Tier

---

### Option 3: Implement Token Optimization (Do This Anyway)

**Reduce token usage by 40-60%:**

#### 1. Shorten Prompts
```python
# Before: ~2000 tokens
prompt = f"""
You are an expert AI interviewer with deep memory and context awareness...
[Long detailed instructions]
"""

# After: ~800 tokens
prompt = f"""
Expert interviewer. Generate next question based on:
- Candidate: {cv_summary}
- Job: {jd_summary}
- History: {recent_turns_only}
[Concise instructions]
"""
```

#### 2. Limit Conversation History
```python
# Only send last 3 turns instead of all history
recent_turns = conversation_history[-3:]
```

#### 3. Cache CV/JD Analysis
```python
# Don't send full CV/JD every time
# Send only relevant excerpts
```

#### 4. Use Streaming (Future Enhancement)
```python
# Stream responses instead of waiting for full completion
# Reduces perceived latency
```

---

## Implementation: Quick Switch to 8B Model

### Step 1: Update Environment Variable
```bash
cd backend
# Edit .env file
GROQ_MODEL=llama-3.1-8b-instant
```

### Step 2: Restart Backend
```bash
# Stop current server (Ctrl+C)
# Start again
uvicorn app.main:app --reload
```

### Step 3: Test
```bash
# Run a test interview
# Should work without rate limit errors
```

---

## Monitoring Rate Limits

### Add Rate Limit Tracking

**In `interview_conductor.py`:**
```python
async def generate_follow_up_question(self, ...):
    try:
        response = await self.client.chat.completions.create(...)
        
        # Log token usage
        usage = response.usage
        print(f"📊 Tokens used: {usage.total_tokens} (prompt: {usage.prompt_tokens}, completion: {usage.completion_tokens})")
        
        return result
    except Exception as e:
        if "rate_limit_exceeded" in str(e):
            print(f"⚠️ RATE LIMIT HIT: {e}")
            # Send alert or notification
        raise
```

### Add Daily Token Counter

**Create `backend/app/utils/token_tracker.py`:**
```python
from datetime import datetime, timedelta
from typing import Dict

class TokenTracker:
    def __init__(self):
        self.daily_usage: Dict[str, int] = {}
        self.reset_time = datetime.now() + timedelta(days=1)
    
    def add_usage(self, tokens: int):
        today = datetime.now().strftime("%Y-%m-%d")
        self.daily_usage[today] = self.daily_usage.get(today, 0) + tokens
        
        # Check if approaching limit
        if self.daily_usage[today] > 90000:  # 90% of 100k
            print(f"⚠️ WARNING: {self.daily_usage[today]}/100,000 tokens used today")
    
    def get_remaining(self) -> int:
        today = datetime.now().strftime("%Y-%m-%d")
        used = self.daily_usage.get(today, 0)
        return 100000 - used

token_tracker = TokenTracker()
```

---

## Fallback Strategy (Already Implemented)

We've already added multiple fallback questions that rotate:

```python
fallback_questions = [
    "Can you tell me more about a challenging project...",
    "How do you stay updated with latest technologies...",
    "Describe a situation with a difficult team member...",
    "What's your approach to debugging...",
    "Tell me about a technical decision..."
]

# Rotate based on turn number
fallback_index = (current_turn - 1) % len(fallback_questions)
```

This prevents the infinite loop even when API fails.

---

## Recommended Action Plan

### Immediate (5 minutes):
1. ✅ Switch to `llama-3.1-8b-instant` in `.env`
2. ✅ Restart backend
3. ✅ Test interview

### Short-term (1 hour):
1. ✅ Add token usage logging
2. ✅ Implement token tracker
3. ✅ Optimize prompts (reduce by 40%)

### Long-term (1 day):
1. ⏳ Upgrade to Groq Dev Tier (if needed)
2. ⏳ Implement prompt caching
3. ⏳ Add streaming responses
4. ⏳ Set up monitoring alerts

---

## Token Usage Optimization Examples

### Before (2000 tokens):
```python
prompt = f"""
You are an expert AI interviewer with deep memory and context awareness. You conduct natural, conversational interviews that adapt to the candidate's performance.

CANDIDATE PROFILE:
{json.dumps(cv_analysis, indent=2)}  # 500 tokens

JOB REQUIREMENTS:
{json.dumps(jd_analysis, indent=2)}  # 500 tokens

INTERVIEW STRATEGY:
{json.dumps(interview_strategy, indent=2)}  # 300 tokens

RECENT CONVERSATION:
{history_text}  # 400 tokens

[Long instructions...]  # 300 tokens
"""
```

### After (800 tokens):
```python
# Summarize CV/JD once, cache it
cv_summary = f"Skills: {', '.join(cv_analysis['skills']['technical'][:5])}"
jd_summary = f"Required: {', '.join(jd_analysis['required_skills'][:5])}"

# Only last 2 turns
recent = conversation_history[-2:]

prompt = f"""
Interviewer for {jd_summary}.
Candidate: {cv_summary}
Last Q&A: {recent}
Generate next question. JSON only.
"""
```

**Result**: 60% token reduction!

---

## Testing Rate Limit Handling

```bash
# Simulate rate limit
# In interview_conductor.py, temporarily add:
raise Exception("rate_limit_exceeded")

# Should see:
# - Fallback question used
# - Different question each time (no loop)
# - Clear error message in logs
```

---

## Status

✅ **Fallback rotation implemented** - Prevents infinite loops
✅ **Anti-loop detection added** - Catches repeated questions
✅ **Better error logging** - Shows rate limit errors clearly
⏳ **Model switch needed** - Change to `llama-3.1-8b-instant`
⏳ **Token optimization** - Reduce prompt sizes

---

## Quick Reference

| Issue | Solution | Time |
|-------|----------|------|
| Rate limit hit | Switch to 8B model | 5 min |
| Infinite loop | Already fixed (fallback rotation) | ✅ Done |
| High token usage | Optimize prompts | 1 hour |
| Need more capacity | Upgrade to Dev Tier | 5 min |

---

**Next Step**: Update `.env` with `GROQ_MODEL=llama-3.1-8b-instant` and restart!
