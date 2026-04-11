# 🚀 Production Deployment Guide - Heroku

## 📋 Table of Contents
1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Backend Deployment (Heroku)](#backend-deployment-heroku)
3. [Frontend Deployment (Vercel)](#frontend-deployment-vercel)
4. [Environment Configuration](#environment-configuration)
5. [Database Setup](#database-setup)
6. [Monitoring & Logging](#monitoring--logging)
7. [CI/CD Pipeline](#cicd-pipeline)
8. [Security Hardening](#security-hardening)
9. [Performance Optimization](#performance-optimization)
10. [Rollback Strategy](#rollback-strategy)

---

## ✅ Pre-Deployment Checklist

### **1. Code Quality**
- [ ] All tests passing (37/37 tests)
- [ ] No hardcoded secrets in code
- [ ] `.env` files in `.gitignore`
- [ ] Production dependencies only in `requirements.txt`
- [ ] Remove debug/test files from deployment

### **2. Security**
- [ ] JWT_SECRET is 32+ characters (cryptographically secure)
- [ ] CORS origins restricted to production domains
- [ ] Rate limiting enabled
- [ ] File upload size limits configured
- [ ] SQL injection protection (SQLAlchemy ORM)
- [ ] XSS protection (FastAPI auto-escaping)

### **3. Performance**
- [ ] Redis caching enabled (Upstash)
- [ ] Database indexes created
- [ ] Connection pooling configured
- [ ] Static file compression enabled
- [ ] CDN configured for frontend assets

### **4. Monitoring**
- [ ] Health check endpoints working
- [ ] Error tracking configured (Sentry)
- [ ] Logging configured (structured JSON logs)
- [ ] Uptime monitoring (UptimeRobot/Pingdom)
- [ ] Performance monitoring (New Relic/DataDog)

---

## 🔧 Backend Deployment (Heroku)

### **Step 1: Install Heroku CLI**
```bash
# Windows (using Chocolatey)
choco install heroku-cli

# Or download from: https://devcenter.heroku.com/articles/heroku-cli
```

### **Step 2: Login to Heroku**
```bash
heroku login
```

### **Step 3: Create Heroku App**
```bash
cd backend

# Create app (choose unique name)
heroku create interviewme-api-prod

# Or use auto-generated name
heroku create

# Verify app created
heroku apps:info
```

### **Step 4: Add PostgreSQL Database**
```bash
# Add Heroku Postgres (Essential-0 plan - $5/month)
heroku addons:create heroku-postgresql:essential-0

# Or use free tier (limited to 10K rows)
# heroku addons:create heroku-postgresql:mini

# Verify database created
heroku pg:info

# Get database URL (auto-set as DATABASE_URL)
heroku config:get DATABASE_URL
```

### **Step 5: Configure Environment Variables**
```bash
# Set all required environment variables
heroku config:set ENVIRONMENT=production
heroku config:set APP_DEBUG=False

# JWT Secret (generate secure 64-char secret)
heroku config:set JWT_SECRET=$(openssl rand -hex 32)

# Groq API
heroku config:set GROQ_API_KEY=your_groq_api_key_here
heroku config:set GROQ_MODEL=llama-3.3-70b-versatile
heroku config:set GROQ_MAX_TOKENS=2048
heroku config:set GROQ_TEMPERATURE=0.7

# Upstash Redis
heroku config:set UPSTASH_REDIS_REST_URL=https://golden-bee-77887.upstash.io
heroku config:set UPSTASH_REDIS_REST_TOKEN=your_upstash_token_here
heroku config:set REDIS_ENABLED=true
heroku config:set CACHE_TTL_SECONDS=3600

# CORS (add your frontend domain)
heroku config:set CORS_ORIGINS='["https://interviewme-app.vercel.app","https://www.yourdomain.com"]'

# Rate Limiting
heroku config:set MAX_INTERVIEWS_PER_USER_PER_DAY=10
heroku config:set MAX_WEBSOCKET_CONNECTIONS_PER_USER=3

# File Upload
heroku config:set MAX_FILE_SIZE_MB=5
heroku config:set ALLOWED_FILE_TYPES='["pdf","docx","txt"]'

# Verify all config vars
heroku config
```

### **Step 6: Deploy to Heroku**
```bash
# Initialize git (if not already)
git init
git add .
git commit -m "Initial production deployment"

# Add Heroku remote
heroku git:remote -a interviewme-api-prod

# Deploy
git push heroku main

# Or if on different branch
git push heroku your-branch:main
```

### **Step 7: Run Database Migrations**
```bash
# Migrations run automatically via Procfile release command
# But you can manually trigger if needed:
heroku run alembic upgrade head

# Verify database tables created
heroku pg:psql
# Then run: \dt
```

### **Step 8: Scale Dynos**
```bash
# Start with 1 web dyno (free tier)
heroku ps:scale web=1

# For production, use Hobby dyno ($7/month)
heroku dyno:type hobby

# Or Professional dyno ($25-$250/month)
# heroku dyno:type professional
```

### **Step 9: Verify Deployment**
```bash
# Check app status
heroku ps

# View logs
heroku logs --tail

# Test health endpoint
curl https://interviewme-api-prod.herokuapp.com/health

# Test API docs
open https://interviewme-api-prod.herokuapp.com/docs
```

---

## 🌐 Frontend Deployment (Vercel)

### **Step 1: Install Vercel CLI**
```bash
npm i -g vercel
```

### **Step 2: Login to Vercel**
```bash
vercel login
```

### **Step 3: Deploy Frontend**
```bash
cd frontend

# Deploy (follow prompts)
vercel

# For production deployment
vercel --prod
```

### **Step 4: Configure Environment Variables**
Go to Vercel Dashboard → Project → Settings → Environment Variables

Add:
```
NEXT_PUBLIC_API_URL=https://interviewme-api-prod.herokuapp.com
NEXT_PUBLIC_WS_URL=wss://interviewme-api-prod.herokuapp.com
```

### **Step 5: Redeploy with Environment Variables**
```bash
vercel --prod
```

---

## 🔐 Environment Configuration

### **Backend `.env.production` (for reference only - use Heroku config vars)**
```env
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname

# Authentication
JWT_SECRET=your_64_character_cryptographically_secure_secret_key_here
JWT_ALGORITHM=HS256

# Groq AI
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_MAX_TOKENS=2048
GROQ_TEMPERATURE=0.7

# Upstash Redis
UPSTASH_REDIS_REST_URL=https://golden-bee-77887.upstash.io
UPSTASH_REDIS_REST_TOKEN=AxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxQ
REDIS_ENABLED=true
CACHE_TTL_SECONDS=3600

# Application
CORS_ORIGINS=["https://interviewme-app.vercel.app"]
ENVIRONMENT=production
APP_DEBUG=False

# Rate Limiting
MAX_INTERVIEWS_PER_USER_PER_DAY=10
MAX_WEBSOCKET_CONNECTIONS_PER_USER=3

# File Upload
MAX_FILE_SIZE_MB=5
ALLOWED_FILE_TYPES=["pdf","docx","txt"]
```

### **Frontend `.env.production`**
```env
NEXT_PUBLIC_API_URL=https://interviewme-api-prod.herokuapp.com
NEXT_PUBLIC_WS_URL=wss://interviewme-api-prod.herokuapp.com
```

---

## 🗄️ Database Setup

### **PostgreSQL Configuration**

#### **1. Connection Pooling**
Heroku Postgres includes connection pooling by default. For custom setup:

```python
# app/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.database_echo,
    pool_size=10,              # Max connections
    max_overflow=20,           # Extra connections when pool full
    pool_timeout=30,           # Wait time for connection
    pool_recycle=3600,         # Recycle connections after 1 hour
    pool_pre_ping=True,        # Verify connection before use
)
```

#### **2. Database Indexes**
Already created via Alembic migrations:
- `ix_users_email` - User email lookup
- `ix_interviews_user_id` - User's interviews
- `ix_interviews_status` - Interview status filtering
- `ix_turns_interview_id` - Interview turns lookup

#### **3. Database Backups**
```bash
# Heroku auto-backups (Essential plan and above)
heroku pg:backups:schedule DATABASE_URL --at '02:00 America/Los_Angeles'

# Manual backup
heroku pg:backups:capture

# Download backup
heroku pg:backups:download

# Restore backup
heroku pg:backups:restore b001 DATABASE_URL
```

---

## 📊 Monitoring & Logging

### **1. Application Logging**

#### **Install Sentry (Error Tracking)**
```bash
pip install sentry-sdk[fastapi]
```

#### **Configure Sentry**
```python
# app/main.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

if settings.is_production:
    sentry_sdk.init(
        dsn="https://your-sentry-dsn@sentry.io/project-id",
        integrations=[FastApiIntegration()],
        traces_sample_rate=0.1,  # 10% of transactions
        environment=settings.ENVIRONMENT,
    )
```

#### **Structured Logging**
```python
# app/core/logging.py
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)

# Configure in main.py
logging.basicConfig(
    level=logging.INFO if settings.is_production else logging.DEBUG,
    handlers=[logging.StreamHandler()],
)
for handler in logging.root.handlers:
    handler.setFormatter(JSONFormatter())
```

### **2. Heroku Logging**
```bash
# View real-time logs
heroku logs --tail

# View last 1000 lines
heroku logs -n 1000

# Filter by dyno
heroku logs --dyno web.1

# Filter by source
heroku logs --source app

# Add log drain (send to external service)
heroku drains:add https://logs.example.com/drain
```

### **3. Uptime Monitoring**

#### **UptimeRobot (Free)**
- Monitor: `https://interviewme-api-prod.herokuapp.com/health`
- Interval: 5 minutes
- Alert: Email/SMS on downtime

#### **Pingdom (Paid)**
- Advanced monitoring with response time tracking
- Global monitoring locations
- Detailed performance reports

### **4. Performance Monitoring**

#### **New Relic (Free tier available)**
```bash
# Add New Relic addon
heroku addons:create newrelic:wayne

# Install agent
pip install newrelic

# Configure
heroku config:set NEW_RELIC_APP_NAME="InterviewMe API"
```

---

## 🔄 CI/CD Pipeline

### **GitHub Actions Workflow**

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'
    
    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        cd backend
        python -m pytest tests/ -v
    
    - name: Run production validation
      run: |
        cd backend
        python production_validation.py

  deploy-backend:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to Heroku
      uses: akhileshns/heroku-deploy@v3.12.14
      with:
        heroku_api_key: ${{secrets.HEROKU_API_KEY}}
        heroku_app_name: "interviewme-api-prod"
        heroku_email: "your-email@example.com"
        appdir: "backend"

  deploy-frontend:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to Vercel
      uses: amondnet/vercel-action@v20
      with:
        vercel-token: ${{ secrets.VERCEL_TOKEN }}
        vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
        vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
        working-directory: ./frontend
```

### **Setup GitHub Secrets**
1. Go to GitHub repo → Settings → Secrets → Actions
2. Add secrets:
   - `HEROKU_API_KEY` - From Heroku account settings
   - `VERCEL_TOKEN` - From Vercel account settings
   - `VERCEL_ORG_ID` - From Vercel project settings
   - `VERCEL_PROJECT_ID` - From Vercel project settings

---

## 🔒 Security Hardening

### **1. HTTPS Only**
```python
# app/main.py
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

if settings.is_production:
    app.add_middleware(HTTPSRedirectMiddleware)
```

### **2. Security Headers**
```python
# app/main.py
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["interviewme-api-prod.herokuapp.com", "*.vercel.app"]
)

@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
```

### **3. Rate Limiting**
```python
# app/core/rate_limiter.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)

# In main.py
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# On endpoints
@router.post("/interviews")
@limiter.limit("10/minute")
async def create_interview(request: Request, ...):
    ...
```

### **4. Input Validation**
Already implemented via Pydantic schemas. Ensure all endpoints use typed schemas.

### **5. SQL Injection Protection**
Already protected via SQLAlchemy ORM (parameterized queries).

### **6. File Upload Security**
```python
# app/utils/text_extraction.py
ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

async def validate_file(file: UploadFile):
    # Check extension
    ext = file.filename.split(".")[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(f"File type .{ext} not allowed")
    
    # Check file size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise ValidationError("File too large (max 5MB)")
    
    # Reset file pointer
    await file.seek(0)
```

---

## ⚡ Performance Optimization

### **1. Enable Gzip Compression**
```python
# app/main.py
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

### **2. Database Query Optimization**
```python
# Use eager loading to prevent N+1 queries
from sqlalchemy.orm import selectinload

interview = await db.execute(
    select(Interview)
    .options(selectinload(Interview.turns))
    .where(Interview.id == interview_id)
)
```

### **3. Redis Caching**
Already implemented. Verify cache hit rates:
```bash
curl https://interviewme-api-prod.herokuapp.com/health/redis
```

### **4. CDN for Frontend**
Vercel automatically provides CDN. No additional configuration needed.

### **5. WebSocket Connection Pooling**
```python
# app/modules/websocket/connection_manager.py
MAX_CONNECTIONS_PER_USER = 3

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        if len(self.active_connections.get(user_id, [])) >= MAX_CONNECTIONS_PER_USER:
            raise HTTPException(429, "Too many connections")
        ...
```

---

## 🔄 Rollback Strategy

### **1. Heroku Rollback**
```bash
# View release history
heroku releases

# Rollback to previous release
heroku rollback

# Rollback to specific release
heroku rollback v42
```

### **2. Database Rollback**
```bash
# Rollback last migration
heroku run alembic downgrade -1

# Rollback to specific version
heroku run alembic downgrade <revision_id>
```

### **3. Vercel Rollback**
```bash
# View deployments
vercel ls

# Rollback to previous deployment
vercel rollback
```

### **4. Blue-Green Deployment**
```bash
# Create staging app
heroku create interviewme-api-staging

# Deploy to staging first
git push staging main

# Test staging
curl https://interviewme-api-staging.herokuapp.com/health

# If good, promote to production
heroku pipelines:promote -a interviewme-api-staging
```

---

## 📈 Cost Estimation

### **Heroku Costs**
- **Hobby Dyno**: $7/month (1 web dyno)
- **PostgreSQL Essential-0**: $5/month (10M rows, 64GB storage)
- **Total**: ~$12/month

### **Upstash Costs**
- **Free Tier**: 10K commands/day (sufficient for MVP)
- **Pay-as-you-go**: $0.2 per 100K commands

### **Vercel Costs**
- **Hobby Plan**: Free (100GB bandwidth, unlimited deployments)
- **Pro Plan**: $20/month (1TB bandwidth, advanced features)

### **Groq API Costs**
- **Free Tier**: 14,400 requests/day (sufficient for testing)
- **Pay-as-you-go**: $0.05-0.27 per 1M tokens

### **Total Monthly Cost (MVP)**
- **Minimum**: $12/month (Heroku only)
- **Recommended**: $32/month (Heroku + Vercel Pro)

---

## 🎯 Post-Deployment Checklist

- [ ] Health endpoints responding (200 OK)
- [ ] API documentation accessible (`/docs`)
- [ ] Database migrations applied
- [ ] Redis cache working (check `/health/redis`)
- [ ] WebSocket connections working
- [ ] File uploads working (CV/JD)
- [ ] AI interview flow working end-to-end
- [ ] CORS configured correctly
- [ ] SSL/HTTPS working
- [ ] Monitoring alerts configured
- [ ] Backup schedule configured
- [ ] CI/CD pipeline working
- [ ] Error tracking (Sentry) receiving events
- [ ] Performance monitoring active

---

## 🆘 Troubleshooting

### **Application Crashes**
```bash
heroku logs --tail
heroku ps
heroku restart
```

### **Database Connection Issues**
```bash
heroku pg:info
heroku pg:diagnose
heroku config:get DATABASE_URL
```

### **Memory Issues**
```bash
heroku ps:type
heroku dyno:type performance-m  # Upgrade to 2.5GB RAM
```

### **Slow Performance**
```bash
# Check dyno metrics
heroku metrics

# Check database performance
heroku pg:diagnose

# Check Redis cache hit rate
curl https://your-app.herokuapp.com/health/redis
```

---

## 📚 Additional Resources

- [Heroku Python Deployment](https://devcenter.heroku.com/articles/deploying-python)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Vercel Deployment](https://vercel.com/docs/deployments/overview)
- [PostgreSQL Best Practices](https://devcenter.heroku.com/articles/postgresql-best-practices)
- [Upstash Redis Docs](https://docs.upstash.com/redis)

---

**Last Updated**: 2024
**Status**: Production Ready ✅
