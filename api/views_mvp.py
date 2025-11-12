"""
Simplified MVP API - Core chatbot functionality only.
Customer asks questions, AI responds using T2SQL + RAG.
"""

import logging
from ninja import Router
from django.http import HttpRequest, JsonResponse

from .schemas import QueryRequest, QueryResponse
from .auth import JWTAuth, get_test_token

logger = logging.getLogger('api')

api_router = Router()
jwt_auth = JWTAuth()


@api_router.get("/health", response=dict)
def health_check(request: HttpRequest):
    """Basic health check - no heavy imports."""
    return {
        "status": "healthy",
        "service": "Proplens AI Chatbot MVP"
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
        "instructions": "Use this token in the Authorization header as: Bearer <token>"
    }


@api_router.post("/chat", response=QueryResponse, auth=jwt_auth)
def chat(request: HttpRequest, query_data: QueryRequest):
    """
    Chat endpoint - Ask any question about properties or CRM data.
    Agent routes to T2SQL (for database queries) or RAG (for brochure info).
    
    Examples:
    - "How many leads do we have?"
    - "What are the facilities at Sobha Waves?"
    - "Show me leads with budget over 1 million"
    """
    import time
    start_time = time.time()
    logger.info(f"Chat request received: query='{query_data.query[:100]}'")
    
    try:
        # Lazy load the agent only when needed
        logger.debug("Loading agent...")
        from .agent.agent import get_agent
        
        initial_state = {
            "query": query_data.query,
            "query_type": "unknown",
            "response": "",
            "metadata": {}
        }
        
        # Run agent - let Gunicorn handle timeout (120s)
        logger.debug("Invoking agent...")
        agent = get_agent()
        final_state = agent.invoke(initial_state)
        
        elapsed = time.time() - start_time
        logger.info(f"Chat request completed in {elapsed:.2f}s: type={final_state.get('query_type')}, response_length={len(final_state.get('response', ''))}")
        
        # Save to history
        from .models import QueryHistory
        QueryHistory.objects.create(
            query=query_data.query,
            query_type=final_state.get('query_type', 'unknown'),
            response=final_state.get('response', '')
            # Skip metadata field if not in model
        )
        
        return QueryResponse(
            query=query_data.query,
            response=final_state.get('response', ''),
            query_type=final_state.get('query_type', 'unknown'),
            metadata=final_state.get('metadata', {}) or {}
        )
        
    except Exception as e:
        import traceback
        elapsed = time.time() - start_time
        error_trace = traceback.format_exc()
        logger.error(f"Chat request failed after {elapsed:.2f}s: {str(e)}", exc_info=True)
        logger.debug(f"Full traceback: {error_trace}")
        return JsonResponse(
            {
                "error": "Error processing query",
                "detail": str(e),
                "query": query_data.query
            },
            status=500
        )

