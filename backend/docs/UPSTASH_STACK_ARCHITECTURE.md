# 🏗️ InterviewMe Architecture Refactor - Upstash Stack Integration

## 🎯 The Vision

**Current Stack (MVP):**
- FastAPI + PostgreSQL/SQLite
- Groq AI (direct calls)
- No caching
- No async jobs
- No vector search

**Target Stack (Production):**
- FastAPI + PostgreSQL
- **Upstash Redis** - Caching layer
- **Upstash QStash** - Async job processing
- **Upstash Vector** - Semantic search & RAG
- Groq AI (with intelligent caching)

---

## 🧠 Engineering Discussion: Why Each Component?

### 1. **Upstash Redis** - The Performance Layer

#### What It Does:
- Cache expensive AI operations (CV/JD analysis)
- Session management (WebSocket state)
- Rate limiting (per-user API quotas)
- Real-time data (interview progress, live stats)

#### Why Upstash Redis vs Standard Redis:
| Feature | Standard Redis | Upstash Redis |
|---------|---------------|---------------|
| **Connection** | TCP (persistent) | HTTP REST API |
| **Serverless** | ❌ Need server | ✅ Fully serverless |
| **Cold Start** | ❌ Connection overhead | ✅ No connections |
| **Pricing** | Fixed (even idle) | Pay-per-request |
| **Deployment** | Complex | Copy-paste URL |
| **Edge Support** | ❌ No | ✅ Global edge |

**Decision**: ✅ Use Upstash Redis
- Serverless-first (matches Vercel/Heroku deployment)
- No connection management (HTTP API)
- Free tier: 10,000 commands/day (enough for MVP)
- Scales automatically

#### Use Cases in InterviewMe:

**1. AI Response Caching**
```python
# Cache CV analysis for 2 hours
cache_key = f"cv:analysis:{hash(cv_text)}"
cached = await redis.get(cache_key)
if cached:
    return json.loads(cached)

result = await groq_api.analyze_cv(cv_text)
await redis.setex(cache_key, 7200, json.dumps(result))
```

**2. Session State (WebSocket)**
```python
# Store interview session state
session_key = f"interview:session:{interview_id}"
await redis.hset(session_key, {
    "current_turn": 3,
    "phase": "technical",
    "is_paused": False,
    "last_activity": timestamp
})
await redis.expire(session_key, 3600)  # 1 hour TTL
```

**3. Rate Limiting**
```python
# Limit user to 10 interviews per day
rate_key = f"rate:user:{user_id}:interviews:{date}"
count = await redis.incr(rate_key)
if count == 1:
    await redis.expire(rate_key, 86400)  # 24 hours
if count > 10:
    raise RateLimitError("Daily interview limit reached")
```

**4. Real-time Stats**
```python
# Track live interview metrics
await redis.hincrby("stats:interviews", "total", 1)
await redis.hincrby("stats:interviews", "active", 1)
await redis.zadd("stats:popular_roles", {"Software Engineer": 1})
```

---

### 2. **Upstash QStash** - The Async Job Layer

#### What It Does:
- Background job processing (email, reports, cleanup)
- Scheduled tasks (daily summaries, reminders)
- Webhook delivery (notify frontend when processing done)
- Retry logic (automatic retries on failure)

#### Why QStash vs Celery:
| Feature | Celery | QStash |
|---------|--------|--------|
| **Infrastructure** | Redis + Worker processes | Serverless (no workers) |
| **Deployment** | Complex (separate workers) | Simple (HTTP webhooks) |
| **Scaling** | Manual (add workers) | Automatic |
| **Monitoring** | DIY | Built-in dashboard |
| **Cost** | Redis + compute | Pay-per-request |
| **Cold Start** | ❌ Workers must run | ✅ No cold start |

**Decision**: ✅ Use QStash (remove Celery)
- No worker processes to manage
- Serverless-first architecture
- Built-in retry logic
- Free tier: 500 messages/day

#### Use Cases in InterviewMe:

