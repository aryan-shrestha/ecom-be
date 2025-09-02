from django.contrib import admin
from .models import UploadedFile


@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    list_display = ['original_filename', 'file_id', 'folder',
                    'file_type', 'file_size', 'uploaded_by', 'uploaded_at']
    list_filter = ['folder', 'file_type', 'file_format', 'uploaded_at']
    search_fields = ['original_filename', 'file_id']
    readonly_fields = ['file_id', 'file_url', 'secure_url',
                       'file_size', 'width', 'height', 'uploaded_at']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('uploaded_by')
