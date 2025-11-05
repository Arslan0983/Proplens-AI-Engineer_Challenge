# Render Environment Variables Setup Guide

## Important Notes

**NO QUOTES NEEDED** - When adding environment variables in Render dashboard, do NOT use quotes around the values.

## How to Add Variables in Render

1. Go to your Render service dashboard
2. Click on "Environment" tab (left sidebar)
3. Click "Add Environment Variable" button
4. For each variable:
   - **Key**: Copy the variable name (left side of =)
   - **Value**: Copy the value (right side of =) - **NO QUOTES**
   - Click "Save"

## Variables to Add

Copy and paste these one by one:

### Required Variables

```
SECRET_KEY
KdSSpUq_ypRCEEPo2nnG9vm8rF4fe9qTCUlzpZ42JU_doWMqa0R2NKKawzVeEnrtX9A
```

```
JWT_SECRET_KEY
7ZljtGsrQAzwGxJbmHyVdUN-yldpu2-wmhPcaFrBF4ndqyWaiWzMZ-jOqQmS8_G8HzQ
```

```
GEMINI_API_KEY
AIzaSyB43agBEzT3XZYV8ESbm-4lWGR4DAeg1AE
```
**Note:** Replace with your actual Gemini API key if different

```
GEMINI_MODEL
gemini-2.5-flash
```

```
CHROMADB_API_KEY
ck-C7LdZaLqEN17n7yM8CZMQpzDgmaVLSidaYMjtbCgf1nC
```

```
CHROMADB_TENANT
f8d5c705-25b3-4306-99f4-40fdd4212e2b
```

```
CHROMADB_DATABASE
test_database
```

```
EMBEDDING_MODEL
all-MiniLM-L6-v2
```

```
DEBUG
False
```

```
ALLOWED_HOSTS
*.onrender.com
```

```
PYTHON_VERSION
3.11.0
```

## Example in Render Dashboard

When you add a variable, it should look like this:

**Key field:**
```
GEMINI_API_KEY
```

**Value field:**
```
AIzaSyB43agBEzT3XZYV8ESbm-4lWGR4DAeg1AE
```

**NOT like this:**
```
"AIzaSyB43agBEzT3XZYV8ESbm-4lWGR4DAeg1AE"
```

## After Adding Variables

1. Save all variables
2. Render will automatically redeploy if the service is already running
3. Check the build logs to ensure everything works

