"""
URL configuration for proplens_challenge project.
"""

from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from ninja import NinjaAPI
# Use simplified MVP views for now
from api.views_mvp import api_router

# Create the main API instance
api = NinjaAPI(
    title="Proplens AI Agent API",
    description="Intelligent agent orchestrated using LangGraph for Text-to-SQL and Document RAG",
    version="1.0.0",
)

# Include the API router
api.add_router("/", api_router)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', api.urls),
    path('', TemplateView.as_view(template_name='chat.html'), name='chat'),
    path('chat/', TemplateView.as_view(template_name='chat.html'), name='chat'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

