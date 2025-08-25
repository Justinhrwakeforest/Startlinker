from rest_framework import serializers
from django.conf import settings
from .models import PitchDeckAnalysis


class PitchDeckAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = PitchDeckAnalysis
        fields = [
            'id', 'original_filename', 'status', 'analysis_result',
            'created_at', 'updated_at', 'is_file_available'
        ]
        read_only_fields = ['id', 'status', 'analysis_result', 'created_at', 'updated_at', 'is_file_available']


class PitchDeckUploadSerializer(serializers.ModelSerializer):
    deck_file = serializers.FileField(
        required=True,
        help_text='PDF file only, max 25MB'
    )
    
    class Meta:
        model = PitchDeckAnalysis
        fields = ['deck_file']
    
    def validate_deck_file(self, value):
        # Check file extension
        if not value.name.lower().endswith('.pdf'):
            raise serializers.ValidationError("Only PDF files are allowed.")
        
        # Check file size
        max_size_mb = settings.ANALYSIS_SETTINGS['MAX_FILE_SIZE_MB']
        if value.size > max_size_mb * 1024 * 1024:
            raise serializers.ValidationError(f"File size cannot exceed {max_size_mb}MB.")
        
        return value
    
    def create(self, validated_data):
        # Set the original filename
        validated_data['original_filename'] = validated_data['deck_file'].name
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class AnalysisListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing analyses."""
    class Meta:
        model = PitchDeckAnalysis
        fields = ['id', 'original_filename', 'status', 'created_at']
        read_only_fields = fields