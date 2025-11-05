"""
Handles customer responses - figures out what they want and responds appropriately.
"""

from typing import Dict, Any, Literal
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from django.conf import settings
from api.services.document_service import get_document_service
from api.models import CampaignLead, CampaignMessage, ScheduledVisit
from django.utils import timezone
import re


class CustomerResponseHandler:
    """Handles customer replies - routes based on intent and generates responses."""
    
    def __init__(self):
        try:
            self.llm = ChatGoogleGenerativeAI(
                model=settings.GEMINI_MODEL,
                google_api_key=settings.GEMINI_API_KEY,
                temperature=0.1
            )
        except Exception as e:
            print(f"Warning: Could not initialize LLM: {e}")
            self.llm = None
    
    def handle_response(
        self,
        campaign_lead: CampaignLead,
        customer_message: str
    ) -> Dict[str, Any]:
        """
        Handle customer message and figure out what they want.
        Returns intent, response, and whether we hit the goal (scheduled visit/call).
        """
        # Save the message
        CampaignMessage.objects.create(
            campaign_lead=campaign_lead,
            message_type='inbound',
            content=customer_message,
            is_ai_generated=False
        )
        
        # Figure out what they want
        intent = self._analyze_intent(customer_message)
        
        # Generate response based on what they want
        if intent == 'schedule_visit' or intent == 'schedule_call':
            # They want to schedule - that's the goal!
            response = self._generate_scheduling_response(
                campaign_lead, customer_message, intent
            )
            return {
                'intent': intent,
                'response': response,
                'schedule_visit': intent == 'schedule_visit',
                'schedule_call': intent == 'schedule_call',
                'goal_achieved': True
            }
        elif intent == 'property_info':
            # They're asking about the property - answer with RAG
            response = self._generate_property_info_response(
                campaign_lead, customer_message
            )
            return {
                'intent': intent,
                'response': response,
                'schedule_visit': False,
                'schedule_call': False,
                'goal_achieved': False
            }
        else:
            # General response - still try to nudge them to schedule
            response = self._generate_nudging_response(
                campaign_lead, customer_message
            )
            return {
                'intent': intent,
                'response': response,
                'schedule_visit': False,
                'schedule_call': False,
                'goal_achieved': False
            }
    
    def _analyze_intent(self, message: str) -> Literal['property_info', 'schedule_visit', 'schedule_call', 'other']:
        """Figure out what the customer wants from their message."""
        message_lower = message.lower()
        
        # Schedule visit keywords
        visit_keywords = [
            'visit', 'viewing', 'tour', 'see the property', 'come by',
            'visit the property', 'schedule a visit', 'book a visit'
        ]
        
        # Schedule call keywords
        call_keywords = [
            'call', 'phone', 'speak', 'talk', 'discuss', 'conversation',
            'schedule a call', 'call me', 'phone call'
        ]
        
        # Property info keywords
        info_keywords = [
            'amenities', 'facilities', 'features', 'price', 'pricing',
            'location', 'bedroom', 'bathroom', 'square', 'floor plan',
            'what are', 'tell me about', 'information', 'details'
        ]
        
        if any(keyword in message_lower for keyword in visit_keywords):
            return 'schedule_visit'
        elif any(keyword in message_lower for keyword in call_keywords):
            return 'schedule_call'
        elif any(keyword in message_lower for keyword in info_keywords):
            return 'property_info'
        else:
            return 'other'
    
    def _generate_property_info_response(
        self,
        campaign_lead: CampaignLead,
        customer_message: str
    ) -> str:
        """Generate response using RAG to answer property questions."""
        if not self.llm:
            return "Thank you for your interest. Please let me know if you'd like to schedule a visit."
        
        # Get project information using RAG
        document_service = get_document_service()
        project_name = campaign_lead.campaign.campaign_project
        
        # Search for relevant information
        query = f"{customer_message} {project_name}"
        results = document_service.search_documents(query, n_results=5)
        
        context = ""
        if results:
            context = "\n\n".join([
                f"Source: {r['metadata'].get('filename', 'Unknown')}\n{r['content']}"
                for r in results
            ])
        
        # Generate response
        prompt = f"""You are a helpful sales associate responding to a customer inquiry about a property.

Customer Question: {customer_message}
Project: {project_name}

Property Information:
{context if context else "Information not available in brochures."}

Lead Information:
- Name: {campaign_lead.lead.name}
- Previous enquiry: {campaign_lead.lead.project_enquired or 'N/A'}
- Budget: ${campaign_lead.lead.budget_min or 'N/A'} - ${campaign_lead.lead.budget_max or 'N/A'}
- Unit preference: {campaign_lead.lead.unit_type or 'N/A'}

Instructions:
1. Answer the customer's question clearly and accurately using the property information provided
2. If information is not available, say so politely
3. After answering, gently nudge them to schedule a property visit or call
4. Keep it friendly and professional
5. End with a clear call-to-action for scheduling

Generate the response:"""

        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            
            # Save AI-generated response
            CampaignMessage.objects.create(
                campaign_lead=campaign_lead,
                message_type='outbound',
                content=response.content,
                is_ai_generated=True
            )
            
            return response.content
        except Exception as e:
            print(f"Error generating response: {e}")
            return "Thank you for your interest. I'd be happy to schedule a visit or call to discuss this further. Would you like to proceed?"
    
    def _generate_scheduling_response(
        self,
        campaign_lead: CampaignLead,
        customer_message: str,
        intent: str
    ) -> str:
        """Generate response for scheduling visit/call."""
        visit_type = 'property_visit' if intent == 'schedule_visit' else 'sales_call'
        
        # Extract date/time from message if mentioned
        scheduled_date = self._extract_date_from_message(customer_message)
        
        # Mark goal as achieved
        campaign_lead.responded = True
        campaign_lead.goal_achieved = True
        campaign_lead.goal_achieved_at = timezone.now()
        campaign_lead.save()
        
        # Create scheduled visit/call (placeholder date if not extracted)
        if not scheduled_date:
            scheduled_date = timezone.now() + timezone.timedelta(days=2)
        
        ScheduledVisit.objects.create(
            campaign_lead=campaign_lead,
            visit_type=visit_type,
            scheduled_date=scheduled_date,
            sales_associate_email='sales@proplens.com',  # TODO: Get from campaign settings
            notified=False
        )
        
        # Generate confirmation response
        response = f"""Thank you {campaign_lead.lead.name}!

I've scheduled your {'property visit' if intent == 'schedule_visit' else 'sales call'} for {scheduled_date.strftime('%B %d, %Y at %I:%M %p')}.

Our sales team will reach out to you shortly to confirm the details and answer any additional questions you may have.

We look forward to meeting you!

Best regards,
Sales Team"""
        
        # Save AI-generated response
        CampaignMessage.objects.create(
            campaign_lead=campaign_lead,
            message_type='outbound',
            content=response,
            is_ai_generated=True
        )
        
        return response
    
    def _generate_nudging_response(
        self,
        campaign_lead: CampaignLead,
        customer_message: str
    ) -> str:
        """Generate general response with nudging toward goal."""
        if not self.llm:
            return "Thank you for your response. Would you like to schedule a property visit or call to discuss further?"
        
        # Get conversation history
        previous_messages = campaign_lead.messages.all().order_by('created_at')
        conversation_history = "\n".join([
            f"{'Customer' if msg.message_type == 'inbound' else 'Sales'}: {msg.content[:200]}"
            for msg in previous_messages[-5:]  # Last 5 messages
        ])
        
        prompt = f"""You are a sales associate having a conversation with a potential property buyer.

Lead Information:
- Name: {campaign_lead.lead.name}
- Project of interest: {campaign_lead.campaign.campaign_project}
- Previous enquiry: {campaign_lead.lead.project_enquired or 'N/A'}

Conversation History:
{conversation_history}

Customer's Latest Message: {customer_message}

Instructions:
1. Respond appropriately to the customer's message
2. Be friendly and helpful
3. Build urgency and nudge them toward scheduling a property visit or call
4. Highlight the benefits of seeing the property in person or having a call
5. Make it clear that scheduling is the next step
6. Keep it concise and engaging

Generate the response:"""

        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            
            # Save AI-generated response
            CampaignMessage.objects.create(
                campaign_lead=campaign_lead,
                message_type='outbound',
                content=response.content,
                is_ai_generated=True
            )
            
            campaign_lead.responded = True
            campaign_lead.save()
            
            return response.content
        except Exception as e:
            print(f"Error generating nudging response: {e}")
            return "Thank you for your response. Would you like to schedule a property visit or call to discuss this further?"
    
    def _extract_date_from_message(self, message: str):
        """Extract date/time from customer message (simplified)."""
        # Simple pattern matching - in production, use a proper date parser
        import re
        from datetime import datetime, timedelta
        
        # Look for common date patterns
        patterns = [
            r'tomorrow',
            r'next week',
            r'monday|tuesday|wednesday|thursday|friday|saturday|sunday',
            r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
        ]
        
        message_lower = message.lower()
        
        if 'tomorrow' in message_lower:
            return timezone.now() + timedelta(days=1)
        elif 'next week' in message_lower:
            return timezone.now() + timedelta(days=7)
        else:
            # Default to 2 days from now
            return timezone.now() + timedelta(days=2)


def get_response_handler() -> CustomerResponseHandler:
    """Get singleton response handler instance."""
    global _response_handler
    if '_response_handler' not in globals():
        _response_handler = CustomerResponseHandler()
    return _response_handler

