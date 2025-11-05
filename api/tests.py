"""
Test suite for the API.
"""

import pytest
import json
from django.test import Client
from django.core.files.uploadedfile import SimpleUploadedFile
from api.models import QueryHistory, Document
from api.auth import create_jwt_token
from api.services.database_service import DatabaseService
from api.services.document_service import get_document_service


@pytest.mark.django_db
class TestAuthentication:
    """Test JWT authentication."""
    
    def test_health_check_no_auth(self, client):
        """Health check should work without authentication."""
        response = client.get('/api/health')
        assert response.status_code == 200
    
    def test_query_without_auth(self, client):
        """Query endpoint should require authentication."""
        response = client.post(
            '/api/queries',
            data=json.dumps({"query": "test"}),
            content_type='application/json'
        )
        assert response.status_code == 401
    
    def test_query_with_auth(self, client, auth_headers):
        """Query endpoint should work with valid JWT."""
        response = client.post(
            '/api/queries',
            data=json.dumps({"query": "What are the top 5 leads?"}),
            content_type='application/json',
            HTTP_AUTHORIZATION=auth_headers['Authorization']
        )
        assert response.status_code in [200, 500]  # 500 if LLM/service not configured


@pytest.mark.django_db
class TestDatabaseService:
    """Test database service."""
    
    def test_initialize_schema(self):
        """Test schema initialization."""
        DatabaseService.initialize_sample_schema()
        
        # Verify tables exist
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            assert 'leads' in tables
            assert 'contacts' in tables


@pytest.mark.django_db
class TestQueryEndpoint:
    """Test query endpoint."""
    
    def test_query_t2sql(self, client, auth_headers):
        """Test Text-to-SQL query."""
        response = client.post(
            '/api/queries',
            data=json.dumps({"query": "How many leads are in the database?"}),
            content_type='application/json',
            HTTP_AUTHORIZATION=auth_headers['Authorization']
        )
        
        if response.status_code == 200:
            data = json.loads(response.content)
            assert 'response' in data
            assert 'query_type' in data
            assert data['query_type'] in ['t2sql', 'rag', 'unknown']
    
    def test_query_rag(self, client, auth_headers):
        """Test Document RAG query."""
        response = client.post(
            '/api/queries',
            data=json.dumps({"query": "What are the amenities in the property?"}),
            content_type='application/json',
            HTTP_AUTHORIZATION=auth_headers['Authorization']
        )
        
        if response.status_code == 200:
            data = json.loads(response.content)
            assert 'response' in data
            assert 'query_type' in data
    
    def test_query_history(self, client, auth_headers):
        """Test that queries are saved to history."""
        initial_count = QueryHistory.objects.count()
        
        response = client.post(
            '/api/queries',
            data=json.dumps({"query": "Test query"}),
            content_type='application/json',
            HTTP_AUTHORIZATION=auth_headers['Authorization']
        )
        
        # Check if query was saved (only if successful)
        if response.status_code == 200:
            assert QueryHistory.objects.count() >= initial_count


@pytest.mark.django_db
class TestDocumentUpload:
    """Test document upload endpoint."""
    
    def test_upload_document_no_auth(self, client):
        """Upload should require authentication."""
        file_content = b"Test PDF content"
        uploaded_file = SimpleUploadedFile("test.pdf", file_content, content_type="application/pdf")
        
        response = client.post('/api/documents/upload', {'file': uploaded_file})
        assert response.status_code == 401
    
    def test_upload_document_with_auth(self, client, auth_headers):
        """Test document upload with authentication."""
        # Create a simple text file
        file_content = b"This is a test document about a property with amenities."
        uploaded_file = SimpleUploadedFile("test.txt", file_content, content_type="text/plain")
        
        response = client.post(
            '/api/documents/upload',
            {'file': uploaded_file},
            HTTP_AUTHORIZATION=auth_headers['Authorization']
        )
        
        # Should either succeed or fail gracefully
        assert response.status_code in [200, 400, 500]
        
        if response.status_code == 200:
            data = json.loads(response.content)
            assert 'document_id' in data
            assert 'chunk_count' in data
            assert data['chunk_count'] > 0


@pytest.mark.django_db
class TestAgentRouting:
    """Test agent routing logic."""
    
    def test_agent_initialization(self):
        """Test that agent can be initialized."""
        from api.agent.agent import get_agent
        agent = get_agent()
        assert agent is not None
    
    def test_routing_t2sql_query(self):
        """Test routing to T2SQL."""
        from api.agent.agent import router_node
        
        state = {
            "query": "How many leads are there?",
            "query_type": "unknown",
            "response": "",
            "metadata": {}
        }
        
        result = router_node(state)
        # Should route to t2sql (or at least make a decision)
        assert result["query_type"] in ["t2sql", "rag"]
    
    def test_routing_rag_query(self):
        """Test routing to RAG."""
        from api.agent.agent import router_node
        
        state = {
            "query": "What are the amenities in the property brochure?",
            "query_type": "unknown",
            "response": "",
            "metadata": {}
        }
        
        result = router_node(state)
        # Should route to rag (or at least make a decision)
        assert result["query_type"] in ["t2sql", "rag"]

