# 🤖 LLM Client - The Foundation Layer

## 🎯 What It Does (Plain English)

The LLM Client is your **single gateway to talk to Groq AI**. Instead of creating 10 different connections to Groq in 10 different files, you create ONE client and reuse it everywhere.

**Think of it like your phone's contact app:**
- You save "Mom" once with her number
- Every time you call/text Mom, you use that saved contact
- You don't re-enter her number every single time

**Our LLM Client:**
- Connects to Groq API once
- Saves default settings (model, temperature, max tokens)
- Provides 2 simple methods: `chat_completion()` and `chat_completion_json()`
- Handles retries automatically if API fails
- Parses JSON responses (even if AI wraps them in markdown)

---

## 🤔 Why We Built It This Way

### ❌ The Problem Before

**Old code had 3 separate Groq clients:**

```python
# cv_processor.py
groq_client = AsyncGroq(api_key=settings.GROQ_API_KEY)

# jd_processor.py  
groq_client = AsyncGroq(api_key=settings.GROQ_API_KEY)

# interview_conductor.py
self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)
```

**Problems:**
1. ❌ **Duplicated code** - Same retry logic copied 3 times
2. ❌ **Inconsistent error handling** - Each file handles errors differently
3. ❌ **Hard to change** - Want to switch from Groq to OpenAI? Update 3+ files!
4. ❌ **No caching** - Can't add caching layer without touching every file
5. ❌ **Testing nightmare** - Need to mock Groq in 3 different places

### ✅ Our Solution

**One centralized client:**

```python
# app/modules/llm/client.py
llm_client = LLMClient()  # Created ONCE

# Everywhere else
from app.modules.llm import llm_client
result = await llm_client.chat_completion_json(prompt)
```

**Benefits:**
1. ✅ **Single source of truth** - One place for all LLM logic
2. ✅ **Consistent behavior** - Same retry logic, error handling everywhere
3. ✅ **Easy to swap** - Change Groq to OpenAI in ONE file
4. ✅ **Caching ready** - Add cache layer without touching other code
5. ✅ **Easy testing** - Mock once, works everywhere

---

## 🔧 How It Works (Line by Line)

### 🏗️ Part 1: The Constructor (`__init__`)

```python
class LLMClient:
    def __init__(self):
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_MODEL
        self.default_max_tokens = settings.GROQ_MAX_TOKENS
        self.default_temperature = settings.GROQ_TEMPERATURE
```

**What's happening:**

1. **`self.client = AsyncGroq(...)`**
   - Creates connection to Groq API
   - `AsyncGroq` = async version (handles multiple requests concurrently)
   - Uses API key from settings (centralized config)
   - Stored in `self.client` so all methods can reuse it

2. **`self.model = settings.GROQ_MODEL`**
   - Saves model name (e.g., "llama-3.3-70b-versatile")
   - Why? Change model in ONE place (settings.py), affects all calls
   - No hardcoded model names scattered everywhere

3. **`self.default_max_tokens` & `self.default_temperature`**
   - Default values for API calls
   - `max_tokens` = max response length (e.g., 2048 tokens)
   - `temperature` = creativity (0.0 = deterministic, 1.0 = creative)
   - Methods can override these, or use defaults

**Real-world analogy:**
Like setting up your car's default settings:
- Radio station preset (model)
- Default AC temperature (temperature)
- Cruise control speed (max_tokens)

You set them once, then every drive uses those defaults unless you manually change them.

---

