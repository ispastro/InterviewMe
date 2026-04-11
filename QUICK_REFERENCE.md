# 🚀 Quick Reference - Deployment Commands

## 📦 One-Command Deployment

### Windows
```powershell
.\deploy.ps1
```

### Linux/Mac
```bash
chmod +x deploy.sh && ./deploy.sh
```

---

## 🔧 Manual Heroku Commands

### Initial Setup
```bash
# Login
heroku login

# Create app
heroku create interviewme-api-prod

# Add PostgreSQL
heroku addons:create heroku-postgresql:essential-0

# Set environment variables
heroku config:set ENVIRONMENT=production
heroku config:set JWT_SECRET=$(openssl rand -hex 32)
heroku config:set GROQ_API_KEY=your_key_here
heroku config:set CORS_ORIGINS='["https://your-frontend.vercel.app"]'
```

### Deploy
```bash
# Add remote
heroku git:remote -a interviewme-api-prod

# Push code
git push heroku main

# Run migrations
heroku run alembic upgrade head

# Scale dynos
heroku ps:scale web=1
```

### Monitoring
```bash
# View logs
heroku logs --tail

# Check status
heroku ps

# Check config
heroku config

# Check database
heroku pg:info
```

---

## 🌐 Vercel Commands

### Deploy
```bash
# Login
vercel login

# Deploy to production
cd frontend && vercel --prod
```

### Environment Variables
```bash
# Set via CLI
vercel env add NEXT_PUBLIC_API_URL production

# Or via dashboard
# https://vercel.com/dashboard → Project → Settings → Environment Variables
```

---

## 🐳 Docker Commands

### Local Development
```bash
# Start all services
docker-compose up

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Build & Run
```bash
# Build backend
cd backend && docker build -t interviewme-backend .

# Run backend
docker run -p 8000:8000 --env-file .env interviewme-backend

# Build frontend
cd frontend && docker build -t interviewme-frontend .

# Run frontend
docker run -p 3000:3000 interviewme-frontend
```

---

## 🧪 Testing Commands

### Backend Tests
```bash
cd backend

# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_models_interview.py -v

# Production validation
python production_validation.py

# Coverage report
pytest --cov=app tests/
```

### Frontend Tests
```bash
cd frontend

# Build test
npm run build

# Type check
npm run type-check

# Lint
npm run lint
```

---

## 🔍 Health Check URLs

### Backend
```
https://your-app.herokuapp.com/health
https://your-app.herokuapp.com/health/ready
https://your-app.herokuapp.com/health/redis
https://your-app.herokuapp.com/docs
```

### Frontend
```
https://your-app.vercel.app
```

---

## 🔄 Rollback Commands

### Heroku
```bash
# View releases
heroku releases

# Rollback to previous
heroku rollback

# Rollback to specific version
heroku rollback v42
```

### Database
```bash
# Rollback migration
heroku run alembic downgrade -1

# Restore backup
heroku pg:backups:restore b001 DATABASE_URL
```

### Vercel
```bash
# View deployments
vercel ls

# Rollback
vercel rollback
```

---

## 📊 Monitoring Commands

### Heroku Metrics
```bash
# View metrics
heroku metrics

# Database metrics
heroku pg:diagnose

# Dyno usage
heroku ps:type
```

### Database Backups
```bash
# Schedule backups
heroku pg:backups:schedule DATABASE_URL --at '02:00 America/Los_Angeles'

# Manual backup
heroku pg:backups:capture

# Download backup
heroku pg:backups:download

# List backups
heroku pg:backups
```

---

## 🔐 Security Commands

### Generate Secrets
```bash
# JWT Secret (64 chars)
openssl rand -hex 32

# Random password
openssl rand -base64 32
```

### Check Security
```bash
# Check for secrets in code
git secrets --scan

# Check dependencies
pip-audit
npm audit
```

---

## 💰 Cost Monitoring

### Heroku
```bash
# View current usage
heroku ps:type

# View addons
heroku addons

# View billing
heroku billing
```

### Check API Usage
```bash
# Groq API usage
# Visit: https://console.groq.com/usage

# Upstash Redis usage
# Visit: https://console.upstash.com
```

---

## 🆘 Emergency Commands

### Backend Down
```bash
# Restart dynos
heroku restart

# Scale up
heroku ps:scale web=2

# Check logs
heroku logs --tail --source app
```

### Database Issues
```bash
# Check connections
heroku pg:ps

# Kill connections
heroku pg:killall

# Reset database (DANGER!)
heroku pg:reset DATABASE_URL
```

### Clear Cache
```bash
# Clear Redis cache
# Use /health/redis endpoint or Upstash console
```

---

## 📝 Git Commands

### Deployment
```bash
# Check status
git status

# Commit changes
git add .
git commit -m "Deploy: production ready"

# Push to GitHub
git push origin main

# Push to Heroku
git push heroku main
```

### Branches
```bash
# Create feature branch
git checkout -b feature/new-feature

# Deploy specific branch
git push heroku feature-branch:main
```

---

## 🔗 Useful URLs

### Documentation
- Heroku: https://devcenter.heroku.com
- Vercel: https://vercel.com/docs
- FastAPI: https://fastapi.tiangolo.com
- Next.js: https://nextjs.org/docs

### Dashboards
- Heroku: https://dashboard.heroku.com
- Vercel: https://vercel.com/dashboard
- Groq: https://console.groq.com
- Upstash: https://console.upstash.com

### Monitoring
- Sentry: https://sentry.io
- UptimeRobot: https://uptimerobot.com
- New Relic: https://newrelic.com

---

## 💡 Pro Tips

1. **Always test locally before deploying**
   ```bash
   pytest tests/ -v && python production_validation.py
   ```

2. **Use staging environment**
   ```bash
   heroku create interviewme-api-staging
   git push staging main
   ```

3. **Monitor logs during deployment**
   ```bash
   heroku logs --tail -a interviewme-api-prod
   ```

4. **Set up automatic backups**
   ```bash
   heroku pg:backups:schedule DATABASE_URL --at '02:00'
   ```

5. **Use environment-specific configs**
   ```bash
   heroku config:set ENVIRONMENT=production
   ```

---

**Quick Help**: For detailed guides, see `DEPLOYMENT_GUIDE.md` and `DEPLOYMENT_CHECKLIST.md`
