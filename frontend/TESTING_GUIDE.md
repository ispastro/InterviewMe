# Quick Start Testing Guide

## 🚀 Current Status
- ✅ Frontend: Running on http://localhost:3000 (or http://10.62.86.47:3000)
- ✅ Environment loaded: .env.local
- ✅ Integration: 70% Complete

## 🧪 Test the Integration

### Step 1: Start Backend (if not running)
```bash
# Open new terminal
cd backend
uvicorn app.main:app --reload
```

Backend should be at: http://localhost:8000

### Step 2: Access Frontend
Open browser: http://localhost:3000

### Step 3: Test Authentication Flow

#### Register New User:
1. Click "Sign Up" button
2. Fill in:
   - Name: Test User
   - Email: test@example.com
   - Password: password123
3. Click "Create Account"
4. Should redirect to dashboard

#### Or Login:
1. Click "Log In" button
2. Enter credentials
3. Click "Sign In"

### Step 4: Test Interview Setup

1. From dashboard, click "Start New Interview"
2. Configure settings:
   - Select Job Role
   - Choose Interview Type (Text/Voice)
   - Set Difficulty Level
   - Pick Interview Style
   - Choose Duration
3. Click "Continue to Upload"

### Step 5: Test File Upload

1. Upload CV file (PDF, DOC, or DOCX)
   - Drag and drop OR click to browse
   - File should show with green checkmark
2. Optionally upload Job Description
3. Click "Start Interview"

### Step 6: Check Backend Logs

Backend should show:
```
POST /api/auth/register - 200 OK
POST /api/interviews/create - 200 OK
POST /api/interviews/{id}/upload-cv - 200 OK
```

## 🔍 What to Verify

### ✅ Working Features:
- [ ] User registration
- [ ] User login
- [ ] JWT token stored in localStorage
- [ ] Interview creation
- [ ] File upload (CV)
- [ ] File upload (JD)
- [ ] Navigation flow

### 🚧 Not Yet Integrated:
- [ ] Live interview WebSocket (shows mock data)
- [ ] Dashboard real data (shows mock data)
- [ ] Interview summary (shows mock data)

## 🐛 Troubleshooting

### Backend Not Responding:
```bash
# Check if backend is running
curl http://localhost:8000/health

# Should return: {"status": "healthy"}
```

### CORS Errors:
Check backend `.env` file has:
```
CORS_ORIGINS=["http://localhost:3000"]
```

### Authentication Errors:
1. Open browser DevTools (F12)
2. Go to Console tab
3. Check for error messages
4. Verify token in Application > Local Storage

### File Upload Errors:
1. Check file size (max 10MB for CV, 5MB for JD)
2. Check file type (PDF, DOC, DOCX, TXT)
3. Check backend logs for errors

## 📊 Check Integration Status

### Browser DevTools:
1. Press F12
2. Go to Network tab
3. Try registering/logging in
4. Should see API calls to http://localhost:8000

### LocalStorage:
1. F12 > Application > Local Storage
2. Should see: `interviewme_token` after login

### Backend API Docs:
Visit: http://localhost:8000/docs
- Test endpoints directly
- Verify API is working

## 🎯 Expected Behavior

### After Registration:
- User created in backend database
- JWT token returned
- Token stored in localStorage
- Redirected to dashboard

### After Interview Setup:
- Interview created in backend
- Interview ID returned
- Files uploaded to backend
- AI analysis triggered
- Redirected to live interview page

### Current Limitation:
- Live interview page still uses mock data
- Will be integrated in next phase

## 📝 Next Steps

Once basic flow works:
1. Update live interview page
2. Integrate dashboard with real data
3. Add interview summary page
4. Add protected routes
5. Full end-to-end testing

## 🆘 Need Help?

Check these files:
- `INTEGRATION_SUMMARY.md` - Full integration details
- `INTEGRATION_PROGRESS.md` - Detailed progress tracking
- Backend logs - Error messages
- Browser console - Frontend errors