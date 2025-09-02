from django.urls import path
from . import views

app_name = 'file_upload'

urlpatterns = [
    path('', views.get_uploaded_files, name='get_uploaded_files'),
    path('upload/', views.upload_file, name='upload_file'),
    path('details/<str:file_id>/', views.get_file_details, name='get_file_details'),
    path('delete/<str:file_id>/', views.delete_file, name='delete_file'),
]