### 🔄 Part 2: The Retry Decorator

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((Exception,)),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True
)
async def chat_completion(...):
```

**What's happening:**

This decorator wraps the method and adds **automatic retry logic**.

**Line by line:**

1. **`stop=stop_after_attempt(3)`**
   - Try maximum 3 times
   - Attempt 1 fails → retry
   - Attempt 2 fails → retry
   - Attempt 3 fails → give up, raise error

2. **`wait=wait_exponential(multiplier=1, min=2, max=10)`**
   - **Exponential backoff** = wait longer each retry
   - Formula: `wait_time = multiplier * (2 ^ attempt_number)`
   - 1st retry: wait 2 seconds (min)
   - 2nd retry: wait 4 seconds (2^2)
   - 3rd retry: wait 8 seconds (2^3, but capped at max=10)

3. **`retry=retry_if_exception_type((Exception,))`**
   - Only retry if an Exception occurs
   - If successful → no retry (obviously!)

4. **`before_sleep=before_sleep_log(logger, logging.WARNING)`**
   - Before each retry, log a warning
   - Example: "Attempt 1 failed, retrying in 2 seconds..."
   - Helps debugging production issues

5. **`reraise=True`**
   - After 3 failed attempts, raise the original error
   - Don't hide failures, let caller handle them

**Real-world analogy:**
Like calling customer service:
- Call 1: Busy signal → wait 2 minutes, try again
- Call 2: Still busy → wait 4 minutes, try again
- Call 3: Still busy → wait 8 minutes, try again
- After 3 tries: Give up, tell user "Service unavailable"

**Why exponential backoff?**
- If Groq server is overloaded, constant 2s retries keep hammering it
- Exponential gives server more breathing room to recover
- Industry standard pattern (AWS, Google, etc. all use this)

---

### 💬 Part 3: The `chat_completion` Method

```python
async def chat_completion(
    self,
    prompt: str,
    system_prompt: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    top_p: float = 0.9
) -> str:
```

**What's happening:**

This is the **main method** for getting text responses from Groq.

**Parameters explained:**

- **`prompt`** (required) - The user's question/instruction
  - Example: "Analyze this CV: {cv_text}"

- **`system_prompt`** (optional) - Instructions for AI's behavior
  - Example: "You are an expert HR professional..."
  - Sets the AI's role/personality

- **`temperature`** (optional) - Creativity level (0.0 to 1.0)
  - 0.0 = Deterministic, same answer every time
  - 0.7 = Balanced (our default)
  - 1.0 = Very creative, different answers
  - If not provided, uses `self.default_temperature`

- **`max_tokens`** (optional) - Max response length
  - Example: 2048 tokens ≈ 1500 words
  - If not provided, uses `self.default_max_tokens`

- **`top_p`** (optional) - Nucleus sampling (default 0.9)
  - Controls diversity of word choices
  - 0.9 = Good balance (industry standard)

**Returns:** Plain text string

---

**Method body breakdown:**

```python
messages = []
if system_prompt:
    messages.append({"role": "system", "content": system_prompt})
messages.append({"role": "user", "content": prompt})
```

**Building the conversation:**
- Groq expects messages in chat format
- `system` role = AI's instructions
- `user` role = The actual question
- Example:
  ```python
  [
      {"role": "system", "content": "You are a helpful assistant"},
      {"role": "user", "content": "What is Python?"}
  ]
  ```

---

```python
response = await self.client.chat.completions.create(
    model=self.model,
    messages=messages,
    temperature=temperature or self.default_temperature,
    max_tokens=max_tokens or self.default_max_tokens,
    top_p=top_p
)
```

**Making the API call:**
- `await` = async call, doesn't block other operations
- `self.client` = The AsyncGroq instance we created in `__init__`
- `temperature or self.default_temperature` = Use provided value, or fallback to default
- Python trick: `None or default` returns `default`

---

```python
if not response.choices or not response.choices[0].message:
    raise AIServiceError("Empty response from AI service")

return response.choices[0].message.content.strip()
```

**Validating and returning:**
- Check if response has content
- Groq returns: `response.choices[0].message.content`
- `.strip()` removes leading/trailing whitespace
- If empty → raise custom error

---

```python
except Exception as e:
    logger.error(f"LLM chat completion failed: {str(e)}")
    raise AIServiceError(f"LLM request failed: {str(e)}")
```

**Error handling:**
- Catch any exception
- Log it for debugging
- Raise custom `AIServiceError` (our app's error type)
- Why custom error? So other code can catch `AIServiceError` specifically

**Real-world analogy:**
Like ordering food delivery:
1. You place order (send prompt)
2. Restaurant confirms (API responds)
3. You get food (return content)
4. If restaurant closed → error (raise AIServiceError)

---

### 📦 Part 4: The `chat_completion_json` Method

```python
async def chat_completion_json(
    self,
    prompt: str,
    system_prompt: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None
) -> Dict[str, Any]:
```

**What's happening:**

This method is for when you **expect JSON response** from AI.

**Why separate method?**
- CV/JD analysis returns structured JSON
- Interview questions return JSON
- Need to parse JSON and handle errors

**Method body:**

```python
content = await self.chat_completion(
    prompt=prompt,
    system_prompt=system_prompt,
    temperature=temperature,
    max_tokens=max_tokens
)
```

**Reusing existing method:**
- Calls `chat_completion()` to get text response
- DRY principle: Don't Repeat Yourself
- All retry logic, error handling inherited

---

```python
try:
    return self._parse_json_response(content)
