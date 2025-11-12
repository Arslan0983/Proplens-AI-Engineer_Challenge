"""
Text-to-SQL service using Vanna framework with ChromaDB.
"""

import logging
import os
import sqlite3
from typing import Optional, Dict, Any, List
from django.conf import settings
from vanna.chromadb import ChromaDB_VectorStore
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
import chromadb
from .database_service import DatabaseService

logger = logging.getLogger('api.services')


class GeminiChromaVanna(ChromaDB_VectorStore):
    """Custom Vanna class combining ChromaDB vector store with Google Gemini LLM."""
    
    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        self.llm = ChatGoogleGenerativeAI(
            model=config.get('model', 'gemini-2.0-flash-exp') if config else 'gemini-2.0-flash-exp',
            google_api_key=config.get('api_key', '') if config else '',
            temperature=0.1
        )
    
    def system_message(self, message: str) -> dict:
        return {"role": "system", "content": message}
    
    def user_message(self, message: str) -> dict:
        return {"role": "user", "content": message}
    
    def assistant_message(self, message: str) -> dict:
        return {"role": "assistant", "content": message}
    
    def submit_prompt(self, prompt, **kwargs) -> str:
        """Submit prompt to Gemini LLM."""
        try:
            # Convert prompt to messages format if needed
            if isinstance(prompt, str):
                messages = [HumanMessage(content=prompt)]
            elif isinstance(prompt, list):
                # Convert list of dicts to LangChain messages
                messages = []
                for msg in prompt:
                    if isinstance(msg, dict):
                        messages.append(HumanMessage(content=msg.get('content', '')))
                    else:
                        messages.append(HumanMessage(content=str(msg)))
            else:
                messages = [HumanMessage(content=str(prompt))]
            
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"Error in submit_prompt: {e}")
            raise


class VannaService:
    """Text-to-SQL using Vanna framework with ChromaDB vector store."""
    
    def __init__(self):
        self.vanna_model = None
        self.db_path = None
        self._initialize()
    
    def _initialize(self):
        """Initialize Vanna with ChromaDB."""
        try:
            DatabaseService.initialize_sample_schema()
            
            db_uri = self._get_db_uri()
            self.db_path = db_uri.replace('sqlite:///', '')
            
            # Initialize custom Vanna with ChromaDB + Gemini
            chroma_config = {
                'model': settings.GEMINI_MODEL,
                'api_key': settings.GEMINI_API_KEY,
                'client': chromadb.CloudClient(
                    api_key=settings.CHROMADB_API_KEY,
                    tenant=settings.CHROMADB_TENANT,
                    database=settings.CHROMADB_DATABASE
                ),
                'collection_name': 'vanna_training'
            }
            
            self.vanna_model = GeminiChromaVanna(config=chroma_config)
            
            # Connect to SQLite database
            self.vanna_model.connect_to_sqlite(self.db_path)
            
            # Train if needed
            self._train_if_needed()
            
        except Exception as e:
            logger.error(f"Error initializing Vanna: {e}", exc_info=True)
            self.vanna_model = None
    
    def _get_db_uri(self) -> str:
        """Get database connection URI."""
        db_settings = settings.DATABASES['default']
        if 'sqlite3' in db_settings['ENGINE']:
            db_path = db_settings['NAME']
            return f"sqlite:///{db_path}"
        else:
            user = db_settings['USER']
            password = db_settings['PASSWORD']
            host = db_settings['HOST']
            port = db_settings['PORT']
            name = db_settings['NAME']
            return f"postgresql://{user}:{password}@{host}:{port}/{name}"
    
    def _get_database_schema(self) -> Dict[str, str]:
        """Read actual database schema and generate DDL."""
        schemas = {}
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
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
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                ddl_parts = [f"CREATE TABLE {table_name} ("]
                column_defs = []
                
                for col in columns:
                    col_id, col_name, col_type, not_null, default_val, is_pk = col
                    col_def = f"    {col_name} {col_type or 'TEXT'}"
                    if is_pk:
                        if col_type and col_type.upper() == 'INTEGER':
                            col_def += " PRIMARY KEY AUTOINCREMENT"
                        else:
                            col_def += " PRIMARY KEY"
                    if not_null and not is_pk:
                        col_def += " NOT NULL"
                    if default_val:
                        col_def += f" DEFAULT {default_val}"
                    column_defs.append(col_def)
                
                ddl_parts.append(",\n".join(column_defs))
                ddl_parts.append(");")
                schemas[table_name] = "\n".join(ddl_parts)
            
            conn.close()
        except Exception as e:
            print(f"Error reading database schema: {e}")
        
        return schemas
    
    def _train_if_needed(self):
        """Train Vanna with database schema using DDL."""
        if not self.vanna_model:
            return
        
        try:
            # Check if already trained
            training_data = self.vanna_model.get_training_data()
            if training_data and len(training_data) > 0:
                logger.info(f"Vanna already trained with {len(training_data)} examples")
                return
            
            logger.info("Training Vanna with database schema...")
            
            # Get schema and train with DDL
            schemas = self._get_database_schema()
            
            for table_name, ddl in schemas.items():
                # Add DDL to Vanna - catch errors to prevent blocking
                try:
                    self.vanna_model.train(ddl=ddl)
                    logger.info(f"  Trained on table: {table_name}")
                except Exception as train_error:
                    logger.warning(f"  Failed to train on table {table_name} (non-blocking): {train_error}")
                    # Continue with other tables instead of crashing
                    continue
            
            logger.info("Vanna training completed (or skipped due to errors)")
            
        except Exception as e:
            logger.warning(f"Vanna training error (non-blocking): {e}", exc_info=True)
            # Don't crash - service will work but SQL generation may be limited
    
    def generate_sql(self, question: str) -> Optional[str]:
        """Generate SQL using Vanna framework."""
        if not self.vanna_model:
            return None
        
        try:
            sql = self.vanna_model.generate_sql(question=question)
            return sql
        except Exception as e:
            logger.error(f"Error generating SQL with Vanna: {e}", exc_info=True)
            return None
    
    def run_sql(self, sql: str) -> Optional[list]:
        """Execute SQL query using Vanna."""
        if not self.vanna_model:
            return None
        
        try:
            # Use Vanna's run_sql
            df = self.vanna_model.run_sql(sql=sql)
            
            # Convert DataFrame to list of dicts
            if df is not None and not df.empty:
                return df.to_dict('records')
            return []
        except Exception as e:
            print(f"Error executing SQL with Vanna: {e}")
            return None
    
    def generate_response(self, question: str, sql: str, results: list) -> str:
        """Generate natural language response using Vanna."""
        if not self.vanna_model:
            if results:
                return f"I found {len(results)} result(s). {str(results[:3])}"
            else:
                return "No results found for your query."
        
        try:
            # Convert results back to DataFrame for Vanna
            import pandas as pd
            df = pd.DataFrame(results) if results else pd.DataFrame()
            
            # Use Vanna's generate explanation
            response = self.vanna_model.generate_explanation(sql=sql, df=df)
            return response
        except Exception as e:
            print(f"Error generating response with Vanna: {e}")
            if results:
                return f"I found {len(results)} result(s). Here are the first few: {str(results[:3])}"
            else:
                return "No results found for your query."


# Singleton instance (lazy-loaded to avoid startup timeout)
_vanna_service = None

def get_vanna_service() -> VannaService:
    """Get Vanna service instance (lazy-loaded)."""
    global _vanna_service
    if _vanna_service is None:
        logger.info("Initializing Vanna service (first use)...")
        _vanna_service = VannaService()
        logger.info("Vanna service initialized successfully")
    return _vanna_service
