# Deployment Checklist for Render MVP

## ✅ What's Already Done

- Core API endpoints working
- Database models and migrations
- JWT authentication
- T2SQL and RAG services
- Campaign management
- AI response handling
- Lead filtering
- Email generation (mocked)

## 🔧 Easy to Implement (Before Deployment)

### 1. Generate Secret Keys ✅
- [x] Generated new SECRET_KEY and JWT_SECRET_KEY
- [ ] Add to Render environment variables

### 2. Upload Brochures to ChromaDB
- [ ] Create management command to upload all brochures
- [ ] Upload all 8 brochures from `Project brochure dataset/`
- [ ] Verify brochures are in ChromaDB

### 3. Load CRM Data
- [ ] Run `python manage.py load_crm_leads` after deployment
- [ ] Verify 98 leads are loaded

### 4. Render Configuration
- [ ] Update `render.yaml` with all required env vars
- [ ] Add ChromaDB env vars to Render dashboard
- [ ] Test deployment locally with production settings

## ⚠️ Medium Difficulty (Can Mock for MVP)

### 1. Email Sending
**Current Status**: Mocked (prints to console)
**For MVP**: Keep mocked, add note in API response
**For Production**: Integrate with SendGrid/Mailgun/Resend

### 2. WhatsApp Integration
**Current Status**: API endpoint ready but not implemented
**For MVP**: Return message that WhatsApp coming soon
**For Production**: Integrate with Twilio WhatsApp API

### 3. Sales Associate Notifications
**Current Status**: Not implemented
**For MVP**: Log to console or return in API response
**For Production**: Send actual emails to sales team

## 🚧 Hard to Implement (Post-MVP)

### 1. Email Webhook for Auto-Response Capture
**Why Hard**: Requires email service with webhook support, email parsing, linking responses to campaigns
**Workaround for MVP**: Manual submission via API endpoint

### 2. Frontend UI
**Why Hard**: Full React/Vue app needed, lots of components
**Workaround for MVP**: Use API docs (Swagger UI) for testing

### 3. Real-time Dashboard
**Why Hard**: WebSocket setup, real-time updates
**Workaround for MVP**: Poll metrics endpoint

### 4. Production Email Service
**Why Hard**: Need to handle bounces, unsubscribes, deliverability
**Workaround for MVP**: Mock it

## 📋 Pre-Deployment Tasks

1. **Environment Variables** - Add to Render:
   - `SECRET_KEY` - Generated
   - `JWT_SECRET_KEY` - Generated
   - `GEMINI_API_KEY` - Already have
   - `CHROMADB_API_KEY` - Already have
   - `CHROMADB_TENANT` - Already have
   - `CHROMADB_DATABASE` - Already have
   - `DEBUG=False`
   - `ALLOWED_HOSTS=*.onrender.com`

2. **Upload Brochures** - Run locally or via management command after deployment

3. **Load CRM Data** - Run management command after deployment

4. **Test API Endpoints** - Verify all endpoints work

## 🚀 Deployment Steps

1. Push code to GitHub
2. Connect repo to Render
3. Set environment variables in Render dashboard
4. Deploy service
5. Run migrations (automatic via build command)
6. Load CRM leads via management command
7. Upload brochures via API or management command
8. Test health endpoint
9. Test API docs endpoint

