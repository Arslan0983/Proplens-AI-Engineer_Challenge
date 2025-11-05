"""
Text-to-SQL service using Vanna-style RAG approach.
Reads the database schema automatically and uses RAG to find relevant SQL examples.
Based on: https://medium.com/mitb-for-all/text-to-sql-just-got-easier-meet-vanna-ai-your-rag-powered-sql-sidekick-e781c3ffb2c5
"""

import os
import sqlite3
from typing import Optional, Dict, Any, List
from django.conf import settings
import google.generativeai as genai
import chromadb
from sentence_transformers import SentenceTransformer
from .database_service import DatabaseService


class VannaService:
    """Converts natural language to SQL using RAG - reads schema automatically, no hardcoding."""
    
    def __init__(self):
        self.llm = None
        self.chroma_client = None
        self.collection = None
        self.embedder = None
        self.db_path = None
        self._initialize()
    
    def _initialize(self):
        """Set up the service - connect to DB, ChromaDB, and Gemini."""
        try:
            DatabaseService.initialize_sample_schema()
            
            db_uri = self._get_db_uri()
            self.db_path = db_uri.replace('sqlite:///', '')
            
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.llm = genai.GenerativeModel(settings.GEMINI_MODEL)
            
            # ChromaDB for storing SQL examples
            self.chroma_client = chromadb.CloudClient(
                api_key=settings.CHROMADB_API_KEY,
                tenant=settings.CHROMADB_TENANT,
                database=settings.CHROMADB_DATABASE
            )
            
            self.collection = self.chroma_client.get_or_create_collection(
                name="sql_training_data",
                metadata={"description": "Training data for Text-to-SQL with RAG"}
            )
            
            self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Train if needed
            self._train_if_needed()
            
        except Exception as e:
            print(f"Error initializing Vanna service: {e}")
            import traceback
            traceback.print_exc()
            self.llm = None
    
    def _get_db_uri(self) -> str:
        """Get the database connection URI."""
        db_settings = settings.DATABASES['default']
        if 'sqlite3' in db_settings['ENGINE']:
            db_path = db_settings['NAME']
            return f"sqlite:///{db_path}"
        else:
            # PostgreSQL
            user = db_settings['USER']
            password = db_settings['PASSWORD']
            host = db_settings['HOST']
            port = db_settings['PORT']
            name = db_settings['NAME']
            return f"postgresql://{user}:{password}@{host}:{port}/{name}"
    
    def _get_database_schema(self) -> Dict[str, str]:
        """
        Read the actual database schema and generate DDL statements.
        Returns table names mapped to their CREATE TABLE statements.
        """
        schemas = {}
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all user tables (exclude only Django system tables, include api_* model tables)
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' 
                AND name NOT LIKE 'sqlite_%'
                AND name NOT LIKE 'django_%'
                AND name NOT LIKE 'auth_%'
                AND name NOT IN ('django_migrations', 'django_content_type', 'django_session', 'django_admin_log')
                ORDER BY name
            """)
            
            tables = cursor.fetchall()
            
            for (table_name,) in tables:
                # Get table info
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                
                # Build CREATE TABLE statement
                ddl_parts = [f"CREATE TABLE {table_name} ("]
                column_defs = []
                primary_keys = []
                
                for col in columns:
                    col_id, col_name, col_type, not_null, default_val, is_pk = col
                    
                    col_def = f"    {col_name} {col_type or 'TEXT'}"
                    
                    if is_pk:
                        if col_type.upper() == 'INTEGER':
                            col_def += " PRIMARY KEY AUTOINCREMENT"
                        else:
                            col_def += " PRIMARY KEY"
                        primary_keys.append(col_name)
                    
                    if not_null and not is_pk:
                        col_def += " NOT NULL"
                    
                    if default_val:
                        col_def += f" DEFAULT {default_val}"
                    
                    column_defs.append(col_def)
                
                ddl_parts.append(",\n".join(column_defs))
                ddl_parts.append(");")
                
                schemas[table_name] = "\n".join(ddl_parts)
                
                # Get foreign keys if any
                cursor.execute(f"PRAGMA foreign_key_list({table_name})")
                foreign_keys = cursor.fetchall()
                
                if foreign_keys:
                    # Add foreign key constraints (simplified for now)
                    fk_info = []
                    for fk in foreign_keys:
                        fk_info.append(f"-- Foreign key: {fk[3]} references {fk[2]}({fk[4]})")
                    schemas[table_name] += "\n" + "\n".join(fk_info)
            
            conn.close()
            
        except Exception as e:
            print(f"Error reading database schema: {e}")
            import traceback
            traceback.print_exc()
        
        return schemas
    
    def _generate_sample_queries(self, table_name: str, columns: List[tuple]) -> List[Dict[str, str]]:
        """
        Generate sample question-SQL pairs based on actual table structure.
        """
        queries = []
        
        # Get column names and types
        col_names = [col[1] for col in columns]
        col_types = {col[1]: col[2] for col in columns}
        
        # Generate basic queries based on table structure
        if 'id' in col_names:
            # Count query
            queries.append({
                "question": f"How many records are in {table_name}?",
                "sql": f"SELECT COUNT(*) as total FROM {table_name};"
            })
            
            # List all query
            main_cols = [col for col in col_names if col not in ['id', 'created_at', 'updated_at']][:5]
            if main_cols:
                cols_str = ", ".join(main_cols)
                queries.append({
                    "question": f"Show me all records from {table_name}",
                    "sql": f"SELECT {cols_str} FROM {table_name};"
                })
        
        # Status/category queries if status-like columns exist
        status_cols = [col for col in col_names if 'status' in col.lower() or 'type' in col.lower()]
        if status_cols:
            status_col = status_cols[0]
            queries.append({
                "question": f"What are the different {status_col} values in {table_name}?",
                "sql": f"SELECT DISTINCT {status_col} FROM {table_name} WHERE {status_col} IS NOT NULL;"
            })
            
            queries.append({
                "question": f"How many records have each {status_col} in {table_name}?",
                "sql": f"SELECT {status_col}, COUNT(*) as count FROM {table_name} GROUP BY {status_col};"
            })
        
        # Source/location queries
        source_cols = [col for col in col_names if 'source' in col.lower() or 'location' in col.lower()]
        if source_cols:
            source_col = source_cols[0]
            queries.append({
                "question": f"How many records came from each {source_col} in {table_name}?",
                "sql": f"SELECT {source_col}, COUNT(*) as count FROM {table_name} GROUP BY {source_col};"
            })
        
        # Company/organization queries
        org_cols = [col for col in col_names if 'company' in col.lower() or 'organization' in col.lower()]
        if org_cols:
            org_col = org_cols[0]
            queries.append({
                "question": f"Which {org_col}s are in {table_name}?",
                "sql": f"SELECT DISTINCT {org_col} FROM {table_name} WHERE {org_col} IS NOT NULL;"
            })
        
        return queries
    
    def _train_if_needed(self):
        """Train Vanna with actual database schema and generated examples."""
        try:
            # Check if already trained
            if self.collection.count() > 0:
                print(f"Vanna-style service already trained with {self.collection.count()} examples")
                return
            
            print("Training Vanna with actual database schema...")
            
            # Step 1: Get actual database schema
            schemas = self._get_database_schema()
            
            if not schemas:
                print("Warning: No tables found in database. Cannot train Vanna.")
                return
            
            training_count = 0
            
            # Step 2: For each table, add DDL and sample queries
            for table_name, ddl in schemas.items():
                # Add DDL
                embedding = self.embedder.encode(ddl).tolist()
                self.collection.add(
                    ids=[f"ddl_{table_name}"],
                    embeddings=[embedding],
                    documents=[ddl],
                    metadatas={"type": "ddl", "table": table_name}
                )
                training_count += 1
                print(f"  Added DDL for table: {table_name}")
                
                # Get column info for generating sample queries
                try:
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = cursor.fetchall()
                    conn.close()
                    
                    # Generate sample queries based on actual table structure
                    sample_queries = self._generate_sample_queries(table_name, columns)
                    
                    # Add sample queries
                    for idx, query_data in enumerate(sample_queries):
                        text = f"{query_data['question']}\n{query_data['sql']}"
                        embedding = self.embedder.encode(text).tolist()
                        self.collection.add(
                            ids=[f"sql_{table_name}_{idx}"],
                            embeddings=[embedding],
                            documents=[text],
                            metadatas={
                                "type": "sql",
                                "table": table_name,
                                "question": query_data["question"],
                                "sql": query_data["sql"]
                            }
                        )
                        training_count += 1
                    
                    if sample_queries:
                        print(f"  Added {len(sample_queries)} sample queries for table: {table_name}")
                        
                except Exception as e:
                    print(f"  Warning: Could not generate sample queries for {table_name}: {e}")
            
            print(f"Training completed! Added {training_count} training examples from {len(schemas)} table(s).")
            
        except Exception as e:
            print(f"Error training Vanna: {e}")
            import traceback
            traceback.print_exc()
    
    def generate_sql(self, question: str) -> Optional[str]:
        """Generate SQL query from natural language question using RAG."""
        if not self.llm:
            return None
        
        try:
            # Step 1: Retrieve relevant SQL examples and DDL using RAG
            question_embedding = self.embedder.encode(question).tolist()
            results = self.collection.query(
                query_embeddings=[question_embedding],
                n_results=3
            )
            
            # Build context from retrieved examples
            context_parts = []
            if results and results['documents']:
                for doc in results['documents'][0]:
                    context_parts.append(doc)
            
            context = "\n\n".join(context_parts)
            
            # Step 2: Generate SQL using LLM with context
            prompt = f"""You are a SQL expert. Based on the following database schema and example queries, generate a SQL query for the user's question.

