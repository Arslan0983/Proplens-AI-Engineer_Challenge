"""
LangGraph agent for routing queries to T2SQL or RAG.
"""

from typing import Dict, Any, Literal, TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END
from django.conf import settings
from api.services.vanna_service import get_vanna_service
from api.services.document_service import get_document_service


# Define state schema
class AgentState(TypedDict):
    query: str
    query_type: str
    response: str
    metadata: Dict[str, Any]


# Initialize LLM
try:
    llm = ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL,
        google_api_key=settings.GEMINI_API_KEY,
        temperature=0.1
    )
except Exception as e:
    print(f"Warning: Could not initialize Gemini LLM: {e}")
    llm = None


def router_node(state: AgentState) -> AgentState:
    """Route query to T2SQL or RAG based on content."""
    query = state.get("query", "")
    query_lower = query.lower()
    
    # Keywords for routing
    sql_keywords = [
        "lead", "leads", "contact", "contacts", "crm", "database",
        "query", "count", "sum", "average", "total", "list", "show",
        "how many", "what is the", "who", "which", "top", "bottom"
    ]
    
    rag_keywords = [
        "property", "properties", "brochure", "project", "development",
        "location", "amenities", "floor", "unit", "price", "square feet",
        "bedroom", "bathroom", "parking", "view", "beachfront", "apartment",
        "condo", "residential", "commercial", "address", "details", "specifications"
    ]
    
    sql_score = sum(1 for keyword in sql_keywords if keyword in query_lower)
    rag_score = sum(1 for keyword in rag_keywords if keyword in query_lower)
    
    # Use LLM for routing if scores are close
    if llm and abs(sql_score - rag_score) <= 1:
        routing_prompt = f"""Determine if this query should use:
1. Text-to-SQL (T2SQL): For queries about CRM data, leads, contacts, database records
2. Document RAG: For queries about properties, real estate, brochures, project details

Query: {query}

Respond with only 't2sql' or 'rag'."""
        
        try:
            response = llm.invoke([HumanMessage(content=routing_prompt)])
            decision = response.content.lower().strip()
            if "t2sql" in decision or "sql" in decision:
                query_type = "t2sql"
            elif "rag" in decision:
                query_type = "rag"
            else:
                query_type = "t2sql" if sql_score >= rag_score else "rag"
        except Exception as e:
            print(f"Error in LLM routing: {e}")
            query_type = "t2sql" if sql_score >= rag_score else "rag"
    else:
        query_type = "t2sql" if sql_score > rag_score else "rag"
    
    state["query_type"] = query_type
    return state


def t2sql_node(state: AgentState) -> AgentState:
    """Handle Text-to-SQL query using Vanna."""
    query = state.get("query", "")
    
    try:
        vanna_service = get_vanna_service()
        
        if vanna_service is None:
            state["response"] = "Text-to-SQL service is not available. Please try asking about property information instead."
            state["metadata"] = {"tool": "text_to_sql_tool", "error": "Service unavailable"}
            return state
        
        sql = vanna_service.generate_sql(query)
        if not sql:
            state["response"] = "I couldn't generate a SQL query for your question. Please try rephrasing it or ask about property information instead."
            state["metadata"] = {"tool": "text_to_sql_tool", "error": "SQL generation failed"}
            return state
        
        results = vanna_service.run_sql(sql)
        if results is None:
            state["response"] = "I couldn't execute the query. Please check the question and try again."
            state["metadata"] = {"tool": "text_to_sql_tool", "error": "SQL execution failed"}
            return state
        
        response = vanna_service.generate_response(query, sql, results)
        state["response"] = response
        state["metadata"] = {"tool": "text_to_sql_tool", "sql": sql, "result_count": len(results)}
        
    except Exception as e:
        state["response"] = f"Error processing T2SQL query: {str(e)}"
        state["metadata"] = {"tool": "text_to_sql_tool", "error": str(e)}
    
    return state


def rag_node(state: AgentState) -> AgentState:
    """Handle Document RAG query."""
    query = state.get("query", "")
    
    try:
        document_service = get_document_service()
        
        results = document_service.search_documents(query, n_results=5)
        
        if not results:
            state["response"] = "I couldn't find any relevant information in the uploaded documents."
            state["metadata"] = {"tool": "document_rag_tool", "error": "No documents found"}
            return state
        
        context = "\n\n".join([
            f"Document: {r['metadata'].get('filename', 'Unknown')}\n{r['content']}"
            for r in results
        ])
        
        prompt = f"""Based on the following context from property brochures, answer the user's question accurately.

Context:
{context}

Question: {query}

Provide a clear and accurate answer based only on the context provided. If the context doesn't contain enough information, say so."""
        
        if llm:
            response = llm.invoke([HumanMessage(content=prompt)])
            state["response"] = response.content
        else:
            state["response"] = "LLM not available for RAG response."
        
        state["metadata"] = {"tool": "document_rag_tool", "documents_found": len(results)}
        
    except Exception as e:
        state["response"] = f"Error processing RAG query: {str(e)}"
        state["metadata"] = {"tool": "document_rag_tool", "error": str(e)}
    
    return state


def route_decision(state: AgentState) -> Literal["t2sql", "rag"]:
    """Conditional edge function - routes based on query_type."""
    return state.get("query_type", "t2sql")


# Build LangGraph workflow
def create_agent_graph() -> StateGraph:
    """Create LangGraph agent with routing logic."""
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("router", router_node)
    workflow.add_node("t2sql", t2sql_node)
    workflow.add_node("rag", rag_node)
    
    # Set entry point - connect START to router
    workflow.add_edge(START, "router")
    
    # Add conditional edges from router
    workflow.add_conditional_edges(
        "router",
        route_decision,
        {
            "t2sql": "t2sql",
            "rag": "rag"
        }
    )
    
    # Both nodes go to END
    workflow.add_edge("t2sql", END)
    workflow.add_edge("rag", END)
    
    return workflow.compile()


# Singleton agent instance
_agent = None

def get_agent() -> StateGraph:
    """Get LangGraph agent instance."""
    global _agent
    if _agent is None:
        _agent = create_agent_graph()
    return _agent
