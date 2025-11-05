# How to Redeploy on Render

## Step 1: Fix the Start Command (IMPORTANT!)

Before redeploying, you MUST fix the start command in Render dashboard:

1. Go to https://dashboard.render.com
2. Click on your service: `proplens-ai-agent`
3. Click **"Settings"** tab (left sidebar)
4. Scroll down to **"Start Command"** section
5. **Delete or change** the current command (if it says `gunicorn app:app`)
6. **Set it to:**
   ```
   gunicorn proplens_challenge.wsgi:application --bind 0.0.0.0:$PORT
   ```
7. Click **"Save Changes"**

## Step 2: Trigger a New Deployment

### Option A: Manual Redeploy (Fastest)
1. In your Render dashboard, go to your service
2. Click the **"Manual Deploy"** button (top right)
3. Select **"Deploy latest commit"**
4. Click **"Deploy"**

### Option B: Push a New Commit (Auto-deploy)
1. Make any small change (like updating a comment)
2. Commit and push:
   ```bash
   git commit --allow-empty -m "Trigger redeploy"
   git push origin master
   ```
3. Render will automatically detect the push and start a new deployment

### Option C: Use Render CLI
```bash
# Install Render CLI first
npm install -g render-cli

# Login
render login

# Deploy
render deploy
```

## Step 3: Monitor the Deployment

1. Watch the **"Events"** tab in Render dashboard
2. Check the **"Logs"** tab for real-time build logs
3. Wait for build to complete (usually 5-10 minutes)

## Step 4: Verify It Works

After deployment succeeds:
1. Visit your service URL: `https://proplens-ai-agent.onrender.com`
2. Check API docs: `https://proplens-ai-agent.onrender.com/api/docs`
3. Test health endpoint: `https://proplens-ai-agent.onrender.com/api/health`

## Troubleshooting

If deployment still fails:
- Check the **Logs** tab for error messages
- Verify environment variables are set correctly
- Make sure start command is exactly: `gunicorn proplens_challenge.wsgi:application --bind 0.0.0.0:$PORT`
- Check that all dependencies installed successfully

