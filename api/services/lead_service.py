"""
Handles filtering leads and loading them from Excel.
"""

import pandas as pd
from typing import List, Dict, Any, Optional
from django.db.models import Q
from datetime import datetime, timedelta
from api.models import CRMLead


class LeadService:
    """Filters and loads CRM leads."""
    
    @staticmethod
    def load_leads_from_excel(file_path: str) -> int:
        """
        Load leads from Excel into the database.
        Returns how many were loaded.
        """
        try:
            df = pd.read_excel(file_path)
            
            # Clean up column names - keep original case for matching
            df.columns = df.columns.str.strip()
            
            # Create lowercase mapping for easier access
            col_map = {col.lower(): col for col in df.columns}
            
            count = 0
            for _, row in df.iterrows():
                # Map Excel columns to database fields using the column mapping
                name_col = col_map.get('lead name', 'Lead name')
                email_col = col_map.get('email', 'Email')
                phone_col = col_map.get('phone', 'Phone')
                country_code_col = col_map.get('country code', 'Country code')
                project_col = col_map.get('project name', 'Project name')
                unit_type_col = col_map.get('unit type', 'Unit type')
                lead_status_col = col_map.get('lead status', 'Lead status')
                last_conversation_summary_col = col_map.get('last conversation summary', 'Last conversation summary')
                
                name = row.get(name_col, '') if pd.notna(row.get(name_col, '')) else ''
                email = row.get(email_col, '') if pd.notna(row.get(email_col, '')) else ''
                phone_val = row.get(phone_col, None)
                if pd.notna(phone_val):
                    country_code = row.get(country_code_col, None)
                    if pd.notna(country_code):
                        phone = f"+{country_code}{phone_val}"
                    else:
                        phone = str(phone_val)
                else:
                    phone = None
                
                project = row.get(project_col, None) if pd.notna(row.get(project_col, None)) else None
                unit_type = row.get(unit_type_col, None) if pd.notna(row.get(unit_type_col, None)) else None
                lead_status = row.get(lead_status_col, None) if pd.notna(row.get(lead_status_col, None)) else None
                last_conversation_summary = row.get(last_conversation_summary_col, None) if pd.notna(row.get(last_conversation_summary_col, None)) else None
                
                lead_data = {
                    'name': name if pd.notna(name) else '',
                    'email': email if pd.notna(email) else '',
                    'phone': phone,
                    'project_enquired': project if pd.notna(project) else None,
                    'unit_type': unit_type if pd.notna(unit_type) else None,
                    'lead_status': lead_status if pd.notna(lead_status) else None,
                    'last_conversation_summary': last_conversation_summary if pd.notna(last_conversation_summary) else None,
                    'family_size': None,  # Not in current Excel
                    'purchase_motive': None,  # Not in current Excel
                    'financing_preference': None,  # Not in current Excel
                    'location_preference': None,  # Not in current Excel
                }
                
                # Handle last conversation date
                last_conv_date_col = col_map.get('last conversation date', 'Last conversation date')
                last_conv_date = row.get(last_conv_date_col, None)
                if pd.notna(last_conv_date):
                    if isinstance(last_conv_date, pd.Timestamp):
                        lead_data['last_conversation_date'] = last_conv_date.date()
                    else:
                        try:
                            from datetime import datetime
                            lead_data['last_conversation_date'] = pd.to_datetime(last_conv_date).date()
                        except:
                            lead_data['last_conversation_date'] = None
                else:
                    lead_data['last_conversation_date'] = None
                
                # Handle budget - check both min/max budget columns and combined budget column
                budget_min_col = col_map.get('min. budget', 'Min. Budget')
                budget_max_col = col_map.get('max budget', 'Max Budget')
                budget_min = row.get(budget_min_col, None)
                budget_max = row.get(budget_max_col, None)
                
                if pd.notna(budget_min):
                    try:
                        # Remove commas and convert
                        budget_min_str = str(budget_min).replace(',', '').strip()
                        lead_data['budget_min'] = float(budget_min_str)
                    except:
                        lead_data['budget_min'] = None
                else:
                    lead_data['budget_min'] = None
                
                if pd.notna(budget_max):
                    try:
                        budget_max_str = str(budget_max).replace(',', '').strip()
                        lead_data['budget_max'] = float(budget_max_str)
                    except:
                        lead_data['budget_max'] = None
                else:
                    lead_data['budget_max'] = None
                
                # If no separate min/max, try combined budget column
                if not lead_data.get('budget_min') and not lead_data.get('budget_max'):
                    budget = row.get('budget', None)
                    if pd.notna(budget):
                        if isinstance(budget, (int, float)):
                            lead_data['budget_min'] = float(budget)
                            lead_data['budget_max'] = float(budget)
                        elif isinstance(budget, str) and '-' in budget:
                            parts = budget.split('-')
                            if len(parts) == 2:
                                try:
                                    lead_data['budget_min'] = float(parts[0].replace(',', '').strip())
                                    lead_data['budget_max'] = float(parts[1].replace(',', '').strip())
                                except:
                                    pass
                
                # Create or update lead (based on email)
                lead, created = CRMLead.objects.update_or_create(
                    email=lead_data['email'],
                    defaults=lead_data
                )
                
                if created:
                    count += 1
            
            return count
            
        except Exception as e:
            print(f"Error loading leads from Excel: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    @staticmethod
    def filter_leads(
        project_enquired: Optional[str] = None,
        budget_min: Optional[float] = None,
        budget_max: Optional[float] = None,
        unit_types: Optional[List[str]] = None,
        lead_status: Optional[str] = None,
        last_conversation_from: Optional[datetime] = None,
        last_conversation_to: Optional[datetime] = None,
    ) -> List[CRMLead]:
        """
        Filter leads based on criteria.
        At least 2 criteria must be provided.
        """
        query = Q()
        criteria_count = 0
        
        if project_enquired:
            query &= Q(project_enquired__icontains=project_enquired)
            criteria_count += 1
        
        if budget_min is not None:
            query &= Q(budget_max__gte=budget_min) | Q(budget_min__gte=budget_min)
            criteria_count += 1
        
        if budget_max is not None:
            query &= Q(budget_min__lte=budget_max) | Q(budget_max__lte=budget_max)
            criteria_count += 1
        
        if unit_types:
            query &= Q(unit_type__in=unit_types)
            criteria_count += 1
        
        if lead_status:
            query &= Q(lead_status__icontains=lead_status)
            criteria_count += 1
        
        if last_conversation_from or last_conversation_to:
            if last_conversation_from and last_conversation_to:
                query &= Q(last_conversation_date__range=[last_conversation_from.date(), last_conversation_to.date()])
            elif last_conversation_from:
                query &= Q(last_conversation_date__gte=last_conversation_from.date())
            elif last_conversation_to:
                query &= Q(last_conversation_date__lte=last_conversation_to.date())
            criteria_count += 1
        
        if criteria_count < 2:
            raise ValueError("At least 2 filter criteria must be provided")
        
        return list(CRMLead.objects.filter(query).distinct())

