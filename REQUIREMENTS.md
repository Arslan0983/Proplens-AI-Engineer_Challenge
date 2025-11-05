# Lead Nurturing Workflow with AI Agent - Complete Requirements

## Project Overview

Property Sales associates need an efficient way to send personalized follow-ups to leads stored in the CRM. This system enables automated, context-aware emails or WhatsApp messages, leveraging past enquiry data from the CRM for hyper-personalization.

**Goal**: Revive past customer leads from the existing CRM/database for ongoing sales campaigns and convert them into property visits for target real estate projects.

## Core Capabilities Required

### 1. Lead Filtering & Shortlisting ✅
**What**: Sales associate can filter and shortlist leads from CRM based on multiple criteria.

**Criteria Options**:
- **Last conversation date** (From date and To date) - Up to past 3 years
- **Project name enquired** - Dropdown with options:
  - Altura
  - Beachgate by Address
  - Damac Bay by Cavalli
  - DLF West Park
  - Godrej Vistas
  - Lumina Grand
  - Sobha Crest
  - Sobha Waves
- **Budget range** - Min and Max budget fields (custom numbers)
- **Unit type** - Multi-select checkbox dropdown:
  - Studio
  - 1 bed
  - 2 bed
  - 2 bed w study
  - 3 bed
  - 4 bed
  - Duplex
  - Penthouse
- **Lead status** - Dropdown:
  - Not Connected
  - Connected
  - Visit scheduled
  - Visit done not purchased
  - Purchased
  - Not interested

**Validation**: At least 2 of the 5 filter fields must be selected.

**Output**: System displays the number of leads matching the selected filters.

### 2. Campaign Message Customization ✅
**What**: Sales associate can configure the campaign message settings.

**Configuration Options**:
- **Campaign project name** - Dropdown (same list as project name enquired)
- **Nurturing message channel** - Dropdown:
  - Email
  - WhatsApp
- **Sales offer details** - Open text field (optional)

**Note**: Offer details (if provided) should be included in all messages just prior to the call-to-action.

### 3. Automated Follow-Up Message Sending ✅
**What**: System automatically sends personalized follow-up messages to all shortlisted leads.

**Process**:
1. Sales associate selects leads using filters
2. Configures campaign settings (project, channel, offer)
3. System generates hyper-personalized messages for each lead
4. Messages are automatically dispatched via Email/WhatsApp
5. No manual intervention required after triggering

**Personalization Based On**:
- Lead's past structured data (budget, unit type, status, etc.)
- Lead's qualitative data:
  - Last conversation summary
  - Family size
  - Unit type preferences
  - Purchase motive
  - Intent
  - Financing options
  - Location preference
- Project features from brochures (retrieved via RAG)
- Campaign sales offer

**Key Requirement**: The message must match customer information (including 'last conversation summary') with the project features of the campaign project being marketed.

### 4. Customer Response Handling (AI Agent) ✅
**What**: AI agent automatically responds to customer replies to nurturing messages.

**Response Scenarios**:
- **Intent: Property Information** - Customer asks questions about property features, amenities, etc.
  - Agent retrieves relevant information from project brochures (RAG)
  - Provides accurate answer
  - Nudges customer toward goal (scheduling visit/call)
  
- **Intent: Schedule Visit/Call** - Customer wants to schedule property viewing or sales call
  - Agent automatically schedules the visit/call
  - Sends confirmation to customer
  - Notifies sales associate via email
  
- **Intent: Other Questions** - General inquiries
  - Agent responds appropriately
  - Builds urgency
  - Nudges customer toward scheduling

**Conversation Management**:
- Multiple conversation turns supported
- Context-aware responses
- Full conversation thread saved

### 5. Visit/Call Scheduling ✅
**What**: When customer agrees to schedule a property visit or sales call.

**Process**:
1. AI agent detects scheduling intent
2. Automatically schedules visit/call
3. Sends confirmation to customer
4. Notifies designated sales associate's email ID

**Tracking**:
- Visit/call type (property visit or sales call)
- Scheduled date and time
- Lead information
- Conversation summary

### 6. Campaign Dashboard & Metrics ✅
**What**: Central dashboard showing campaign performance metrics.

**Dashboard Sections**:

**Section 1: Campaign Selection**
- Dropdown to select campaign (e.g., "Nurturing Campaign 1", "Nurturing Campaign 2", "Nurturing Campaign 3")

**Section 2: Key Metrics (Displayed in boxes)**
- **No. of leads shortlisted** from CRM as per criteria
- **No. of messages sent**
- **No. of unique leads responded**
- **No. of unique leads for which goal is achieved** (visit/call scheduled)

