from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import cloudinary
import cloudinary.uploader
import os
import uuid
from .models import UploadedFile
from .serializers import FileUploadSerializer, UploadedFileSerializer


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_file(request):
    """
    Upload a file to Cloudinary with custom folder naming
    """
    serializer = FileUploadSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(
            {'error': 'Invalid data', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    file = serializer.validated_data['file']
    folder = serializer.validated_data.get('folder', 'general')
    custom_filename = serializer.validated_data.get('custom_filename')

    try:
        # Generate a unique public_id for the file
        if custom_filename:
            # Remove file extension from custom filename
            filename_without_ext = os.path.splitext(custom_filename)[0]
            public_id = f"{folder}/{filename_without_ext}_{uuid.uuid4().hex[:8]}"
        else:
            # Use original filename without extension
            original_name = os.path.splitext(file.name)[0]
            public_id = f"{folder}/{original_name}_{uuid.uuid4().hex[:8]}"

        # Upload to Cloudinary
        upload_result = cloudinary.uploader.upload(
            file,
            public_id=public_id,
            folder=folder,
            resource_type='auto',  # Automatically detect file type
            overwrite=False
        )

        # Save metadata to database
        uploaded_file = UploadedFile.objects.create(
            file_id=upload_result['public_id'],
            original_filename=file.name,
            file_url=upload_result['url'],
            secure_url=upload_result['secure_url'],
            folder=folder,
            file_type=upload_result['resource_type'],
            file_format=upload_result['format'],
            file_size=upload_result['bytes'],
            width=upload_result.get('width'),
            height=upload_result.get('height'),
            uploaded_by=request.user
        )

        # Serialize and return the response
        response_serializer = UploadedFileSerializer(uploaded_file)

        return Response({
            'success': True,
            'message': 'File uploaded successfully',
            'data': response_serializer.data
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({
            'error': 'File upload failed',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_uploaded_files(request):
    """
    Get all uploaded files for the authenticated user
    """
    folder = request.query_params.get('folder')

    files = UploadedFile.objects.filter(uploaded_by=request.user)

    if folder:
        files = files.filter(folder=folder)

    serializer = UploadedFileSerializer(files, many=True)

    return Response({
        'success': True,
        'data': serializer.data
    })


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_file(request, file_id):
    """
    Delete a file from Cloudinary and database
    """
    try:
        uploaded_file = UploadedFile.objects.get(
            file_id=file_id,
            uploaded_by=request.user
        )

        # Delete from Cloudinary
        cloudinary.uploader.destroy(file_id, resource_type='auto')

        # Delete from database
        uploaded_file.delete()

        return Response({
            'success': True,
            'message': 'File deleted successfully'
        })

    except UploadedFile.DoesNotExist:
        return Response({
            'error': 'File not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': 'File deletion failed',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_file_details(request, file_id):
    """
    Get details of a specific uploaded file
    """
    try:
        uploaded_file = UploadedFile.objects.get(
            file_id=file_id,
            uploaded_by=request.user
        )

        serializer = UploadedFileSerializer(uploaded_file)

        return Response({
            'success': True,
            'data': serializer.data
        })

    except UploadedFile.DoesNotExist:
        return Response({
            'error': 'File not found'
        }, status=status.HTTP_404_NOT_FOUND)
