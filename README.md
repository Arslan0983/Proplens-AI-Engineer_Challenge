# Lead Nurturing Workflow with AI Agent

## Project Overview

Built a lead nurturing system that helps sales associates send personalized follow-up messages to CRM leads. The AI agent automatically handles customer responses. It uses RAG to pull info from project brochures and match it with lead data for personalized emails.

## What I Built

### Core Features

1. **Lead Filtering & Shortlisting**
   - Filter leads by project name, budget range, unit type, lead status, or last conversation date
   - Need at least 2 criteria to filter
   - Endpoint: `POST /api/campaigns/filter-leads`

2. **Campaign Management**
   - Create campaigns with project selection, email/WhatsApp channel, and sales offers
   - Generates personalized emails for each lead automatically
   - Endpoints: `POST /api/campaigns`, `GET /api/campaigns`, `GET /api/campaigns/{id}/metrics`

3. **Personalized Email Generation**
   - Pulls together lead data (budget, unit type, status)
   - Uses conversation history, family size, purchase motive
   - Grabs project features from brochures via RAG
   - Generates emails with Google Gemini

4. **AI Agent Response Handling**
   - Figures out what the customer wants (property info, scheduling, or something else)
   - Routes to the right handler:
     - **Property questions**: Uses RAG to find answers from brochures, then nudges toward scheduling
     - **Want to schedule**: Automatically books visit/call and notifies sales
     - **Other stuff**: General response that tries to get them to schedule
   - Endpoint: `POST /api/campaigns/{id}/responses`

5. **Campaign Dashboard & Metrics**
   - Tracks shortlisted leads, messages sent, responses, goals achieved
   - Shows scheduled visits/calls with conversation summaries
   - View full conversation threads

6. **Text-to-SQL (T2SQL)**
   - Query CRM leads in plain English
   - Uses Vanna framework with RAG
   - Reads the database schema automatically (no manual config needed)
   - Endpoint: `POST /api/queries`

7. **Agent Orchestration**
   - Uses LangGraph StateGraph for routing between T2SQL and RAG
   - State management handled by LangGraph
   - Conditional routing based on query intent

8. **Document RAG**
   - Upload project brochures (PDF, DOCX)
   - Semantic search for project info
   - Used for both email generation and answering customer questions
   - Endpoint: `POST /api/documents/upload`

### Tech Stack

- Django Ninja for the API
- LangGraph StateGraph for agent orchestration and state management
- Google Gemini (gemini-2.0-flash-exp) for LLM
- ChromaDB Cloud for vector storage
- SQLite (can switch to PostgreSQL)
- Vanna framework for Text-to-SQL with RAG
- Sentence Transformers for embeddings

**Database Models:**
- `CRMLead` - Lead data (loaded 98 leads from Excel)
- `Campaign` - Campaign settings
- `CampaignLead` - Which leads are in which campaign
- `CampaignMessage` - Message threads (sent/received)
- `ScheduledVisit` - Scheduled visits and calls
- `QueryHistory` - Query logs
- `Document` - Brochure metadata

**Services:**
- `LeadService` - Filtering leads and loading from Excel
- `EmailService` - Generating personalized emails with RAG
- `CustomerResponseHandler` - Handles customer replies
- `VannaService` - Text-to-SQL with auto schema reading
- `DocumentService` - Processing brochures for RAG

## Project Structure

```
api/
├── models.py                    # All database models
├── views.py                     # API endpoints
├── schemas.py                   # Pydantic request/response schemas
├── auth.py                      # JWT authentication
├── agent/
│   └── agent.py                 # T2SQL/RAG router agent
├── services/
│   ├── lead_service.py          # Lead filtering logic
│   ├── email_service.py         # Email generation with RAG
│   ├── response_handler.py      # Customer response handling
│   ├── vanna_service.py         # Text-to-SQL (dynamic schema)
│   └── document_service.py      # Document RAG processing
└── management/commands/
    └── load_crm_leads.py        # Load CRM data from Excel

proplens_challenge/
├── settings.py                  # Django settings
├── urls.py                      # URL routing
└── wsgi.py                      # WSGI config
```

## API Endpoints

