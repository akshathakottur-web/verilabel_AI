
from rest_framework import serializers

from .models import Scan


class ScanSerializer(serializers.ModelSerializer):
    scan_id = serializers.IntegerField(source='id', read_only=True)
    batch_id = serializers.IntegerField(read_only=True)
    image_url = serializers.SerializerMethodField()
    uploaded_by = serializers.SerializerMethodField()
    score = serializers.SerializerMethodField()
    review = serializers.SerializerMethodField()

    class Meta:
        model = Scan
        fields = [
            'scan_id',
            'batch_id',
            'status',
            'image_url',
            'uploaded_by',
            'created_at',
            'product_name',
            'score',
            'extracted_fields',
            'compliance_result',
            'review',
        ]

    def get_image_url(self, obj):
        return obj.image.url if obj.image else None

    def get_uploaded_by(self, obj):
        user = obj.uploaded_by
        return {'user_id': user.username, 'name': user.name, 'role': user.role}

    def get_score(self, obj):
        result = obj.compliance_result or {}
        return result.get('score')

        
    def get_review(self, obj):
        return {
            'status': obj.review_status,
            'reviewed_by': obj.reviewed_by.username if obj.reviewed_by else None,
            'reviewed_at': obj.reviewed_at,
            'review_note': obj.review_note,
        }
