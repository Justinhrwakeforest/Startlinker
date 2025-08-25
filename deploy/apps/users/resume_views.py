# Resume management views
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from .models import Resume
from .serializers import ResumeSerializer


@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticated])
def resume_list_create(request):
    """List user's resumes or create a new one"""
    if request.method == 'GET':
        resumes = Resume.objects.filter(user=request.user)
        serializer = ResumeSerializer(resumes, many=True, context={'request': request})
        return Response({
            'resumes': serializer.data,
            'count': resumes.count(),
            'max_allowed': 5
        })
    
    elif request.method == 'POST':
        # Check if user has reached the maximum number of resumes
        current_count = Resume.objects.filter(user=request.user).count()
        if current_count >= 5:
            return Response({
                'error': 'You can only upload up to 5 resumes. Please delete an existing resume before uploading a new one.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = ResumeSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            try:
                resume = serializer.save()
                return Response({
                    'message': 'Resume uploaded successfully',
                    'resume': ResumeSerializer(resume, context={'request': request}).data
                }, status=status.HTTP_201_CREATED)
            except ValidationError as e:
                return Response({
                    'error': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([permissions.IsAuthenticated])
def resume_detail(request, resume_id):
    """Get, update, or delete a specific resume"""
    resume = get_object_or_404(Resume, id=resume_id, user=request.user)
    
    if request.method == 'GET':
        serializer = ResumeSerializer(resume, context={'request': request})
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = ResumeSerializer(resume, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            resume = serializer.save()
            return Response({
                'message': 'Resume updated successfully',
                'resume': ResumeSerializer(resume, context={'request': request}).data
            })
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        # If this was the default resume, make another resume default if available
        if resume.is_default:
            other_resumes = Resume.objects.filter(user=request.user).exclude(id=resume_id)
            if other_resumes.exists():
                other_resumes.first().is_default = True
                other_resumes.first().save()
        
        # Delete the file from storage
        if resume.file:
            resume.file.delete()
        
        resume.delete()
        return Response({
            'message': 'Resume deleted successfully'
        }, status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def set_default_resume(request, resume_id):
    """Set a resume as default"""
    resume = get_object_or_404(Resume, id=resume_id, user=request.user)
    
    # Remove default from other resumes
    Resume.objects.filter(user=request.user, is_default=True).exclude(id=resume_id).update(is_default=False)
    
    # Set this resume as default
    resume.is_default = True
    resume.save()
    
    return Response({
        'message': 'Default resume updated successfully',
        'resume': ResumeSerializer(resume, context={'request': request}).data
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_default_resume(request):
    """Get the user's default resume"""
    try:
        resume = Resume.objects.get(user=request.user, is_default=True)
        serializer = ResumeSerializer(resume, context={'request': request})
        return Response(serializer.data)
    except Resume.DoesNotExist:
        # Try to get any resume
        resume = Resume.objects.filter(user=request.user).first()
        if resume:
            serializer = ResumeSerializer(resume, context={'request': request})
            return Response(serializer.data)
        else:
            return Response({
                'error': 'No resumes found'
            }, status=status.HTTP_404_NOT_FOUND)