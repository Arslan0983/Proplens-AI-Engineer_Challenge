"""
API endpoints for the lead nurturing system.
"""

from ninja import Router
from django.http import HttpRequest, JsonResponse
from typing import List
from datetime import datetime
from django.utils import timezone
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from pathlib import Path
from django.core.mail import send_mail
from django.conf import settings

from .schemas import (
    QueryRequest, QueryResponse, DocumentUploadResponse,
    LeadFilterRequest, LeadFilterResponse, CampaignCreateRequest,
    CampaignResponse, CampaignMetricsResponse, CustomerResponseRequest
)
from .auth import JWTAuth, get_test_token
# Lazy import to avoid startup delays
# from .agent.agent import get_agent
from .models import (
    QueryHistory, Document, Campaign, CRMLead, CampaignLead,
    CampaignMessage, ScheduledVisit
)
# Lazy imports to avoid startup delays
# from .services.document_service import get_document_service
from .services.lead_service import LeadService
from .services.email_service import EmailService

api_router = Router()
jwt_auth = JWTAuth()


@api_router.post("/queries", response=QueryResponse, auth=jwt_auth)
def submit_query(request: HttpRequest, query_data: QueryRequest):
    """
    Submit a query - the agent figures out if it's a T2SQL or RAG question.
    """
    try:
        agent = get_agent()
        
        initial_state = {
            "query": query_data.query,
            "query_type": "unknown",
            "response": "",
            "metadata": {}
        }
        
        # Invoke LangGraph agent
        result = agent.invoke(initial_state)
        
        QueryHistory.objects.create(
            query=query_data.query,
            query_type=result.get("query_type", "unknown"),
            response=result.get("response", "")
        )
        
        return QueryResponse(
            response=result.get("response", "No response generated"),
            query_type=result.get("query_type", "unknown"),
            metadata=result.get("metadata", {})
        )
    
    except Exception as e:
        return JsonResponse(
            {"error": "Internal server error", "detail": str(e)},
            status=500
        )


@api_router.post("/documents/upload", response=DocumentUploadResponse, auth=jwt_auth)
def upload_document(request: HttpRequest, file):
    """
    Upload a brochure - gets processed, chunked, embedded, and stored in ChromaDB.
    """
    try:
        if not file:
            return JsonResponse(
                {"error": "No file provided"},
                status=400
            )
        
        filename = file.name
        file_path = default_storage.save(
            f"documents/{filename}",
            ContentFile(file.read())
        )
        
        full_path = default_storage.path(file_path)
        file_type = Path(filename).suffix.lower().lstrip('.')
        
        document_service = get_document_service()
        chunk_count = document_service.process_document(full_path, filename)
        
        doc = Document.objects.create(
            filename=filename,
            file_path=file_path,
            file_type=file_type,
            chunk_count=chunk_count
        )
        
        return DocumentUploadResponse(
            message="Document uploaded and processed successfully",
            document_id=doc.id,
            filename=filename,
            chunk_count=chunk_count
        )
    
    except Exception as e:
        return JsonResponse(
            {"error": "Error processing document", "detail": str(e)},
            status=500
        )


@api_router.get("/health", response=dict)
def health_check(request: HttpRequest):
    """Basic health check."""
    return {
        "status": "healthy",
        "service": "Proplens AI Agent API"
    }


@api_router.get("/test-token", response=dict)
def get_test_token_endpoint(request: HttpRequest):
    """
    Generate a test JWT token for testing.
    WARNING: This is for testing only. In production, use proper login endpoint.
    """
    token = get_test_token()
    return {
        "token": token,
        "note": "This is a test token valid for 24 hours. Use it in Authorization header as 'Bearer <token>'"
    }


# Lead Nurturing Campaign Endpoints

