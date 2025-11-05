# Deployment Guide

## Deploying to Render.com

### Prerequisites
1. Render.com account (free tier available)
2. GitHub repository with your code (or use Render's direct deployment)

### Step-by-Step Deployment

1. **Create a New Web Service**
   - Log in to Render.com
   - Click "New +" → "Web Service"
   - Connect your repository or use direct deployment

2. **Configure Build Settings**
   - **Name**: `proplens-ai-agent`
   - **Environment**: `Python 3`
   - **Build Command**: 
     ```bash
     pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput
     ```
   - **Start Command**:
     ```bash
     gunicorn proplens_challenge.wsgi:application --bind 0.0.0.0:$PORT
     ```

3. **Set Environment Variables**
   In the Render dashboard, add these environment variables:
   - `GEMINI_API_KEY`: Your Google Gemini API key
   - `SECRET_KEY`: Django secret key (generate a strong one)
   - `JWT_SECRET_KEY`: JWT signing key (can be same as SECRET_KEY)
   - `DEBUG`: `False`
   - `ALLOWED_HOSTS`: `*.onrender.com` (or your specific domain)
   - `PYTHON_VERSION`: `3.11.0`

4. **Optional: Add PostgreSQL Database**
   - Click "New +" → "PostgreSQL"
   - Configure database settings
   - Add connection environment variables to your web service:
     - `DB_NAME`
     - `DB_USER`
     - `DB_PASSWORD`
     - `DB_HOST`
     - `DB_PORT`

5. **Deploy**
   - Click "Create Web Service"
   - Render will build and deploy your application
   - Wait for deployment to complete (usually 5-10 minutes)

6. **Verify Deployment**
   - Visit your service URL (e.g., `https://proplens-ai-agent.onrender.com`)
   - Check health endpoint: `https://your-service.onrender.com/api/health`
   - Test API documentation: `https://your-service.onrender.com/api/docs`

### Using render.yaml (Alternative)

If you have a `render.yaml` file in your repository:
1. Render will automatically detect it
2. You can deploy using Render Blueprint
3. Settings from `render.yaml` will be used

### Post-Deployment

1. **Initialize Database Schema**
   - Access Django shell via Render shell or one-off commands
   - Or wait for first query to auto-initialize

2. **Upload Initial Documents**
   - Use the `/api/documents/upload` endpoint
   - Upload your brochure PDFs

3. **Generate JWT Token**
   - For testing, use the test token generator or create a login endpoint
   - Include token in API requests

### Monitoring

- Check Render dashboard for logs and metrics
- Set up alerts for service downtime
- Monitor API usage and response times

### Troubleshooting

**Build Failures**:
- Check build logs in Render dashboard
- Verify all dependencies are in `requirements.txt`
- Ensure Python version compatibility

**Runtime Errors**:
- Check application logs
- Verify environment variables are set correctly
- Test locally with same configuration

**Database Issues**:
- Ensure database is accessible from Render
- Check connection credentials
- Verify migrations ran successfully

## Alternative Deployment Options

### Heroku
Similar to Render, but requires:
- `Procfile` with: `web: gunicorn proplens_challenge.wsgi:application`
- `runtime.txt` with Python version

### Railway
- Similar setup to Render
- Good for quick deployments

### AWS/GCP/Azure
- More complex setup
- Requires containerization (Docker) or server configuration
- Better for production scale

