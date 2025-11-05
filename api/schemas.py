"""
Pydantic schemas for API request/response models.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class QueryRequest(BaseModel):
    """Request schema for agent queries."""
    query: str = Field(..., description="Natural language query for the agent")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What are the top 5 leads by potential value?"
            }
        }


class QueryResponse(BaseModel):
    """Response schema for agent queries."""
    response: str = Field(..., description="Agent's natural language response")
    query_type: str = Field(..., description="Type of query executed: 't2sql' or 'rag'")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata about the response")
    
    class Config:
        json_schema_extra = {
            "example": {
                "response": "The top 5 leads by potential value are...",
                "query_type": "t2sql",
                "metadata": {"sql_query": "SELECT ..."}
            }
        }


class DocumentUploadResponse(BaseModel):
    """Response schema for document upload."""
    message: str
    document_id: int
    filename: str
    chunk_count: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Document uploaded and processed successfully",
                "document_id": 1,
                "filename": "brochure.pdf",
                "chunk_count": 42
            }
        }


class ErrorResponse(BaseModel):
    """Error response schema."""
    error: str
    detail: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "Authentication failed",
                "detail": "Invalid or missing JWT token"
            }
        }


# Lead Nurturing Campaign Schemas

class LeadFilterRequest(BaseModel):
    """Request schema for filtering leads."""
    project_enquired: Optional[str] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    unit_types: Optional[List[str]] = None
    lead_status: Optional[str] = None
    last_conversation_from: Optional[datetime] = None
    last_conversation_to: Optional[datetime] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "project_enquired": "Altura",
                "budget_min": 500000,
                "budget_max": 1000000,
                "unit_types": ["2 bed", "3 bed"],
                "lead_status": "Connected"
            }
        }


class LeadFilterResponse(BaseModel):
    """Response schema for lead filtering."""
    leads_count: int
    lead_ids: List[int]
    
    class Config:
        json_schema_extra = {
            "example": {
                "leads_count": 15,
                "lead_ids": [1, 2, 3, 4, 5]
            }
        }


class CampaignCreateRequest(BaseModel):
    """Request schema for creating a campaign."""
    name: str
    campaign_project: str
    message_channel: str = "email"
    sales_offer: Optional[str] = None
    lead_ids: List[int]
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Q1 2025 Property Campaign",
                "campaign_project": "Lumina Grand",
                "message_channel": "email",
                "sales_offer": "Special 5% discount for early buyers",
                "lead_ids": [1, 2, 3, 4, 5]
            }
        }


class CampaignResponse(BaseModel):
    """Response schema for campaign."""
    id: int
    name: str
    campaign_project: str
    message_channel: str
    sales_offer: Optional[str]
    leads_shortlisted: int
    messages_sent: int
    leads_responded: int
    goals_achieved: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class CampaignMetricsResponse(BaseModel):
    """Response schema for campaign metrics."""
    campaign_id: int
    campaign_name: str
    leads_shortlisted: int
    messages_sent: int
    leads_responded: int
    goals_achieved: int
    scheduled_visits: List[Dict[str, Any]]
    
    class Config:
        json_schema_extra = {
            "example": {
                "campaign_id": 1,
                "campaign_name": "Q1 2025 Property Campaign",
                "leads_shortlisted": 50,
                "messages_sent": 45,
                "leads_responded": 12,
                "goals_achieved": 5,
                "scheduled_visits": []
            }
        }


class CustomerResponseRequest(BaseModel):
    """Request schema for customer response."""
    lead_id: int
    message: str

