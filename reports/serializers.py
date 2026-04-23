from rest_framework import serializers
from .models import IssueCategory, IssueReport

class IssueCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = IssueCategory
        fields = '__all__'

class IssueReportSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    citizen_name = serializers.CharField(source='citizen.get_full_name', read_only=True)
    status_color = serializers.CharField(source='get_status_color', read_only=True)
    priority_color = serializers.CharField(source='get_priority_color', read_only=True)

    class Meta:
        model = IssueReport
        fields = [
            'id', 'report_id', 'citizen', 'citizen_name', 'category', 'category_name',
            'title', 'description', 'location', 'ward_number', 'landmark',
            'latitude', 'longitude', 'image', 'image2', 'status', 'status_color',
            'priority', 'priority_color', 'points_awarded', 'created_at', 'updated_at',
            'resolved_at', 'admin_remarks', 'assigned_to', 'upvotes'
        ]
        read_only_fields = ['report_id', 'citizen', 'status', 'points_awarded', 'upvotes']
