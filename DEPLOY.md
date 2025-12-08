# Deploying to Railway

## Prerequisites
1. Create a Railway account at https://railway.app
2. Install Railway CLI: `npm install -g @railway/cli`
3. Login: `railway login`

## Quick Deploy (Recommended)

### Step 1: Create a new Railway project
```bash
cd /Users/oem/Desktop/Claude/cocktail-app
railway init
```

### Step 2: Deploy Backend
```bash
cd backend
railway up
```

After deployment, note your backend URL (e.g., `https://cocktail-backend-xxx.railway.app`)

Then set environment variables in Railway dashboard:
- `ANTHROPIC_API_KEY` = your Anthropic API key
- `DATABASE_URL` = sqlite:///./cocktails.db (or add a PostgreSQL plugin for production)

### Step 3: Deploy Frontend
```bash
cd ../frontend
railway up
```

Set the environment variable in Railway dashboard:
- `NEXT_PUBLIC_API_URL` = https://YOUR-BACKEND-URL.railway.app/api

### Step 4: Generate Domain
In Railway dashboard, go to each service → Settings → Generate Domain

---

## Alternative: Deploy from GitHub

1. Push to GitHub:
```bash
cd /Users/oem/Desktop/Claude/cocktail-app
git init
git add .
git commit -m "Initial commit"
git remote add origin YOUR_GITHUB_REPO
git push -u origin main
```

2. In Railway dashboard:
   - New Project → Deploy from GitHub
   - Select your repo
   - Railway will detect both services

3. Configure each service:
   - Set root directory to `backend` or `frontend`
   - Add environment variables

---

## Environment Variables

### Backend
| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key |
| `DATABASE_URL` | Database connection string |

### Frontend
| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_API_URL` | Full URL to backend API (e.g., https://xxx.railway.app/api) |

---

## Production Database (Recommended)

For production, add PostgreSQL:
1. In Railway dashboard, click "New" → "Database" → "PostgreSQL"
2. Copy the `DATABASE_URL` from the PostgreSQL service
3. Set it in your backend service variables

Note: You'll need to update the backend to handle PostgreSQL UUIDs if using Postgres.
