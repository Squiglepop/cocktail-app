# Deploying Cocktail Recipe Library to Railway

A complete step-by-step guide to deploying this application to Railway, written for beginners.

## Table of Contents
1. [Deployment Options](#deployment-options)
2. [What You'll Need](#what-youll-need)
3. [Getting Your API Keys](#getting-your-api-keys)
4. [Option A: Deploy with Claude Code (Recommended)](#option-a-deploy-with-claude-code-recommended)
5. [Option B: Manual Deployment](#option-b-manual-deployment)
6. [Troubleshooting](#troubleshooting)

---

## Deployment Options

You have two ways to deploy this application:

| Option | Time | Difficulty | What Claude Can Do |
|--------|------|------------|-------------------|
| **A. Claude Code** | ~10 min | Easy | Automates GitHub setup, generates keys, guides Railway config |
| **B. Manual** | ~25 min | Medium | You do everything yourself |

**Recommendation:** Use Claude Code (Option A) if you have it installed. It automates the tedious parts and walks you through the rest.

---

## What You'll Need

Before starting, you'll need accounts on these services:

| Service | What It's For | Sign Up |
|---------|---------------|---------|
| **GitHub** | Hosts your code | [github.com/signup](https://github.com/signup) |
| **Anthropic** | AI recipe extraction | [console.anthropic.com](https://console.anthropic.com/) |
| **Railway** | Hosts your app | [railway.app](https://railway.app) |

**Cost estimates:**
- Railway: ~$3-8/month (free tier includes $5/month credit)
- Anthropic: ~$0.01-0.05 per recipe extraction (new accounts get free credits)

---

## Getting Your API Keys

### Anthropic API Key

You'll need this regardless of which deployment option you choose.

1. Go to [console.anthropic.com](https://console.anthropic.com/)
2. Sign up or log in
3. Click **"Get API Keys"** in the left sidebar
4. Click **"Create Key"**
5. Name it "cocktail-app"
6. **Copy the key immediately** (starts with `sk-ant-`) - you won't see it again!

**Keep this key safe** - you'll need it during deployment.

---

## Option A: Deploy with Claude Code (Recommended)

Claude Code can automate most of the deployment process. Here's what it can and cannot do:

### What Claude Can Automate

| Task | Automated? | Notes |
|------|-----------|-------|
| Generate SECRET_KEY | Yes | Claude runs the Python command |
| Create GitHub repo | Yes | Using `gh` CLI if authenticated |
| Push code to GitHub | Yes | Commits and pushes automatically |
| Generate commands | Yes | Provides exact commands to run |
| Guide Railway setup | Partial | Tells you exactly what to click |

### What Requires Manual Steps

| Task | Why Manual? |
|------|-------------|
| Get Anthropic API key | Requires your Anthropic account login |
| Railway account creation | Requires browser authentication |
| Railway UI configuration | No API/CLI for service creation |
| Setting environment variables | Done in Railway dashboard |

### Start a Deployment Session

Copy and paste this prompt into Claude Code to begin:

```
I want to deploy the cocktail-app to Railway. Please help me through the process:

1. First, generate a SECRET_KEY for me
2. Check if I have the GitHub CLI installed and authenticated
3. Help me create a GitHub repository and push the code
4. Walk me through the Railway setup step-by-step

I already have:
- [ ] Anthropic API key (I'll paste it when needed: ________________)
- [ ] Railway account created

Please start by generating the SECRET_KEY and checking my GitHub CLI status.
```

### What to Expect

Claude will:

1. **Generate your SECRET_KEY** by running:
   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
   Save this output!

2. **Check GitHub CLI** and help you authenticate if needed:
   ```bash
   gh auth status
   ```

3. **Create and push to GitHub**:
   ```bash
   cd /path/to/cocktail-app
   gh repo create cocktail-app --private --source=. --push
   ```

4. **Guide you through Railway** with specific instructions like:
   > "Now go to railway.app/dashboard and click 'New Project' → 'Deploy from GitHub repo' → Select 'cocktail-app'"

5. **Tell you exactly what environment variables to set** and where.

### Quick Deployment Prompt (Experienced Users)

If you're comfortable with the process, use this shorter prompt:

```
Deploy cocktail-app to Railway. I have my Anthropic key ready.
Generate a SECRET_KEY, push to GitHub, and give me the Railway
configuration steps with all environment variables I need to set.
```

---

## Option B: Manual Deployment

If you prefer to do everything yourself, or don't have Claude Code.

### Step 1: Generate a Secret Key

Run this command in your terminal:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Save the output - you'll need it later.

### Step 2: Push Code to GitHub

1. Go to [github.com/new](https://github.com/new)
2. Name your repository `cocktail-app`
3. Keep it **Private** if you prefer
4. Click **"Create repository"**
5. Run these commands:

```bash
cd /path/to/cocktail-app
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/cocktail-app.git
git push -u origin main
```

### Step 3: Create Railway Project

1. Go to [railway.app/dashboard](https://railway.app/dashboard)
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Find and select your `cocktail-app` repository

### Step 4: Add PostgreSQL Database

1. In your Railway project, click **"New"** (+ button)
2. Select **"Database"** → **"Add PostgreSQL"**
3. Wait for it to provision (~30 seconds)

### Step 5: Deploy Backend

1. Click **"New"** → **"GitHub Repo"** → Select your repo
2. Go to **"Settings"** tab:
   - Set **Root Directory** to `backend`
   - Click **"Generate Domain"**
3. Go to **"Variables"** tab and add:

| Variable | Value |
|----------|-------|
| `ANTHROPIC_API_KEY` | Your key from Anthropic (sk-ant-...) |
| `SECRET_KEY` | The key you generated in Step 1 |
| `DATABASE_URL` | Click "Add Reference" → PostgreSQL → DATABASE_URL |
| `CORS_ORIGINS` | (leave empty for now) |

### Step 6: Deploy Frontend

1. Click **"New"** → **"GitHub Repo"** → Select your repo
2. Go to **"Settings"** tab:
   - Set **Root Directory** to `frontend`
   - Click **"Generate Domain"** (note this URL!)
3. Go to **"Variables"** tab and add:

| Variable | Value |
|----------|-------|
| `NEXT_PUBLIC_API_URL` | Your backend URL (e.g., `https://xxx.up.railway.app`) |

### Step 7: Update CORS Settings

1. Go back to your **backend service**
2. Go to **"Variables"** tab
3. Set `CORS_ORIGINS` to your frontend URL:
   ```
   https://your-frontend-xxx.up.railway.app
   ```

### Step 8: Verify

1. Wait for both services to show green "Deployed" status
2. Open your frontend URL
3. Try uploading a cocktail recipe image!

---

## Environment Variables Reference

| Variable | Service | Required | Description |
|----------|---------|----------|-------------|
| `ANTHROPIC_API_KEY` | Backend | Yes | From [Anthropic Console](https://console.anthropic.com/) |
| `SECRET_KEY` | Backend | Yes | Generate with Python (see above) |
| `DATABASE_URL` | Backend | Yes | Auto-linked from Railway PostgreSQL |
| `CORS_ORIGINS` | Backend | Yes | Your frontend Railway URL |
| `NEXT_PUBLIC_API_URL` | Frontend | Yes | Your backend Railway URL |

---

## Troubleshooting

### Backend won't start / "Missing required environment variables"

1. Go to backend service → Variables tab
2. Verify all 4 variables are set (not empty)
3. Check `DATABASE_URL` is linked via "Add Reference" (not copy-pasted)

### "CORS error" in browser

1. `CORS_ORIGINS` must exactly match your frontend URL
2. Include `https://`, no trailing slash

### Frontend can't connect to API

1. `NEXT_PUBLIC_API_URL` should be your backend URL
2. Don't include `/api` at the end

### Database errors

1. Check PostgreSQL service is running (green status)
2. Try redeploying the backend

### How to view logs

1. Click on any service → **"Deployments"** tab
2. Click latest deployment → **"View Logs"**

---

## Claude Code Troubleshooting Prompt

If you run into issues during deployment, use this prompt:

```
I'm having trouble deploying cocktail-app to Railway. Here's what's happening:

[Describe the error or issue]

My current setup:
- Backend URL: [your backend URL]
- Frontend URL: [your frontend URL]
- Error message: [paste any error]

Please help me diagnose and fix this issue.
```

---

## Post-Deployment

Once deployed successfully:

- **Custom domain**: Service Settings → Domains → Add custom domain
- **Monitor usage**: Railway dashboard shows resource metrics
- **View logs**: Deployments tab → View Logs

---

## Getting Help

- **Railway docs**: [docs.railway.app](https://docs.railway.app)
- **Railway Discord**: [discord.gg/railway](https://discord.gg/railway)
- **Anthropic docs**: [docs.anthropic.com](https://docs.anthropic.com)
