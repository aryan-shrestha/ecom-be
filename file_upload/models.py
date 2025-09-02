from django.db import models
from django.contrib.auth.models import User
import cloudinary.models


class UploadedFile(models.Model):
    """Model to track uploaded files metadata"""

    FOLDER_CHOICES = [
        ('products', 'Products'),
        ('categories', 'Categories'),
        ('users', 'Users'),
        ('general', 'General'),
    ]

    file_id = models.CharField(
        max_length=255, unique=True)  # Cloudinary public_id
    original_filename = models.CharField(max_length=255)
    file_url = models.URLField()
    secure_url = models.URLField()
    folder = models.CharField(
        max_length=50, choices=FOLDER_CHOICES, default='general')
    file_type = models.CharField(max_length=10)  # image, video, etc.
    file_format = models.CharField(max_length=10)  # jpg, png, mp4, etc.
    file_size = models.IntegerField()  # in bytes
    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    uploaded_by = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.original_filename} - {self.file_id}"