**1. Async CV/JD Processing**
```python
# User uploads CV → return immediately
@app.post("/api/interviews/{id}/upload-cv")
async def upload_cv(interview_id: str, file: UploadFile):
    cv_text = await extract_text(file)
    
    # Queue processing job (don't wait)
    await qstash.publish_json(
        url=f"{settings.API_URL}/webhooks/process-cv",
        body={
            "interview_id": interview_id,
            "cv_text": cv_text
        },
        retries=3
    )
    
    return {"status": "processing", "message": "CV uploaded, analyzing..."}

# Webhook handler (called by QStash)
@app.post("/webhooks/process-cv")
async def process_cv_webhook(data: dict):
    interview_id = data["interview_id"]
    cv_text = data["cv_text"]
    
    # Process CV (can take 3-5 seconds)
    cv_analysis = await analyze_cv_with_ai(cv_text)
    
    # Update database
    await update_interview(interview_id, cv_analysis=cv_analysis)
    
    # Notify frontend via WebSocket
    await notify_user(interview_id, "cv_processed", cv_analysis)
    
    return {"status": "success"}
```

**2. Scheduled Jobs**
```python
# Send daily interview summary emails
await qstash.publish_json(
    url=f"{settings.API_URL}/webhooks/daily-summary",
    body={"date": today},
    schedule="0 9 * * *"  # Every day at 9 AM
)
```

**3. Delayed Jobs**
```python
# Send reminder 1 hour before scheduled interview
await qstash.publish_json(
    url=f"{settings.API_URL}/webhooks/send-reminder",
    body={"interview_id": interview_id},
    delay=3600  # 1 hour delay
)
```

**4. Cleanup Jobs**
```python
# Delete old interview data after 90 days
await qstash.publish_json(
    url=f"{settings.API_URL}/webhooks/cleanup-old-data",
    body={"before_date": ninety_days_ago},
    schedule="0 2 * * 0"  # Every Sunday at 2 AM
)
```

---

### 3. **Upstash Vector** - The Intelligence Layer

#### What It Does:
- Semantic search (find similar CVs, questions, interviews)
- RAG (Retrieval-Augmented Generation) for better questions
- Duplicate detection (same CV uploaded twice)
- Recommendation engine (suggest similar roles)

#### Why Upstash Vector vs Pinecone/Weaviate:
| Feature | Pinecone | Weaviate | Upstash Vector |
|---------|----------|----------|----------------|
| **Serverless** | ✅ Yes | ❌ Self-hosted | ✅ Yes |
| **Pricing** | $70/mo min | Complex | Free tier |
| **Integration** | Separate service | Separate service | Same ecosystem |
| **Setup** | Complex | Very complex | Simple |
| **Edge Support** | ❌ No | ❌ No | ✅ Yes |

**Decision**: ✅ Use Upstash Vector
- Same ecosystem as Redis/QStash (unified billing, auth)
- Serverless (no infrastructure)
- Free tier: 10,000 queries/day
- Simple REST API

#### Use Cases in InterviewMe:

**1. Semantic CV Search**
```python
# Find similar candidates
cv_embedding = await get_embedding(cv_text)  # OpenAI/Groq embeddings

# Store CV vector
await vector.upsert(
    vectors=[{
        "id": f"cv:{interview_id}",
        "vector": cv_embedding,
        "metadata": {
            "role": "Software Engineer",
            "years": 5,
            "skills": ["Python", "FastAPI", "React"]
        }
    }]
)

# Find similar CVs
similar = await vector.query(
    vector=cv_embedding,
    top_k=5,
    include_metadata=True
)
# Returns: 5 most similar CVs with metadata
```

**2. RAG for Better Interview Questions**
```python
# Generate question using past successful interviews
query_embedding = await get_embedding(f"{role} {seniority} technical question")

# Find similar past questions
similar_questions = await vector.query(
    vector=query_embedding,
    top_k=3,
    filter={"role": role, "rating": {"$gte": 8}}
)

# Use as context for LLM
context = "\n".join([q["metadata"]["question"] for q in similar_questions])
prompt = f"""
Based on these successful questions from past interviews:
{context}

Generate a new question for {role} at {seniority} level...
"""
```

**3. Duplicate Detection**
```python
# Check if CV already uploaded
cv_embedding = await get_embedding(cv_text)
similar = await vector.query(vector=cv_embedding, top_k=1)

if similar[0]["score"] > 0.95:  # 95% similarity
    return {"error": "This CV was already uploaded", "interview_id": similar[0]["id"]}
```

