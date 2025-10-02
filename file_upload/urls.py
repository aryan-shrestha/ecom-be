from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UploadedFileViewSet

app_name = 'file_upload'

router = DefaultRouter()
router.register(r'files', UploadedFileViewSet, basename='uploadedfile')

urlpatterns = [
    path('', include(router.urls)),
]