except json.JSONDecodeError as e:
    logger.error(f"Failed to parse JSON response: {content[:200]}")
    raise AIServiceError(f"Invalid JSON response from AI: {str(e)}")
```

**Parsing JSON:**
- Try to parse the text as JSON
- If fails → log first 200 chars (for debugging)
- Raise custom error with helpful message

**Why might parsing fail?**
- AI returns markdown: ` ```json\n{...}\n``` `
- AI adds explanation: "Here's the JSON: {...}"
- AI returns invalid JSON: `{name: "test"}` (missing quotes)

That's why we need `_parse_json_response()`...

---

### 🧩 Part 5: The `_parse_json_response` Helper

```python
def _parse_json_response(self, content: str) -> Dict[str, Any]:
    try:
        return json.loads(content.strip())
    except json.JSONDecodeError:
        if "```" in content:
            start = content.find("```json") + 7 if "```json" in content else content.find("```") + 3
            end = content.find("```", start)
            if end > start:
                return json.loads(content[start:end].strip())
        raise
```

**What's happening:**

This is a **smart JSON parser** that handles AI quirks.

**Step 1: Try simple parse**
```python
return json.loads(content.strip())
```
- Try parsing directly
- `.strip()` removes whitespace
- If works → done!

**Step 2: Extract from markdown**
```python
if "```" in content:
```
- AI often wraps JSON in markdown code blocks
- Example:
  ```
  Here's the analysis:
  ```json
  {"name": "John", "age": 30}
  ```
  ```

**Step 3: Find JSON boundaries**
```python
start = content.find("```json") + 7 if "```json" in content else content.find("```") + 3
```
- Look for ` ```json ` first (7 chars)
- If not found, look for ` ``` ` (3 chars)
- `start` = position after the opening backticks

```python
end = content.find("```", start)
```
- Find closing ` ``` ` after the opening
- `end` = position of closing backticks

```python
if end > start:
    return json.loads(content[start:end].strip())
```
- Extract text between backticks
- Parse that as JSON
- If works → done!

**Step 4: Give up**
```python
raise
```
- Re-raise the original `json.JSONDecodeError`
- Let caller handle it

**Real-world analogy:**
Like opening a package:
1. Try opening normally (simple parse)
2. If wrapped in bubble wrap, remove it first (extract from markdown)
3. If still can't open, give up and ask for help (raise error)

---

### 🎯 Part 6: The Singleton Instance

```python
llm_client = LLMClient()
```

**What's happening:**

At the bottom of the file, we create **ONE instance** of LLMClient.

**Why?**
- When you `import` this module, Python runs this line
- Creates the instance ONCE
- Every file that imports gets the SAME instance

**Usage everywhere:**
```python
# cv_processor.py
from app.modules.llm import llm_client
result = await llm_client.chat_completion_json(prompt)

# jd_processor.py
from app.modules.llm import llm_client
result = await llm_client.chat_completion_json(prompt)

# interview_conductor.py
from app.modules.llm import llm_client
result = await llm_client.chat_completion(prompt)
```

**All three files use the SAME `llm_client` instance!**

**Benefits:**
- ✅ One Groq connection shared across app
- ✅ Consistent settings everywhere
- ✅ Easy to mock for testing
- ✅ Memory efficient

**Real-world analogy:**
Like a company's printer:
- One printer in the office (singleton)
- Everyone uses the same printer
- Don't need 50 printers for 50 employees

---

## 💡 Key Concepts Used

### 1. **Singleton Pattern**
- One instance shared across entire app
- Created at module import time
- Memory efficient, consistent behavior

### 2. **Dependency Injection**
- Settings injected via `app.config.settings`
- Easy to change without touching code
- Testable (can inject mock settings)

### 3. **Retry with Exponential Backoff**
- Industry standard for API calls
- Handles transient failures gracefully
- Gives overloaded servers time to recover

### 4. **DRY (Don't Repeat Yourself)**
- `chat_completion_json()` reuses `chat_completion()`
- Retry logic defined once, applied to both methods
- JSON parsing logic in separate helper

### 5. **Defensive Programming**
- Validate response before returning
- Handle markdown-wrapped JSON
- Log errors for debugging
- Raise custom exceptions

### 6. **Async/Await**
- Non-blocking API calls
- Can handle multiple requests concurrently
- Essential for web servers

---

## 🚨 Common Mistakes Avoided

### ❌ Mistake 1: Creating client in every function
```python
# BAD
async def analyze_cv(cv_text):
    client = AsyncGroq(api_key=settings.GROQ_API_KEY)  # New connection every time!
    response = await client.chat.completions.create(...)
```

