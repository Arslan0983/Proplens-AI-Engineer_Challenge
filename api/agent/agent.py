"""
Router agent that figures out if a query should go to T2SQL or RAG.
"""

from typing import Dict, Any, Literal
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from django.conf import settings
from api.services.vanna_service import get_vanna_service
from api.services.document_service import get_document_service


# Set up Gemini
try:
    llm = ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL,
        google_api_key=settings.GEMINI_API_KEY,
        temperature=0.1
    )
except Exception as e:
    print(f"Warning: Could not initialize Gemini LLM: {e}")
    llm = None


def text_to_sql_tool(question: str) -> str:
    """
    Use this for questions about the database - leads, contacts, CRM data.
    """
    vanna_service = get_vanna_service()
    
    sql = vanna_service.generate_sql(question)
    if not sql:
        return "I couldn't generate a SQL query for your question. Please try rephrasing it."
    
    results = vanna_service.run_sql(sql)
    if results is None:
        return "I couldn't execute the query. Please check the question and try again."
    
    response = vanna_service.generate_response(question, sql, results)
    
    return response


def document_rag_tool(query: str) -> str:
    """
    Use this for questions about properties, real estate, project details, or brochure content.
    """
    document_service = get_document_service()
    
    results = document_service.search_documents(query, n_results=5)
    
    if not results:
        return "I couldn't find any relevant information in the uploaded documents. Please try a different query or upload more documents."
    
    context = "\n\n".join([
        f"Document: {r['metadata'].get('filename', 'Unknown')}\n{r['content']}"
        for r in results
    ])
    
    prompt = f"""Based on the following context from property brochures, answer the user's question accurately.

Context:
{context}

Question: {query}

Provide a clear and accurate answer based only on the context provided. If the context doesn't contain enough information, say so."""
    
    response = llm.invoke([HumanMessage(content=prompt)])
    
    return response.content


class SimpleAgent:
    """Routes queries to either T2SQL or RAG."""
    
    def __init__(self):
        self.llm = llm
    
    def route_query(self, query: str) -> Literal["t2sql", "rag"]:
        """Figure out if this should go to T2SQL or RAG."""
        query_lower = query.lower()
        
        # Keywords that suggest T2SQL
        sql_keywords = [
            "lead", "leads", "contact", "contacts", "crm", "database",
            "query", "count", "sum", "average", "total", "list", "show",
            "how many", "what is the", "who", "which", "top", "bottom"
        ]
        
        # Keywords that suggest RAG (document search)
        rag_keywords = [
            "property", "properties", "brochure", "project", "development",
            "location", "amenities", "floor", "unit", "price", "square feet",
            "bedroom", "bathroom", "parking", "view", "beachfront", "apartment",
            "condo", "residential", "commercial", "address", "details", "specifications"
        ]
        
        sql_score = sum(1 for keyword in sql_keywords if keyword in query_lower)
        rag_score = sum(1 for keyword in rag_keywords if keyword in query_lower)
        
        # If scores are close, ask LLM to decide
        if self.llm and abs(sql_score - rag_score) <= 1:
            routing_prompt = f"""Determine if this query should use:
1. Text-to-SQL (T2SQL): For queries about CRM data, leads, contacts, database records
2. Document RAG: For queries about properties, real estate, brochures, project details

Query: {query}

Respond with only 't2sql' or 'rag'."""
            
            try:
                response = self.llm.invoke([HumanMessage(content=routing_prompt)])
                decision = response.content.lower().strip()
                if "t2sql" in decision or "sql" in decision:
                    return "t2sql"
                elif "rag" in decision:
                    return "rag"
            except Exception as e:
                print(f"Error in LLM routing: {e}")
        
        # Default to whichever has higher score
        if sql_score > rag_score:
            return "t2sql"
        elif rag_score > sql_score:
            return "rag"
        else:
            # Default to T2SQL if unclear
            return "t2sql"
    
    def invoke(self, state: Dict[str, Any], config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run the agent."""
        query = state.get("query", "")
        
        if not query:
            return {
                "query": query,
                "query_type": "unknown",
                "response": "No query provided",
                "metadata": {}
            }
        
        query_type = self.route_query(query)
        
        try:
            if query_type == "t2sql":
                response = text_to_sql_tool(query)
                metadata = {"tool": "text_to_sql_tool"}
            else:  # rag
                response = document_rag_tool(query)
                metadata = {"tool": "document_rag_tool"}
            
            return {
                "query": query,
                "query_type": query_type,
                "response": response,
                "metadata": metadata
            }
        except Exception as e:
            return {
                "query": query,
                "query_type": query_type,
                "response": f"Error executing query: {str(e)}",
                "metadata": {"error": str(e)}
            }


# Singleton agent instance
_agent = None

def get_agent() -> SimpleAgent:
    """Get the agent instance (creates it if needed)."""
    global _agent
    if _agent is None:
        _agent = SimpleAgent()
    return _agent