**4. Job Recommendation**
```python
# Recommend jobs based on CV
cv_embedding = await get_embedding(cv_text)

# Find matching job descriptions
matching_jobs = await vector.query(
    vector=cv_embedding,
    top_k=10,
    filter={"type": "job_description"}
)

return {"recommended_jobs": [j["metadata"] for j in matching_jobs]}
```

---

## 🏗️ Proposed Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Next.js)                       │
│  - User uploads CV/JD                                            │
│  - WebSocket for live interview                                  │
│  - Real-time updates                                             │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ HTTP/WebSocket
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BACKEND (FastAPI)                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  API Layer                                                │   │
│  │  - REST endpoints                                         │   │
│  │  - WebSocket handlers                                     │   │
│  │  - Webhook receivers (QStash callbacks)                   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                         │                                        │
│                         │                                        │
│  ┌──────────────────────┼────────────────────────────────────┐  │
│  │                      ▼                                     │  │
│  │            Service Layer                                   │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │  │
│  │  │ CV Processor│  │JD Processor │  │  Interview  │      │  │
│  │  │             │  │             │  │  Conductor  │      │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘      │  │
│  └────────────────────────────────────────────────────────────┘  │
│                         │                                        │
│                         │                                        │
│  ┌──────────────────────┼────────────────────────────────────┐  │
│  │                      ▼                                     │  │
│  │            Integration Layer                               │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │  │
│  │  │   Redis     │  │   QStash    │  │   Vector    │      │  │
│  │  │   Client    │  │   Client    │  │   Client    │      │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘      │  │
│  └────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                         │
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   Upstash    │  │   Upstash    │  │   Upstash    │
│    Redis     │  │    QStash    │  │   Vector     │
│              │  │              │  │              │
│  - Caching   │  │  - Async     │  │  - Semantic  │
│  - Sessions  │  │    Jobs      │  │    Search    │
│  - Rate      │  │  - Webhooks  │  │  - RAG       │
│    Limiting  │  │  - Schedules │  │  - Similarity│
└──────────────┘  └──────────────┘  └──────────────┘
        │                │                │
        └────────────────┼────────────────┘
                         │
                         ▼
                ┌──────────────┐
                │  PostgreSQL  │
                │   Database   │
                │              │
                │  - Users     │
                │  - Interviews│
                │  - Turns     │
                │  - Feedback  │
                └──────────────┘
