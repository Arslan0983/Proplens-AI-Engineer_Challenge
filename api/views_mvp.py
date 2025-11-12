"""
Simplified MVP API - Core chatbot functionality only.
Customer asks questions, AI responds using T2SQL + RAG.
"""

from ninja import Router
from django.http import HttpRequest, JsonResponse

from .schemas import QueryRequest, QueryResponse
from .auth import JWTAuth, get_test_token

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
    try:
        import signal
        from contextlib import contextmanager
        
        @contextmanager
        def timeout_handler(seconds):
            """Handle timeout for agent execution."""
            def timeout_signal(signum, frame):
                raise TimeoutError(f"Agent execution timed out after {seconds} seconds")
            
            # Set signal handler
            old_handler = signal.signal(signal.SIGALRM, timeout_signal)
            signal.alarm(seconds)
            try:
                yield
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
        
        # Lazy load the agent only when needed
        from .agent.agent import get_agent
        
        initial_state = {
            "query": query_data.query,
            "query_type": "unknown",
            "response": "",
            "metadata": {}
        }
        
        # Run agent with timeout protection (90 seconds)
        try:
            agent = get_agent()
            # Use timeout only on Linux/Unix (signal.SIGALRM not available on Windows)
            import sys
            if sys.platform != 'win32':
                with timeout_handler(90):
                    final_state = agent.invoke(initial_state)
            else:
                final_state = agent.invoke(initial_state)
        except TimeoutError as te:
            return JsonResponse(
                {
                    "error": "Request timeout",
                    "detail": "The query took too long to process. Please try a simpler question or try again.",
                    "query": query_data.query
                },
                status=504
            )
        
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
        print(f"Error in chat: {e}")
        print(traceback.format_exc())
        return JsonResponse(
            {
                "error": "Error processing query",
                "detail": str(e),
                "query": query_data.query
            },
            status=500
        )