**Why bad?**
- Creates new connection every call (slow!)
- Wastes resources
- Can hit connection limits

**Our solution:** Singleton instance, reused everywhere

---

### ❌ Mistake 2: No retry logic
```python
# BAD
async def chat_completion(prompt):
    response = await self.client.chat.completions.create(...)
    # Network hiccup → FAILS IMMEDIATELY
```

**Why bad?**
- Transient failures crash the app
- Poor user experience
- Production systems need resilience

**Our solution:** `@retry` decorator with exponential backoff

---

### ❌ Mistake 3: Hardcoded settings
```python
# BAD
response = await client.chat.completions.create(
    model="llama-3.3-70b-versatile",  # Hardcoded!
    temperature=0.7,                   # Hardcoded!
    max_tokens=2048                    # Hardcoded!
)
```

**Why bad?**
- Want to change model? Update 50 files!
- Can't configure per environment (dev/prod)
- Testing nightmare

**Our solution:** Settings from `app.config`, defaults in `__init__`

---

### ❌ Mistake 4: Ignoring markdown-wrapped JSON
```python
# BAD
def parse_json(content):
    return json.loads(content)  # Fails if AI returns ```json\n{...}\n```
```

**Why bad?**
- AI often wraps JSON in markdown
- Parsing fails randomly
- Hard to debug

**Our solution:** `_parse_json_response()` handles markdown extraction

---

### ❌ Mistake 5: Generic exceptions
```python
# BAD
except Exception as e:
    raise Exception(f"Error: {e}")  # Generic error
```

**Why bad?**
- Can't catch specific LLM errors
- Hard to handle different error types
- Poor error messages

**Our solution:** Raise custom `AIServiceError` with context

---

## 🎓 Quick Reference

### Basic Usage

```python
from app.modules.llm import llm_client

# Simple text response
response = await llm_client.chat_completion(
    prompt="What is Python?",
    system_prompt="You are a helpful coding tutor"
)
print(response)  # "Python is a high-level programming language..."

# JSON response
result = await llm_client.chat_completion_json(
    prompt="Analyze this CV: {cv_text}. Return JSON with name, skills, experience.",
    temperature=0.3  # Lower = more consistent
)
print(result)  # {"name": "John", "skills": [...], ...}
```

### Advanced Usage

```python
# Override defaults
response = await llm_client.chat_completion(
    prompt="Write a creative story",
    temperature=0.9,      # More creative
    max_tokens=4096       # Longer response
)

# With system prompt
response = await llm_client.chat_completion(
    prompt="How do I center a div?",
    system_prompt="You are a senior frontend engineer. Be concise and practical."
)
```

### Error Handling

```python
from app.core.exceptions import AIServiceError

try:
    result = await llm_client.chat_completion_json(prompt)
except AIServiceError as e:
    logger.error(f"LLM failed: {e}")
    # Fallback logic here
    result = {"error": "AI service unavailable"}
```

---

## 🔗 What's Next?

Now that we have the **foundation layer** (LLM Client), we can build:

1. **Cache Layer** (`cache.py`) - Redis caching to avoid redundant API calls
2. **Gateway Layer** (`gateway.py`) - Orchestration with caching + direct/queue routing
3. **Queue Layer** (`queue.py`) - Celery tasks for async processing

Each layer builds on top of this client! 🚀

---

## 📊 Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    YOUR CODE                             │
│  (cv_processor, jd_processor, interview_conductor)      │
└─────────────────────┬───────────────────────────────────┘
                      │
                      │ import llm_client
                      ▼
┌─────────────────────────────────────────────────────────┐
│              LLMClient (client.py)                       │
│  ┌─────────────────────────────────────────────────┐   │
│  │  chat_completion()        ← Text responses      │   │
│  │  chat_completion_json()   ← JSON responses      │   │
│  │  _parse_json_response()   ← Smart JSON parser   │   │
│  └─────────────────────────────────────────────────┘   │
│                      │                                   │
│                      │ @retry decorator                  │
│                      │ (3 attempts, exponential backoff) │
│                      ▼                                   │
│              AsyncGroq Client                            │
└─────────────────────┬───────────────────────────────────┘
                      │
                      │ HTTPS
                      ▼
              ┌───────────────┐
              │   Groq API    │
              │ (llama-3.3)   │
              └───────────────┘
```

---

**Last Updated:** 2024  
**Status:** ✅ Production Ready  
**Next:** Build Cache Layer (`02-cache.md`)
