"""
Generates personalized emails using RAG to pull project info from brochures.
"""

from typing import Dict, Any
from django.conf import settings
import google.generativeai as genai
from api.services.document_service import get_document_service
from api.models import CRMLead, Campaign


class EmailService:
    """Handles email generation - uses RAG to get project info and Gemini to write personalized emails."""
    
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.llm = genai.GenerativeModel(settings.GEMINI_MODEL)
        self.document_service = get_document_service()
    
    def generate_personalized_email(
        self,
        lead: CRMLead,
        campaign: Campaign
    ) -> str:
        """
        Generate personalized email for a lead.
        Pulls project info from brochures via RAG, combines with lead data, sends to Gemini.
        """
        # Grab project details from brochures
        project_query = f"Tell me about {campaign.campaign_project} project features, amenities, and details"
        brochure_info = self._get_project_info(project_query)
        
        # Build context about the lead
        lead_context = self._build_lead_context(lead)
        
        # Generate email using LLM
        prompt = f"""You are a professional sales associate writing a personalized follow-up email to a potential property buyer.

LEAD INFORMATION:
{lead_context}

CAMPAIGN PROJECT: {campaign.campaign_project}

PROJECT INFORMATION FROM BROCHURES:
{brochure_info}

SALES OFFER (if any):
{campaign.sales_offer or 'No specific offer mentioned'}

INSTRUCTIONS:
1. Write a warm, personalized email that references the lead's past inquiry and preferences
2. Highlight relevant project features that match their needs (family size, unit type, budget, location preference)
3. Reference their last conversation summary if available
4. Include the sales offer just before the call-to-action
5. End with a clear call-to-action asking them to schedule a property visit or call
6. Keep it professional but friendly and engaging
7. Make it hyper-personalized based on all available lead information

Generate the email body only (no subject line):"""

        try:
            response = self.llm.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error generating email: {e}")
            return self._generate_fallback_email(lead, campaign)
    
    def _get_project_info(self, query: str) -> str:
        """Search brochures for project info using RAG."""
        try:
            results = self.document_service.search_documents(query, n_results=5)
            if results:
                context = "\n\n".join([
                    f"Source: {r['metadata'].get('filename', 'Unknown')}\n{r['content']}"
                    for r in results
                ])
                return context
            return "Project information not available in brochures."
        except Exception as e:
            print(f"Error retrieving project info: {e}")
            return "Project information not available."
    
    def _build_lead_context(self, lead: CRMLead) -> str:
        """Put together all the lead info into a context string."""
        context_parts = [
            f"Name: {lead.name}",
            f"Email: {lead.email}",
        ]
        
        if lead.project_enquired:
            context_parts.append(f"Previously enquired about: {lead.project_enquired}")
        
        if lead.budget_min or lead.budget_max:
            budget_str = ""
            if lead.budget_min:
                budget_str += f"${lead.budget_min:,.0f}"
            if lead.budget_max and lead.budget_max != lead.budget_min:
                budget_str += f" - ${lead.budget_max:,.0f}"
            context_parts.append(f"Budget: {budget_str}")
        
        if lead.unit_type:
            context_parts.append(f"Unit type preference: {lead.unit_type}")
        
        if lead.family_size:
            context_parts.append(f"Family size: {lead.family_size}")
        
        if lead.location_preference:
            context_parts.append(f"Location preference: {lead.location_preference}")
        
        if lead.purchase_motive:
            context_parts.append(f"Purchase motive: {lead.purchase_motive}")
        
        if lead.financing_preference:
            context_parts.append(f"Financing preference: {lead.financing_preference}")
        
        if lead.last_conversation_summary:
            context_parts.append(f"Last conversation summary: {lead.last_conversation_summary}")
        
        if lead.last_conversation_date:
            context_parts.append(f"Last conversation date: {lead.last_conversation_date}")
        
        return "\n".join(context_parts)
    
    def _generate_fallback_email(self, lead: CRMLead, campaign: Campaign) -> str:
        """Fallback email if Gemini fails (shouldn't happen but just in case)."""
        return f"""Dear {lead.name},

We hope this email finds you well. We wanted to reach out regarding your interest in property investments.

We have an exciting opportunity with {campaign.campaign_project} that we believe might interest you.

{campaign.sales_offer or 'We have special offers available for interested buyers.'}

We would love to schedule a property visit or call to discuss how this project aligns with your needs.

Please let us know your availability, and we'll arrange a convenient time.

Best regards,
Sales Team"""