**Section 3: Goal Achievements (Property Visit/Call Scheduled)**
- List of all leads with:
  - Lead name
  - Contact details (email, phone)
  - Summary of last nurturing conversation
  - Date of proposed viewing/call

**Section 4: Follow-ups**
- View conversation threads between AI agent and customers
- Select a specific customer (lead) name
- Expand to see full conversation thread in pop-up

## User Stories & Acceptance Criteria

### User Story 1: Shortlist Leads for Follow-Up ✅
**As a** sales associate,  
**I want to** filter existing leads from the CRM based on specific criteria  
**So that** I can target the right audience for personalized follow-ups.

**Acceptance Criteria**:
- ✅ Can select leads based on last conversation date (From/To date picker)
- ✅ Can select leads based on project name enquired (dropdown)
- ✅ Can select leads based on budget range (min/max fields)
- ✅ Can select leads based on unit type (multi-select)
- ✅ Can select leads based on lead status (dropdown)
- ✅ All filter fields are optional
- ✅ At least 2 of 5 fields must be selected
- ✅ System displays number of matching leads after clicking "Shortlist leads"

### User Story 2: Customize Follow-Up Message ✅
**As a** sales associate,  
**I want to** personalize the follow-up message  
**So that** it aligns with the lead's past inquiry and highlights relevant offers.

**Acceptance Criteria**:
- ✅ Can input campaign project name (dropdown)
- ✅ Can select nurturing message channel (Email/WhatsApp dropdown)
- ✅ Can input sales offer details (open text field)
- ✅ Offer details (if provided) included in all messages just before call-to-action

### User Story 3: Send Automated Follow-Up Messages ✅
**As a** sales associate,  
**I want** the system to send personalized follow-up messages automatically  
**So that** I don't have to send them manually.

**Acceptance Criteria**:
- ✅ Upon submission, system sends messages to all shortlisted leads via Email/WhatsApp
- ✅ Messages are personalized based on:
  - Selected campaign project features (from brochures via RAG)
  - Past lead details from CRM (structured + qualitative)
- ✅ No manual intervention required after triggering

### User Story 4: Track Agent Replies to Responding Customers ✅
**As a** sales associate,  
**I want to** track all AI agent responses to customers responding to nurturing messages  
**So that** I can monitor conversations and follow up when needed.

**Acceptance Criteria**:
- ✅ Any reply to email follow-up is captured in Campaign screen under 'Followups' section
- ✅ Can select specific customer (lead) name
- ✅ Can expand to see full conversation thread between AI agent and customer in pop-up

## Technical Requirements

### Foundation Framework (From Initial Requirements)
- ✅ Django Ninja RESTful API
- ✅ LangGraph-style agent orchestration
- ✅ JWT Authentication
- ✅ ChromaDB Cloud for vector storage
- ✅ Google Gemini LLM

### Text-to-SQL (T2SQL) Capability
- ✅ Must use Vanna framework approach with RAG
- ✅ ChromaDB as vector store for training data (DDL, documentation, SQL examples)
- ✅ Agent must interpret natural language queries into SQL
- ✅ Execute SQL against relational database
- ✅ Return meaningful natural language responses
- ✅ Sample schema and data sufficient for demonstration

### Document RAG Capability
- ✅ Process brochure documents (PDF, DOCX)
- ✅ Store in ChromaDB vector store
- ✅ Semantic search against brochure vectors
- ✅ Retrieve most relevant text chunks
- ✅ Use LLM to synthesize accurate answers

### Document Ingestion API
- ✅ Dedicated upload endpoint for brochure documents
- ✅ Pipeline:
  1. File upload acceptance
  2. Chunking/Splitting (recursive text splitting)
  3. Embedding (using documented embedding model)
  4. Storage in ChromaDB (vectors, chunks, metadata)
- ✅ Clear documentation on usage

## UI Screens (For Reference)

### Section 1: Campaign Creation

**Screen 1: Shortlist Leads for Campaign**
- Filter fields:
  - Project name enquired (dropdown)
  - Budget range (min/max fields)
  - Unit type (multi-select checkboxes)
  - Lead status (dropdown)
  - Last conversation date (From/To date pickers)
- "Shortlist leads" button
- Display: Number of matching leads

**Screen 2: Set Campaign Messaging**
- Campaign project name (dropdown)
- Nurturing message channel (Email/WhatsApp dropdown)
- Sales offer details (text field)

### Section 2: Campaign Dashboards