```

---

## 📦 Refactored Project Structure

```
backend/
├── app/
│   ├── core/
│   │   ├── cache.py          # Redis cache manager
│   │   ├── queue.py          # QStash job manager
│   │   ├── vector.py         # Vector search manager
│   │   └── exceptions.py
│   │
│   ├── integrations/         # NEW: External service clients
│   │   ├── __init__.py
│   │   ├── upstash/
│   │   │   ├── __init__.py
│   │   │   ├── redis_client.py      # Upstash Redis wrapper
│   │   │   ├── qstash_client.py     # Upstash QStash wrapper
│   │   │   └── vector_client.py     # Upstash Vector wrapper
│   │   └── groq/
│   │       ├── __init__.py
│   │       └── client.py            # Groq AI client
│   │
│   ├── services/             # Business logic
│   │   ├── cv_service.py     # CV processing (uses cache + vector)
│   │   ├── jd_service.py     # JD processing (uses cache + vector)
│   │   ├── interview_service.py
│   │   └── analytics_service.py
│   │
│   ├── workers/              # NEW: QStash webhook handlers
│   │   ├── __init__.py
│   │   ├── cv_processor.py   # Async CV processing
│   │   ├── jd_processor.py   # Async JD processing
│   │   ├── email_sender.py   # Email notifications
│   │   └── cleanup.py        # Data cleanup jobs
│   │
│   ├── modules/
│   │   ├── auth/
│   │   ├── interviews/
│   │   └── websocket/
│   │
│   ├── models/               # Database models
│   ├── schemas/              # Pydantic schemas
│   ├── config.py
│   ├── database.py
│   └── main.py
│
├── tests/
├── alembic/
├── requirements.txt
└── .env
```

---

## 🔧 Implementation Plan

### Phase 1: Remove Celery, Add Upstash Clients (Week 1)

**Tasks:**
1. ✅ Remove Celery dependencies
2. ✅ Add Upstash SDK dependencies
3. ✅ Create Upstash client wrappers
4. ✅ Update config with Upstash credentials
5. ✅ Initialize clients in app startup

**Files to Change:**
- `requirements.txt` - Remove Celery, add Upstash SDKs
- `app/config.py` - Add Upstash config
- `app/integrations/upstash/` - Create client wrappers
- `app/main.py` - Initialize clients

---

### Phase 2: Implement Redis Caching (Week 1-2)

**Tasks:**
1. ✅ Wrap LLM calls with cache layer
2. ✅ Cache CV/JD analysis results
3. ✅ Implement session state in Redis
4. ✅ Add rate limiting
5. ✅ Add monitoring endpoints

**Files to Change:**
- `app/core/cache.py` - Cache manager
- `app/services/cv_service.py` - Add caching
- `app/services/jd_service.py` - Add caching
- `app/modules/websocket/` - Use Redis for session state

---

### Phase 3: Implement QStash Jobs (Week 2)

**Tasks:**
1. ✅ Create webhook endpoints
2. ✅ Move CV/JD processing to async
3. ✅ Implement email notifications
4. ✅ Add scheduled cleanup jobs
5. ✅ Add retry logic

**Files to Create:**
- `app/workers/cv_processor.py`
- `app/workers/jd_processor.py`
- `app/workers/email_sender.py`
- `app/modules/webhooks/router.py`

---

### Phase 4: Implement Vector Search (Week 3)

**Tasks:**
1. ✅ Generate embeddings for CVs/JDs
2. ✅ Store vectors in Upstash Vector
3. ✅ Implement semantic search
4. ✅ Add RAG for question generation
5. ✅ Add duplicate detection

**Files to Create:**
- `app/core/vector.py` - Vector manager
- `app/services/embedding_service.py`
- `app/services/search_service.py`

---

### Phase 5: Testing & Optimization (Week 4)

**Tasks:**
1. ✅ Integration tests
2. ✅ Performance benchmarks
3. ✅ Cost analysis
4. ✅ Documentation
5. ✅ Deployment

---

## 💰 Cost Analysis

### Free Tier Limits:
- **Upstash Redis**: 10,000 commands/day
- **Upstash QStash**: 500 messages/day
- **Upstash Vector**: 10,000 queries/day

### Expected Usage (100 users/day):
- **Redis**: ~5,000 commands/day (cache hits/misses, sessions)
- **QStash**: ~200 messages/day (CV/JD processing, emails)
- **Vector**: ~500 queries/day (similarity search)

**Verdict**: ✅ Free tier is enough for MVP + early growth

### At Scale (1,000 users/day):
- **Redis**: ~50,000 commands/day → $10/month
- **QStash**: ~2,000 messages/day → $5/month
- **Vector**: ~5,000 queries/day → Free tier

**Total**: ~$15/month (vs $300/month in Groq savings)

---

## 🎯 Key Engineering Decisions

### 1. **Why Upstash over AWS/GCP?**
- ✅ Serverless-first (no infrastructure)
- ✅ Unified ecosystem (Redis + QStash + Vector)
- ✅ Simple pricing (pay-per-request)
- ✅ Edge support (global low latency)
- ✅ Free tier (generous for MVP)

### 2. **Why Remove Celery?**
- ❌ Requires worker processes (not serverless)
- ❌ Complex deployment (separate workers)
- ❌ Manual scaling (add/remove workers)
- ❌ Monitoring overhead (DIY)
- ✅ QStash is simpler, serverless, auto-scaling

### 3. **Why Vector DB?**
- ✅ Semantic search (find similar CVs/questions)
- ✅ RAG (better interview questions)
- ✅ Duplicate detection (UX improvement)
- ✅ Future features (recommendations, analytics)

---

## 🚀 Next Steps

**What do you want to tackle first?**

1. **Option A: Start with Redis** (quickest win)
   - Implement caching layer
   - See immediate performance gains
   - ~2-3 hours work

2. **Option B: Start with QStash** (biggest refactor)
   - Remove Celery
   - Implement async jobs
   - ~1 day work

3. **Option C: Start with Vector** (most innovative)
   - Implement semantic search
   - Add RAG for questions
   - ~2 days work

4. **Option D: Full refactor** (all at once)
   - Implement all three
   - ~1 week work

**My recommendation**: Start with **Option A (Redis)** → then **Option B (QStash)** → then **Option C (Vector)**

This gives you incremental wins and validates each component before moving to the next.

---

**Ready to start? Which option do you want to implement first?** 🚀
