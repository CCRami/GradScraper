from rest_framework import serializers
from .models import ScrapingProgress

class ScrapingProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScrapingProgress
        fields = '__all__'