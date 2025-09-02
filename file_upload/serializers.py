from rest_framework import serializers
from .models import UploadedFile


class FileUploadSerializer(serializers.Serializer):
    """Serializer for file upload requests"""
    file = serializers.FileField()
    folder = serializers.ChoiceField(
        choices=UploadedFile.FOLDER_CHOICES,
        default='general',
        required=False
    )
    custom_filename = serializers.CharField(max_length=255, required=False)


class UploadedFileSerializer(serializers.ModelSerializer):
    """Serializer for uploaded file metadata response"""

    class Meta:
        model = UploadedFile
        fields = [
            'id', 'file_id', 'original_filename', 'file_url',
            'secure_url', 'folder', 'file_type', 'file_format',
            'file_size', 'width', 'height', 'uploaded_at'
        ]
        read_only_fields = ['id', 'uploaded_at']
