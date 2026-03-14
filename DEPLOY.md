# Deployment Guide

Two options: **Railway** (recommended, easiest) or **Self-hosted** (docker-compose.prod.yml).

---

## Option A — Railway (cloud, free tier available)

Railway deploys each service from a Dockerfile and provides a managed PostgreSQL plugin.

### Step 1 — Push to GitHub

Make sure your latest code is pushed:
```bash
git add -A && git commit -m "production config" && git push
```

### Step 2 — Create a Railway project

1. Go to [railway.app](https://railway.app) and sign in with GitHub
2. Click **New Project → Deploy from GitHub repo → select your repo**
3. Railway will auto-detect the root directory — change the **Root Directory** to `backend`

### Step 3 — Deploy the Backend service

In the backend service settings:

**Build**: Railway detects `backend/Dockerfile` automatically.

Set these **environment variables** (Settings → Variables):
```
SECRET_KEY=<generate: python -c "import secrets; print(secrets.token_hex(32))">
GROQ_API_KEY=gsk_...
LLM_MODEL=llama-3.3-70b-versatile
GMAIL_ADDRESS=you@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
SLACK_BOT_TOKEN=xoxb-...
SLACK_DEFAULT_CHANNEL=U0XXXXXXXXX
FRONTEND_URL=https://<your-frontend-service>.up.railway.app
```

`DATABASE_URL` will be set automatically in Step 4.

### Step 4 — Add PostgreSQL

In your Railway project:
1. Click **+ New → Database → PostgreSQL**
2. In the backend service → Variables, click **Add Reference**
3. Reference `${{Postgres.DATABASE_URL}}` → rename variable to `DATABASE_URL`
4. **Important**: the DATABASE_URL Railway provides uses `postgresql://` — change the scheme to `postgresql+asyncpg://` for async SQLAlchemy:
   ```
   DATABASE_URL=postgresql+asyncpg://...
   ```

### Step 5 — Deploy the Frontend service

1. In your Railway project, click **+ New → GitHub Repo** (same repo again)
2. Set **Root Directory** to `frontend`
3. Set these **environment variables / build variables**:
   ```
   REACT_APP_API_URL=https://<your-backend-service>.up.railway.app
   ```
   > This is a **build-time** variable — it gets baked into the React bundle when Docker builds the image.

4. **Port**: set `PORT=80` (nginx listens on 80)

### Step 6 — Seed the database

After backend is live, open the Railway shell for the backend service (or run locally with the prod DATABASE_URL):

```bash
# From your local machine with prod DATABASE_URL set:
cd backend
DATABASE_URL="postgresql+asyncpg://..." python - <<'EOF'
import asyncio
from app.models.database import init_db, Doctor, Patient
from app.core.security import get_password_hash
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os

engine = create_async_engine(os.environ["DATABASE_URL"])
Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def seed():
    async with Session() as db:
        db.add(Doctor(name="Dr. Smith", email="doctor@demo.com", specialization="General",
                      phone="555-0101", password_hash=get_password_hash("demo123")))
        db.add(Patient(name="Jane Doe", email="patient@demo.com",
                       phone="555-0202", password_hash=get_password_hash("demo123")))
        await db.commit()
        print("Seeded demo users: doctor@demo.com / patient@demo.com (password: demo123)")

asyncio.run(seed())
EOF
```

### Step 7 — Update CORS

Once you know both service URLs:
- Backend → Variables: `FRONTEND_URL=https://yourfrontend.up.railway.app`
- Redeploy backend

---

## Option B — Self-hosted VPS (docker-compose.prod.yml)

### Prerequisites
- A Linux VPS (Ubuntu 22.04+)
- Docker + Docker Compose installed
- Ports 80 and 8000 open in firewall

### Steps

```bash
# 1. SSH into your server and clone the repo
git clone https://github.com/yourusername/doctor-appointment-mcp.git
cd doctor-appointment-mcp

# 2. Create .env.prod from example
cp .env.example .env.prod
nano .env.prod   # fill in all values

# 3. Build and start all services
# Replace YOUR_SERVER_IP with your VPS public IP
REACT_APP_API_URL=http://YOUR_SERVER_IP:8000 \
  docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build

# 4. Check logs
docker compose -f docker-compose.prod.yml logs -f

# 5. Seed the database (first run only)
docker exec -it <backend-container-name> python -c "
import asyncio
from app.models.database import init_db
asyncio.run(init_db())
print('DB initialized')
"
```

Frontend is served on **port 80**, backend API on **port 8000**.

---

## Environment Variables Reference

| Variable | Service | Required | Description |
|---|---|---|---|
| `DATABASE_URL` | Backend | ✅ | PostgreSQL connection string (asyncpg scheme) |
| `SECRET_KEY` | Backend | ✅ | JWT signing key (random 32+ chars) |
| `GROQ_API_KEY` | Backend | ✅ | Groq API key (free at console.groq.com) |
| `LLM_MODEL` | Backend | — | Default: `llama-3.3-70b-versatile` |
| `GMAIL_ADDRESS` | Backend | — | Gmail address for email notifications |
| `GMAIL_APP_PASSWORD` | Backend | — | Gmail App Password (not your main password) |
| `SLACK_BOT_TOKEN` | Backend | — | Slack bot token (`xoxb-...`) |
| `SLACK_DEFAULT_CHANNEL` | Backend | — | Slack channel/user ID for notifications |
| `FRONTEND_URL` | Backend | — | Production frontend URL (for CORS) |
| `REACT_APP_API_URL` | Frontend (build) | ✅ | Backend service public URL |