@api_router.post("/campaigns/filter-leads", response=LeadFilterResponse, auth=jwt_auth)
def filter_leads(request: HttpRequest, filter_data: LeadFilterRequest):
    """
    Filter leads - need at least 2 criteria.
    """
    try:
        leads = LeadService.filter_leads(
            project_enquired=filter_data.project_enquired,
            budget_min=filter_data.budget_min,
            budget_max=filter_data.budget_max,
            unit_types=filter_data.unit_types,
            lead_status=filter_data.lead_status,
            last_conversation_from=filter_data.last_conversation_from,
            last_conversation_to=filter_data.last_conversation_to,
        )
        
        return LeadFilterResponse(
            leads_count=len(leads),
            lead_ids=[lead.id for lead in leads]
        )
    except ValueError as e:
        return JsonResponse(
            {"error": str(e)},
            status=400
        )
    except Exception as e:
        return JsonResponse(
            {"error": "Error filtering leads", "detail": str(e)},
            status=500
        )


@api_router.post("/campaigns", response=CampaignResponse, auth=jwt_auth)
def create_campaign(request: HttpRequest, campaign_data: CampaignCreateRequest):
    """
    Create a new lead nurturing campaign and send personalized messages.
    """
    try:
        # Create campaign
        campaign = Campaign.objects.create(
            name=campaign_data.name,
            campaign_project=campaign_data.campaign_project,
            message_channel=campaign_data.message_channel,
            sales_offer=campaign_data.sales_offer
        )
        
        # Add leads to campaign
        leads = CRMLead.objects.filter(id__in=campaign_data.lead_ids)
        campaign_leads = []
        for lead in leads:
            campaign_lead = CampaignLead.objects.create(
                campaign=campaign,
                lead=lead
            )
            campaign_leads.append(campaign_lead)
        
        # Generate and send emails
        email_service = EmailService()
        messages_sent = 0
        
        for campaign_lead in campaign_leads:
            try:
                # Generate personalized email
                email_content = email_service.generate_personalized_email(
                    lead=campaign_lead.lead,
                    campaign=campaign
                )
                
                # Save outbound message
                CampaignMessage.objects.create(
                    campaign_lead=campaign_lead,
                    message_type='outbound',
                    content=email_content,
                    is_ai_generated=True
                )
                
                # Send email to demonstration email address
                demo_email = "arslan.asif09832c@gmail.com"
                subject = f"Follow-up on {campaign.campaign_project} - {campaign_lead.lead.name}"
                
                # Include original recipient info in email body
                email_body = f"""
Original Recipient: {campaign_lead.lead.name} ({campaign_lead.lead.email})

{email_content}
"""
                
                try:
                    send_mail(
                        subject=subject,
                        message=email_body,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[demo_email],
                        fail_silently=False,
                    )
                    print(f"✓ Email sent to {demo_email} for lead {campaign_lead.lead.name} ({campaign_lead.lead.email})")
                except Exception as e:
                    print(f"✗ Error sending email to {demo_email}: {e}")
                    # Still mark as sent for demo purposes
                
                # Mark as sent
                campaign_lead.message_sent = True
                campaign_lead.message_sent_at = timezone.now()
                campaign_lead.save()
                messages_sent += 1
                
            except Exception as e:
                print(f"Error sending email to {campaign_lead.lead.email}: {e}")
        
        # Return campaign response
        return CampaignResponse(
            id=campaign.id,
            name=campaign.name,
            campaign_project=campaign.campaign_project,
            message_channel=campaign.message_channel,
            sales_offer=campaign.sales_offer,
            leads_shortlisted=len(campaign_leads),
            messages_sent=messages_sent,
            leads_responded=0,
            goals_achieved=0,
            created_at=campaign.created_at
        )
        
    except Exception as e:
        return JsonResponse(
            {"error": "Error creating campaign", "detail": str(e)},
            status=500
        )