### Lead Nurturing
- `POST /api/campaigns/filter-leads` - Filter and shortlist leads
- `POST /api/campaigns` - Create campaign and send emails
- `GET /api/campaigns` - List all campaigns
- `GET /api/campaigns/{id}/metrics` - Campaign dashboard metrics
- `POST /api/campaigns/{id}/responses` - Handle customer response

### Document & Query
- `POST /api/documents/upload` - Upload project brochures
- `POST /api/queries` - Submit query (T2SQL/RAG router)
- `GET /api/health` - Health check
- `GET /api/test-token` - Get test JWT token (for testing)

## Setup & Installation

### 1. Environment Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env and add:
# - GEMINI_API_KEY
# - CHROMADB_API_KEY
# - CHROMADB_TENANT
# - CHROMADB_DATABASE
# - SECRET_KEY
# - JWT_SECRET_KEY
```

### 2. Database Setup

```bash
# Run migrations
python manage.py migrate

# Load CRM leads from Excel
python manage.py load_crm_leads "Mock CRM leads for nurturing.xlsx"
```

### 3. Upload Project Brochures

```bash
# Upload brochures for RAG (repeat for each brochure)
curl -X POST http://localhost:8000/api/documents/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@Project\ brochure\ dataset/BEACHGATE-BY-ADDRESS-EMAAR-BEACHFRONT-BROCHURE.pdf"
```

### 4. Start Server

```bash
python manage.py runserver
```

Visit http://localhost:8000/api/docs for interactive API documentation.

## Usage Examples

### Filter Leads

```bash
curl -X POST http://localhost:8000/api/campaigns/filter-leads \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "project_enquired": "Altura",
    "budget_min": 500000,
    "budget_max": 1000000,
    "unit_types": ["2 bed", "3 bed"]
  }'
```

### Create Campaign

```bash
curl -X POST http://localhost:8000/api/campaigns \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Q1 2025 Campaign",
    "campaign_project": "Lumina Grand",
    "message_channel": "email",
    "sales_offer": "Special 5% discount",
    "lead_ids": [1, 2, 3, 4, 5]
  }'
```

### Query CRM Leads (T2SQL)

```bash
curl -X POST http://localhost:8000/api/queries \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "How many leads have lead_status connected?"}'
```

### Handle Customer Response

```bash
curl -X POST http://localhost:8000/api/campaigns/1/responses \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "lead_id": 1,
    "message": "What are the amenities in this property? I would like to schedule a visit."
  }'
```

## Current Status

### What's Done
- Core features working
- Lead filtering and shortlisting
- Campaign management
- Personalized email generation
- AI agent handles customer responses
- Campaign metrics dashboard
- T2SQL for querying CRM
- Document RAG for brochures
- Loaded 98 leads from Excel

### Still TODO (for production)
- Real email sending (right now it just prints to console)
- WhatsApp integration (code is ready, just needs to be wired up)
- Frontend UI (API is done, just need to build the UI)
- Email webhook for auto-response capture
- Sales associate notifications

## Key Features

### Personalization
- Matches what the lead wants with what the project offers
- References their last conversation
- Uses their family size and why they're buying
- Pulls relevant project info from brochures via RAG

### Auto Schema Reading
- Vanna service reads the database schema on its own
- No need to hardcode table names
- Generates training data from actual tables
- Works with any database structure

### AI Agent
- Figures out what customers want
- Handles back-and-forth conversations
- Keeps context across messages
- Always nudges toward scheduling visits/calls

## Documentation

- **REQUIREMENTS.md** - Complete requirements document
- **DEPLOYMENT.md** - Deployment guide for Render.com
- **API Docs** - http://localhost:8000/api/docs (Swagger UI)

## Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=api
```

## Environment Variables

Required in `.env`:
```
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-2.5-flash
CHROMADB_API_KEY=your-chromadb-api-key
CHROMADB_TENANT=your-chromadb-tenant
CHROMADB_DATABASE=your-database-name
SECRET_KEY=your-django-secret-key
JWT_SECRET_KEY=your-jwt-secret-key
DEBUG=True
```

## Notes

- Email sending is mocked right now (just prints to console). For production, need to hook up SMTP or an email service.
- Using ChromaDB Cloud for storing vectors.
- All personalization happens via RAG + LLM, no template strings.
- T2SQL reads the database schema automatically - no config needed.

