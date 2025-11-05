"""
Database service for setting up sample CRM schema and managing database connections.
"""

import sqlite3
from pathlib import Path
from django.conf import settings
from django.db import connection


class DatabaseService:
    """Service for managing database operations and sample data."""
    
    @staticmethod
    def initialize_sample_schema():
        """Initialize sample CRM schema with leads data for T2SQL demonstration."""
        with connection.cursor() as cursor:
            # Create leads table (matching Vanna training)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    phone TEXT,
                    company TEXT,
                    potential_value DECIMAL(10, 2),
                    status TEXT,
                    source TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create contacts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS contacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lead_id INTEGER,
                    interaction_date DATE,
                    interaction_type TEXT,
                    notes TEXT,
                    FOREIGN KEY (lead_id) REFERENCES leads(id)
                )
            """)
            
            # Insert sample data
            cursor.execute("SELECT COUNT(*) FROM leads")
            if cursor.fetchone()[0] == 0:
                sample_leads = [
                    ("John Doe", "john.doe@example.com", "+1234567890", "Tech Corp", 50000.00, "Qualified", "Website"),
                    ("Jane Smith", "jane.smith@example.com", "+1234567891", "Finance Inc", 75000.00, "Contacted", "Referral"),
                    ("Bob Johnson", "bob.johnson@example.com", "+1234567892", "Sales Co", 30000.00, "New", "Social Media"),
                    ("Alice Brown", "alice.brown@example.com", "+1234567893", "Marketing Ltd", 90000.00, "Qualified", "Website"),
                    ("Charlie Wilson", "charlie.wilson@example.com", "+1234567894", "Consulting Group", 60000.00, "Contacted", "Referral"),
                    ("Diana Martinez", "diana.martinez@example.com", "+1234567895", "Innovation Labs", 45000.00, "New", "Website"),
                    ("Eve Anderson", "eve.anderson@example.com", "+1234567896", "Digital Solutions", 80000.00, "Qualified", "Social Media"),
                    ("Frank Taylor", "frank.taylor@example.com", "+1234567897", "Enterprise Systems", 55000.00, "Contacted", "Referral"),
                ]
                
                cursor.executemany("""
                    INSERT INTO leads (name, email, phone, company, potential_value, status, source)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, sample_leads)
                
            
            connection.commit()
    
    @staticmethod
    def get_connection():
        """Get database connection."""
        return connection

