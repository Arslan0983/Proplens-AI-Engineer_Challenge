"""
Management command to load CRM leads from Excel file.
"""

from django.core.management.base import BaseCommand
from api.services.lead_service import LeadService
from pathlib import Path
import os


class Command(BaseCommand):
    help = 'Load CRM leads from Excel file'

    def add_arguments(self, parser):
        parser.add_argument(
            'file_path',
            type=str,
            help='Path to the Excel file containing CRM leads'
        )

    def handle(self, *args, **options):
        file_path = options['file_path']
        
        # Check if file exists
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'File not found: {file_path}'))
            return
        
        self.stdout.write(f'Loading leads from {file_path}...')
        
        try:
            count = LeadService.load_leads_from_excel(file_path)
            self.stdout.write(
                self.style.SUCCESS(f'Successfully loaded {count} leads')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error loading leads: {e}')
            )

