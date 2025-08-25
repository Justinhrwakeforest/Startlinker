# Job Application Management Views for Job Posters
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import Job, JobApplication
from .serializers import JobApplicationDetailSerializer


class ApplicationPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_job_applications(request, job_id):
    """Get all applications for a specific job (job poster only)"""
    job = get_object_or_404(Job, id=job_id)
    
    # Check if user is the job poster
    if job.posted_by != request.user:
        return Response({
            'error': 'You are not authorized to view applications for this job'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Get applications with filtering options
    applications = JobApplication.objects.filter(job=job).select_related(
        'user', 'job', 'selected_resume'
    ).order_by('-applied_at')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        applications = applications.filter(status=status_filter)
    
    # Search by applicant name or email
    search = request.GET.get('search')
    if search:
        applications = applications.filter(
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(user__email__icontains=search) |
            Q(user__username__icontains=search)
        )
    
    # Paginate results
    paginator = ApplicationPagination()
    page = paginator.paginate_queryset(applications, request)
    if page is not None:
        serializer = JobApplicationDetailSerializer(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)
    
    serializer = JobApplicationDetailSerializer(applications, many=True, context={'request': request})
    return Response({
        'applications': serializer.data,
        'total_count': applications.count(),
        'job_info': {
            'id': job.id,
            'title': job.title,
            'posted_at': job.posted_at,
            'location': job.location,
            'job_type': job.job_type.name if job.job_type else None
        }
    })


@api_view(['GET', 'PUT'])
@permission_classes([permissions.IsAuthenticated])
def application_detail(request, application_id):
    """Get or update a specific application (job poster only)"""
    application = get_object_or_404(JobApplication, id=application_id)
    
    # Check if user is the job poster
    if application.job.posted_by != request.user:
        return Response({
            'error': 'You are not authorized to view this application'
        }, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'GET':
        serializer = JobApplicationDetailSerializer(application, context={'request': request})
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        # Update application status and review notes
        allowed_updates = ['status', 'review_notes', 'interview_scheduled_at', 'interview_notes']
        update_data = {k: v for k, v in request.data.items() if k in allowed_updates}
        
        # Set reviewer if status is being updated
        if 'status' in update_data:
            update_data['reviewed_by'] = request.user
            from django.utils import timezone
            update_data['reviewed_at'] = timezone.now()
        
        # Update the application
        for field, value in update_data.items():
            setattr(application, field, value)
        application.save()
        
        serializer = JobApplicationDetailSerializer(application, context={'request': request})
        return Response({
            'message': 'Application updated successfully',
            'application': serializer.data
        })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def my_job_applications_summary(request):
    """Get summary of applications for all jobs posted by the user"""
    user_jobs = Job.objects.filter(posted_by=request.user)
    
    summary = []
    for job in user_jobs:
        applications = JobApplication.objects.filter(job=job)
        
        # Count by status
        status_counts = {}
        for choice in JobApplication.STATUS_CHOICES:
            status_counts[choice[0]] = applications.filter(status=choice[0]).count()
        
        summary.append({
            'job_id': job.id,
            'job_title': job.title,
            'total_applications': applications.count(),
            'status_breakdown': status_counts,
            'recent_applications': applications.order_by('-applied_at')[:3].count(),
            'posted_at': job.posted_at,
            'is_active': job.is_active
        })
    
    return Response({
        'summary': summary,
        'total_jobs': len(summary),
        'total_applications': sum(item['total_applications'] for item in summary)
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def bulk_update_applications(request):
    """Bulk update multiple applications"""
    application_ids = request.data.get('application_ids', [])
    status_update = request.data.get('status')
    review_notes = request.data.get('review_notes', '')
    
    if not application_ids or not status_update:
        return Response({
            'error': 'application_ids and status are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Get applications that belong to user's jobs
    applications = JobApplication.objects.filter(
        id__in=application_ids,
        job__posted_by=request.user
    )
    
    if not applications.exists():
        return Response({
            'error': 'No valid applications found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Update applications
    from django.utils import timezone
    updated_count = applications.update(
        status=status_update,
        review_notes=review_notes,
        reviewed_by=request.user,
        reviewed_at=timezone.now()
    )
    
    return Response({
        'message': f'Successfully updated {updated_count} applications',
        'updated_count': updated_count
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def application_statistics(request, job_id):
    """Get detailed statistics for a specific job's applications"""
    job = get_object_or_404(Job, id=job_id)
    
    # Check if user is the job poster
    if job.posted_by != request.user:
        return Response({
            'error': 'You are not authorized to view statistics for this job'
        }, status=status.HTTP_403_FORBIDDEN)
    
    applications = JobApplication.objects.filter(job=job)
    
    # Status distribution
    status_stats = {}
    for choice in JobApplication.STATUS_CHOICES:
        count = applications.filter(status=choice[0]).count()
        status_stats[choice[1]] = count
    
    # Timeline data (applications per day for last 30 days)
    from datetime import datetime, timedelta
    from django.db.models import Count
    from django.utils import timezone
    
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    timeline_data = applications.filter(
        applied_at__date__gte=start_date
    ).extra(
        select={'day': 'date(applied_at)'}
    ).values('day').annotate(
        count=Count('id')
    ).order_by('day')
    
    # Quality metrics
    total_apps = applications.count()
    with_resume = applications.filter(
        Q(selected_resume__isnull=False) | Q(resume__isnull=False)
    ).count()
    
    avg_cover_letter_length = applications.aggregate(
        avg_length=models.Avg(models.Length('cover_letter'))
    )['avg_length'] or 0
    
    return Response({
        'job_title': job.title,
        'total_applications': total_apps,
        'status_distribution': status_stats,
        'timeline_data': list(timeline_data),
        'quality_metrics': {
            'applications_with_resume': with_resume,
            'resume_percentage': round((with_resume / total_apps * 100) if total_apps > 0 else 0, 1),
            'avg_cover_letter_length': round(avg_cover_letter_length, 0)
        },
        'recent_activity': applications.order_by('-applied_at')[:5].values(
            'id', 'user__first_name', 'user__last_name', 'applied_at', 'status'
        )
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def initiate_conversation_with_applicant(request, application_id):
    """Initiate a conversation between job poster and applicant"""
    application = get_object_or_404(JobApplication, id=application_id)
    
    # Check if user is the job poster
    if application.job.posted_by != request.user:
        return Response({
            'error': 'You are not authorized to message this applicant'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        from apps.messaging.models import Conversation
        from django.utils import timezone
        
        # Check if conversation already exists for this application
        existing_conversation = Conversation.objects.filter(
            related_job_application=application,
            conversation_type='job_application'
        ).first()
        
        if existing_conversation:
            return Response({
                'conversation_id': str(existing_conversation.id),
                'message': 'Conversation already exists',
                'exists': True
            })
        
        # Create new conversation
        conversation = Conversation.objects.create(
            created_by=request.user,
            related_job_application=application,
            conversation_type='job_application',
            group_name=f"Application: {application.job.title}"
        )
        
        # Add participants
        conversation.participants.add(request.user, application.user)
        
        # Create initial system message
        from apps.messaging.models import Message
        initial_message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=request.data.get('initial_message', 
                f"Hi {application.user.get_display_name()}, I'd like to discuss your application for the {application.job.title} position."),
            message_type='text'
        )
        
        return Response({
            'conversation_id': str(conversation.id),
            'message': 'Conversation initiated successfully',
            'exists': False,
            'initial_message_id': str(initial_message.id)
        })
        
    except Exception as e:
        return Response({
            'error': f'Failed to initiate conversation: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)