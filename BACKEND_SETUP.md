# Backend Setup Troubleshooting

## Quick Start

### Option 1: Use the startup script (Recommended)
```bash
start-backend.bat
```

### Option 2: Manual startup
```bash
cd backend
venv\Scripts\activate
uvicorn main:app --reload
```

## Common Issues

### Issue 1: "uvicorn: command not found" or "No module named uvicorn"

**Cause**: Dependencies not installed in virtual environment

**Fix**:
```bash
cd backend
venv\Scripts\activate
pip install -r requirements.txt
```

If you see errors about Rust/Cargo:
```bash
# Install without the problematic packages first
pip install fastapi uvicorn sqlalchemy psycopg2-binary python-dotenv
pip install pydantic==2.5.3  # Use newer version that has prebuilt wheels
pip install alembic requests beautifulsoup4 lxml pytest python-jose passlib
```

### Issue 2: Virtual environment doesn't exist

**Fix**:
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Issue 3: Port 8000 already in use

**Fix**:
```bash
# Find and kill the process using port 8000
netstat -ano | findstr :8000
taskkill /PID <PID_NUMBER> /F

# Or use a different port
uvicorn main:app --reload --port 8001
```

## Verify Backend is Running

Open in browser or use curl:
- Health check: http://localhost:8000/health
- API docs: http://localhost:8000/docs

Should return:
```json
{"status": "healthy", "version": "0.1.0"}
```

## Environment Variables

Make sure `backend/.env` has:
```
DATABASE_URL=postgresql://postgres:yoyoda00@localhost/cannabis_aggregator
SUPABASE_URL=https://cexurvymsvbmqpigfzuj.supabase.co
SUPABASE_SERVICE_KEY=<your-service-key>
SECRET_KEY=your-secret-key-change-in-production
```

## Database Connection

If you see database errors:
1. Verify PostgreSQL is running
2. Check DATABASE_URL in `.env`
3. Verify database exists: `cannabis_aggregator`
4. Check user/password are correct

## Need Help?

1. Check backend logs for specific errors
2. Ensure Python 3.11+ is installed: `python --version`
3. Make sure all environment variables are set
4. Verify database is accessible
