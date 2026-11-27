
from django.conf import settings
from django.db import models


class Batch(models.Model):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='batches'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Batch {self.id}'


class Scan(models.Model):
    STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('processing', 'Processing'),
        ('done', 'Done'),
        ('failed', 'Failed'),
        ('low_quality', 'Low quality'),
    ]
    REVIEW_CHOICES = [
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
    ]

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='scans'
    )
    batch = models.ForeignKey(
        Batch, null=True, blank=True, on_delete=models.SET_NULL, related_name='scans'
    )
    image = models.ImageField(upload_to='scans/')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')
    created_at = models.DateTimeField(auto_now_add=True)

    product_name = models.CharField(max_length=200, blank=True)
    vision_result = models.JSONField(null=True, blank=True)
    extracted_fields = models.JSONField(null=True, blank=True)
    compliance_result = models.JSONField(null=True, blank=True)
    score = models.IntegerField(null=True, blank=True)
    verdict = models.CharField(max_length=20, blank=True)
    error_message = models.TextField(blank=True)

    review_status = models.CharField(max_length=20, choices=REVIEW_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='reviewed_scans'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_note = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Scan {self.id} ({self.status})'
