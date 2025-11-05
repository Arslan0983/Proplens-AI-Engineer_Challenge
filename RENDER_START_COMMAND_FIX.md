# Fix for "ModuleNotFoundError: No module named 'app'"

## The Problem

Render is trying to run:
```
gunicorn app:app
```

But it should be:
```
gunicorn proplens_challenge.wsgi:application
```

## The Solution

### Option 1: Check Render Dashboard (Most Likely Issue)

1. Go to your Render service dashboard
2. Click on "Settings" tab
3. Scroll to "Start Command" section
4. **Change it to:**
   ```
   gunicorn proplens_challenge.wsgi:application --bind 0.0.0.0:$PORT
   ```
5. Make sure it's NOT set to `gunicorn app:app`
6. Save and redeploy

### Option 2: Verify render.yaml and Procfile

Both files already have the correct command:
- `render.yaml`: `startCommand: gunicorn proplens_challenge.wsgi:application --bind 0.0.0.0:$PORT`
- `Procfile`: `web: gunicorn proplens_challenge.wsgi:application --bind 0.0.0.0:$PORT`

If you're using Render Blueprint (render.yaml), make sure the dashboard settings match.

### Option 3: Delete Procfile if using Blueprint

If you're using `render.yaml` (Blueprint), you can delete the `Procfile` to avoid conflicts. The Blueprint will use the command from `render.yaml`.

## Verification

After fixing, the deployment logs should show:
```
Running 'gunicorn proplens_challenge.wsgi:application --bind 0.0.0.0:$PORT'
```

NOT:
```
Running 'gunicorn app:app'
```