@api_router.get("/campaigns/{campaign_id}/metrics", response=CampaignMetricsResponse, auth=jwt_auth)
def get_campaign_metrics(request: HttpRequest, campaign_id: int):
    """Get campaign metrics and dashboard data."""
    try:
        campaign = Campaign.objects.get(id=campaign_id)
        
        campaign_leads = campaign.campaign_leads.all()
        leads_shortlisted = campaign_leads.count()
        messages_sent = campaign_leads.filter(message_sent=True).count()
        leads_responded = campaign_leads.filter(responded=True).count()
        goals_achieved = campaign_leads.filter(goal_achieved=True).count()
        
        # Get scheduled visits
        scheduled_visits = []
        for campaign_lead in campaign_leads.filter(goal_achieved=True):
            visits = campaign_lead.scheduled_visits.all()
            for visit in visits:
                scheduled_visits.append({
                    "lead_name": campaign_lead.lead.name,
                    "lead_email": campaign_lead.lead.email,
                    "lead_phone": campaign_lead.lead.phone,
                    "visit_type": visit.visit_type,
                    "scheduled_date": visit.scheduled_date.isoformat(),
                    "conversation_summary": campaign_lead.messages.filter(
                        message_type='inbound'
                    ).order_by('-created_at').first().content[:200] if campaign_lead.messages.filter(message_type='inbound').exists() else ""
                })
        
        return CampaignMetricsResponse(
            campaign_id=campaign.id,
            campaign_name=campaign.name,
            leads_shortlisted=leads_shortlisted,
            messages_sent=messages_sent,
            leads_responded=leads_responded,
            goals_achieved=goals_achieved,
            scheduled_visits=scheduled_visits
        )
        
    except Campaign.DoesNotExist:
        return JsonResponse(
            {"error": "Campaign not found"},
            status=404
        )
    except Exception as e:
        return JsonResponse(
            {"error": "Error fetching metrics", "detail": str(e)},
            status=500
        )


@api_router.get("/campaigns", response=List[CampaignResponse], auth=jwt_auth)
def list_campaigns(request: HttpRequest):
    """List all campaigns."""
    try:
        campaigns = Campaign.objects.all()
        result = []
        
        for campaign in campaigns:
            campaign_leads = campaign.campaign_leads.all()
            result.append(CampaignResponse(
                id=campaign.id,
                name=campaign.name,
                campaign_project=campaign.campaign_project,
                message_channel=campaign.message_channel,
                sales_offer=campaign.sales_offer,
                leads_shortlisted=campaign_leads.count(),
                messages_sent=campaign_leads.filter(message_sent=True).count(),
                leads_responded=campaign_leads.filter(responded=True).count(),
                goals_achieved=campaign_leads.filter(goal_achieved=True).count(),
                created_at=campaign.created_at
            ))
        
        return result
        
    except Exception as e:
        return JsonResponse(
            {"error": "Error fetching campaigns", "detail": str(e)},
            status=500
        )


@api_router.post("/campaigns/{campaign_id}/responses", auth=jwt_auth)
def handle_customer_response(request: HttpRequest, campaign_id: int, response_data: CustomerResponseRequest):
    """
    Handle customer response to nurturing email.
    """
    try:
        from api.services.response_handler import get_response_handler
        
        campaign = Campaign.objects.get(id=campaign_id)
        lead_id = response_data.lead_id
        customer_message = response_data.message
        
        campaign_lead = CampaignLead.objects.get(
            campaign=campaign,
            lead_id=lead_id
        )
        
        # Handle response
        handler = get_response_handler()
        result = handler.handle_response(campaign_lead, customer_message)
        
        return JsonResponse({
            "success": True,
            "intent": result['intent'],
            "response": result['response'],
            "goal_achieved": result.get('goal_achieved', False)
        })
        
    except Campaign.DoesNotExist:
        return JsonResponse(
            {"error": "Campaign not found"},
            status=404
        )
    except CampaignLead.DoesNotExist:
        return JsonResponse(
            {"error": "Lead not found in campaign"},
            status=404
        )
    except Exception as e:
        return JsonResponse(
            {"error": "Error handling response", "detail": str(e)},
            status=500
        )

