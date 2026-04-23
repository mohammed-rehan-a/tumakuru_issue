from rest_framework import serializers
from django.contrib.auth.models import User
from .models import CitizenProfile

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']

class CitizenProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    level = serializers.CharField(source='get_level', read_only=True)
    progress_percentage = serializers.FloatField(read_only=True)

    class Meta:
        model = CitizenProfile
        fields = [
            'id', 'user', 'phone', 'address', 'ward_number',
            'aadhaar_last4', 'points', 'total_reports', 'is_verified',
            'joined_date', 'bio', 'level', 'progress_percentage'
        ]
