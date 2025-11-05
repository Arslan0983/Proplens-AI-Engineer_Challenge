"""
Management command to upload all brochures from the Project brochure dataset folder.
"""

import os
from django.core.management.base import BaseCommand
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from pathlib import Path
from api.services.document_service import get_document_service
from api.models import Document


class Command(BaseCommand):
    help = 'Upload all brochures from Project brochure dataset folder to ChromaDB'

    def add_arguments(self, parser):
        parser.add_argument(
            '--folder',
            type=str,
            default='Project brochure dataset',
            help='Path to folder containing brochures'
        )

    def handle(self, *args, **options):
        folder_path = options['folder']
        
        if not os.path.exists(folder_path):
            self.stdout.write(self.style.ERROR(f'Folder not found: {folder_path}'))
            return
        
        # Get all PDF and DOCX files
        brochure_files = []
        for ext in ['*.pdf', '*.docx', '*.doc']:
            brochure_files.extend(Path(folder_path).glob(ext))
        
        if not brochure_files:
            self.stdout.write(self.style.WARNING(f'No PDF/DOCX files found in {folder_path}'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'Found {len(brochure_files)} brochure files'))
        
        document_service = get_document_service()
        uploaded_count = 0
        
        for brochure_file in brochure_files:
            try:
                filename = brochure_file.name
                self.stdout.write(f'Processing {filename}...')
                
                # Check if already uploaded
                if Document.objects.filter(filename=filename).exists():
                    self.stdout.write(self.style.WARNING(f'  {filename} already uploaded, skipping'))
                    continue
                
                # Read file
                with open(brochure_file, 'rb') as f:
                    file_content = f.read()
                
                # Save to Django storage
                file_path = default_storage.save(
                    f"documents/{filename}",
                    ContentFile(file_content)
                )
                
                full_path = default_storage.path(file_path)
                file_type = brochure_file.suffix.lower().lstrip('.')
                
                # Process document (extract, chunk, embed, store in ChromaDB)
                chunk_count = document_service.process_document(full_path, filename)
                
                # Save document metadata
                Document.objects.create(
                    filename=filename,
                    file_path=file_path,
                    file_type=file_type,
                    chunk_count=chunk_count
                )
                
                uploaded_count += 1
                self.stdout.write(self.style.SUCCESS(f'  ✓ Uploaded {filename} ({chunk_count} chunks)'))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ✗ Error uploading {filename}: {str(e)}'))
                import traceback
                traceback.print_exc()
        
        self.stdout.write(self.style.SUCCESS(f'\nUploaded {uploaded_count} brochures successfully'))