**Screen 3: Nurturing Campaign Metrics**
- Campaign name dropdown (top of screen)
- Key metrics boxes:
  - Leads shortlisted
  - Messages sent
  - Leads responded
  - Goals achieved
- Property visit/Call scheduled section:
  - List of leads with:
    - Name
    - Contact details
    - Conversation summary
    - Proposed viewing/call date
- Followups section:
  - Select customer name
  - Expand to view conversation thread

## Implementation Status

### ✅ Completed Features
1. ✅ Lead filtering API with all 5 criteria
2. ✅ Campaign creation and management
3. ✅ Hyper-personalized email generation (using RAG + lead data)
4. ✅ AI agent for customer response handling
5. ✅ Intent analysis (property info, schedule visit/call, other)
6. ✅ Automatic visit/call scheduling
7. ✅ Campaign metrics dashboard API
8. ✅ Conversation thread management
9. ✅ T2SQL capability for querying CRM leads
10. ✅ Document RAG for project brochures
11. ✅ CRM data loading from Excel

### ⏳ Pending (For Production)
1. ⏳ Actual email sending (currently mocked)
2. ⏳ WhatsApp integration (API endpoint ready, needs implementation)
3. ⏳ Frontend UI (API endpoints ready)
4. ⏳ Email webhook for automatic response capture
5. ⏳ Sales associate notification system

## API Endpoints Summary

### Lead Management
- `POST /api/campaigns/filter-leads` - Filter and shortlist leads

### Campaign Management
- `POST /api/campaigns` - Create campaign and send emails
- `GET /api/campaigns` - List all campaigns
- `GET /api/campaigns/{id}/metrics` - Get campaign dashboard metrics

### Customer Interaction
- `POST /api/campaigns/{id}/responses` - Handle customer response (AI agent)

### Document Management
- `POST /api/documents/upload` - Upload project brochures

### Query System (T2SQL/RAG Router)
- `POST /api/queries` - Submit query (routes to T2SQL or RAG automatically)

## Data Flow Summary

### Campaign Creation Flow
```
1. Filter Leads (POST /api/campaigns/filter-leads)
   ↓
2. Create Campaign (POST /api/campaigns)
   ↓
3. Generate Personalized Emails (RAG + Lead Data + LLM)
   ↓
4. Send Messages (Email/WhatsApp)
   ↓
5. Track Metrics (Dashboard)
```

### Customer Response Flow
```
1. Customer Responds to Email
   ↓
2. Submit Response (POST /api/campaigns/{id}/responses)
   ↓
3. AI Agent Analyzes Intent
   ↓
4a. Property Info → RAG Retrieval → Answer + Nudge
4b. Schedule Visit → Auto-Schedule → Notify Sales
4c. Other → General Response + Nudge
   ↓
5. Update Campaign Metrics
```

## Key Technical Decisions

1. **Hyper-Personalization**: Combines structured CRM data + qualitative data (last conversation summary) + project brochure features (RAG) + LLM generation
2. **Intent Analysis**: Keyword-based + LLM reasoning for accurate routing
3. **Dynamic Schema**: Vanna reads actual database schema, no hardcoded tables
4. **RAG Integration**: Project features retrieved from brochures for both email generation and customer responses
5. **Goal-Oriented**: System always nudges toward scheduling property visits/calls

## Testing Requirements

### Minimum Solution (For Challenge)
1. ✅ Shortlist leads based on criteria
2. ✅ Generate hyper-personalized message
3. ✅ Send message over email (mock email ID for demonstration)
4. ✅ AI agent ability to respond to customer response
5. ✅ Sample customer response: "What are the facilities and amenities in this property?"
6. ✅ Agent responds based on project brochure data

### Data Sources
- ✅ Mock CRM leads from Excel file
- ✅ Project brochure dataset folder (PDFs)

## Notes

1. **AI Tools**: Developer can use any AI tool, must document clearly
2. **Minimal Solution**: Should involve shortlisting, message generation, email sending (mock), and response handling
3. **Project Brochures**: Use project brochure dataset folder as ground truth
4. **Pricing**: Can use placeholder pricing if needed

## Success Criteria

✅ System can filter leads based on multiple criteria  
✅ System generates hyper-personalized emails using RAG + lead data  
✅ System sends messages automatically  
✅ AI agent handles customer responses intelligently  
✅ System schedules visits/calls when customer agrees  
✅ Campaign dashboard shows all metrics  
✅ T2SQL can query CRM lead data  
✅ Document RAG retrieves project information from brochures  

---

**Status**: ✅ Core functionality implemented. Ready for production enhancements (actual email sending, WhatsApp, UI frontend).

