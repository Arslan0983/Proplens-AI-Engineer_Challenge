# PostgreSQL Cloud Setup Guide

## Option 1: Using Render Dashboard (Recommended)

### Step 1: Create PostgreSQL Database on Render

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **"New +"** → **"PostgreSQL"**
3. Configure:
   - **Name**: `proplens-postgres`
   - **Database**: `proplens_db`
   - **User**: `proplens_user`
   - **Plan**: Free (or paid if needed)
   - **Region**: Choose closest to you
4. Click **"Create Database"**

### Step 2: Link Database to Web Service

1. Go to your **Web Service** (`proplens-ai-agent`)
2. Go to **"Environment"** tab
3. Scroll down to **"Add Environment Variable"**
4. Render automatically creates `DATABASE_URL` when you link the database:
   - Click **"Link Database"** button
   - Select `proplens-postgres`
   - Render will automatically add `DATABASE_URL` environment variable

### Step 3: Redeploy

1. Go to **"Manual Deploy"** → **"Clear build cache & deploy"**
2. Wait for deployment to complete

## Option 2: Using render.yaml (Already Configured)

The `render.yaml` file already includes PostgreSQL configuration. When you deploy via Blueprint:

1. Render will automatically create the PostgreSQL database
2. The `DATABASE_URL` will be automatically set
3. Django will automatically use PostgreSQL

## Verify PostgreSQL is Working

After deployment, check logs:
```bash
# Should see: "Using PostgreSQL database"
# Should NOT see: "Using SQLite database"
```

## Load Data to PostgreSQL

After deployment, you'll need to load your CRM leads:

1. **Option A**: Use Django shell on Render (via SSH)
2. **Option B**: Create an admin endpoint to load data
3. **Option C**: Use Django management command via Render shell

### Using Render Shell:

1. Go to your Web Service on Render
2. Click **"Shell"** tab
3. Run:
```bash
python manage.py load_crm_leads "Mock CRM leads for nurturing.xlsx"
python manage.py upload_brochures --folder "Project brochure dataset/"
```

## Local Development with PostgreSQL

If you want to test PostgreSQL locally:

1. Install PostgreSQL locally or use Docker:
```bash
docker run --name postgres-proplens -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=proplens_db -p 5432:5432 -d postgres:15
```

2. Set environment variable:
```bash
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/proplens_db"
```

3. Run migrations:
```bash
python manage.py migrate
```

4. Load data:
```bash
python manage.py load_crm_leads "Mock CRM leads for nurturing.xlsx"
```

