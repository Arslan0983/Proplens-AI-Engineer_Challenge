"""
Database models.
"""

from django.db import models


class QueryHistory(models.Model):
    """Keep track of all queries for analytics."""
    query = models.TextField()
    query_type = models.CharField(max_length=20)  # 't2sql' or 'rag'
    response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Query Histories'

    def __str__(self):
        return f"{self.query_type}: {self.query[:50]}"


class Document(models.Model):
    """Metadata for uploaded brochures."""
    filename = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500)
    file_type = models.CharField(max_length=50)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    chunk_count = models.IntegerField(default=0)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.filename


# Lead Nurturing Models

class CRMLead(models.Model):
    """Lead data from the Excel file."""
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True, null=True)
    project_enquired = models.CharField(max_length=255, blank=True, null=True)
    budget_min = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    budget_max = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    unit_type = models.CharField(max_length=100, blank=True, null=True)
    lead_status = models.CharField(max_length=100, blank=True, null=True)
    last_conversation_date = models.DateField(blank=True, null=True)
    last_conversation_summary = models.TextField(blank=True, null=True)
    family_size = models.CharField(max_length=50, blank=True, null=True)
    purchase_motive = models.TextField(blank=True, null=True)
    financing_preference = models.CharField(max_length=100, blank=True, null=True)
    location_preference = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-last_conversation_date', '-created_at']
        verbose_name = 'CRM Lead'
        verbose_name_plural = 'CRM Leads'

    def __str__(self):
        return f"{self.name} - {self.project_enquired or 'No Project'}"


class Campaign(models.Model):
    """Lead nurturing campaign."""
    name = models.CharField(max_length=255)
    campaign_project = models.CharField(max_length=255)  # Project being marketed
    message_channel = models.CharField(max_length=20, choices=[
        ('email', 'Email'),
        ('whatsapp', 'WhatsApp')
    ], default='email')
    sales_offer = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class CampaignLead(models.Model):
    """Leads shortlisted for a campaign."""
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='campaign_leads')
    lead = models.ForeignKey(CRMLead, on_delete=models.CASCADE, related_name='campaigns')
    message_sent = models.BooleanField(default=False)
    message_sent_at = models.DateTimeField(blank=True, null=True)
    responded = models.BooleanField(default=False)
    goal_achieved = models.BooleanField(default=False)  # Visit/call scheduled
    goal_achieved_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['campaign', 'lead']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.campaign.name} - {self.lead.name}"


class CampaignMessage(models.Model):
    """Messages sent to leads in a campaign."""
    campaign_lead = models.ForeignKey(CampaignLead, on_delete=models.CASCADE, related_name='messages')
    message_type = models.CharField(max_length=20, choices=[
        ('outbound', 'Outbound (System to Lead)'),
        ('inbound', 'Inbound (Lead to System)')
    ])
    content = models.TextField()
    is_ai_generated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.campaign_lead} - {self.message_type} - {self.created_at}"


class ScheduledVisit(models.Model):
    """Scheduled property visits or calls."""
    campaign_lead = models.ForeignKey(CampaignLead, on_delete=models.CASCADE, related_name='scheduled_visits')
    visit_type = models.CharField(max_length=20, choices=[
        ('property_visit', 'Property Visit'),
        ('sales_call', 'Sales Call')
    ])
    scheduled_date = models.DateTimeField()
    sales_associate_email = models.EmailField()
    notified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['scheduled_date']

    def __str__(self):
        return f"{self.campaign_lead.lead.name} - {self.visit_type} - {self.scheduled_date}"