IMPORTANT NOTES:
- When querying CRM leads data, use the 'api_crmlead' table (not 'leads' or 'crm_leads')
- Column names in api_crmlead: lead_status (not 'status'), project_enquired (not 'project'), unit_type, budget_min, budget_max, etc.
- Always use exact column names from the schema provided in the context

Context (Database Schema and Examples):
{context}

User Question: {question}

Generate only the SQL query without any explanation. Return only valid SQL. Use exact column names from the schema."""
            
            response = self.llm.generate_content(prompt)
            sql = response.text.strip()
            
            # Clean up SQL (remove markdown code blocks if present)
            if sql.startswith("```sql"):
                sql = sql[6:]
            if sql.startswith("```"):
                sql = sql[3:]
            if sql.endswith("```"):
                sql = sql[:-3]
            sql = sql.strip()
            
            return sql
        except Exception as e:
            print(f"Error generating SQL: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def run_sql(self, sql: str) -> Optional[list]:
        """Execute SQL query and return results."""
        if not self.db_path:
            return None
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(sql)
            
            # Handle queries that don't return results
            if cursor.description is None:
                conn.commit()
                conn.close()
                return []
            
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            results = [dict(zip(columns, row)) for row in rows]
            conn.close()
            return results
        except Exception as e:
            print(f"Error executing SQL: {e}")
            return None
    
    def generate_response(self, question: str, sql: str, results: list) -> str:
        """Generate natural language response from SQL results."""
        if not self.llm:
            # Fallback response
            if results:
                return f"I found {len(results)} result(s). {str(results[:3])}"
            else:
                return "No results found for your query."
        
        try:
            # Format results for LLM
            results_str = str(results) if results else "No results"
            
            prompt = f"""Based on the following SQL query and results, provide a clear, natural language answer to the user's question.

Question: {question}
SQL Query: {sql}
Results: {results_str}

Provide a concise and informative answer."""
            
            response = self.llm.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Error generating response: {e}")
            # Fallback response
            if results:
                return f"I found {len(results)} result(s). Here are the first few: {str(results[:3])}"
            else:
                return "No results found for your query."


# Singleton instance
_vanna_service: Optional[VannaService] = None

def get_vanna_service() -> VannaService:
    """Get or create Vanna service instance."""
    global _vanna_service
    if _vanna_service is None:
        _vanna_service = VannaService()
    return _vanna_service

