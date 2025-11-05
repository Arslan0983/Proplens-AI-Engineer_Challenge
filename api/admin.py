"""
Django admin configuration.
"""

from django.contrib import admin
from .models import QueryHistory, Document


@admin.register(QueryHistory)
class QueryHistoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'query_type', 'query', 'created_at']
    list_filter = ['query_type', 'created_at']
    search_fields = ['query', 'response']
    readonly_fields = ['created_at']


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['id', 'filename', 'file_type', 'chunk_count', 'uploaded_at']
    list_filter = ['file_type', 'uploaded_at']
    search_fields = ['filename']
    readonly_fields = ['uploaded_at']

