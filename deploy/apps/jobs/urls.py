# startup_hub/apps/jobs/urls.py - Updated with all endpoints

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import JobTypeViewSet, JobViewSet
from . import application_views

router = DefaultRouter()
router.register(r'types', JobTypeViewSet)
router.register(r'', JobViewSet)

# URL patterns - specific endpoints MUST come before router to avoid conflicts
urlpatterns = [
    # Custom endpoints FIRST - before router to avoid pattern conflicts
    path('debug-create/', JobViewSet.as_view({'post': 'debug_create'}), name='job-debug-create'),
    path('recent/', JobViewSet.as_view({'get': 'recent'}), name='job-recent'),
    path('urgent/', JobViewSet.as_view({'get': 'urgent'}), name='job-urgent'),
    path('remote/', JobViewSet.as_view({'get': 'remote'}), name='job-remote'),
    path('filters/', JobViewSet.as_view({'get': 'filters'}), name='job-filters'),
    path('recommendations/', JobViewSet.as_view({'get': 'recommendations'}), name='job-recommendations'),
    path('my-jobs/', JobViewSet.as_view({'get': 'my_jobs'}), name='job-my-jobs'),
    path('my-applications/', JobViewSet.as_view({'get': 'my_applications'}), name='job-my-applications'),
    path('admin/', JobViewSet.as_view({'get': 'admin_list'}), name='job-admin-list'),
    path('bulk-admin/', JobViewSet.as_view({'post': 'bulk_admin'}), name='job-bulk-admin'),
    path('admin_stats/', JobViewSet.as_view({'get': 'admin_stats'}), name='job-admin-stats'),
    
    # Job-specific endpoints with dynamic IDs
    path('<int:pk>/apply/', JobViewSet.as_view({'post': 'apply'}), name='job-apply'),
    path('<int:pk>/admin/', JobViewSet.as_view({'patch': 'admin_action'}), name='job-admin-action'),
    
    # Application management endpoints
    path('<int:job_id>/applications/', application_views.get_job_applications, name='job-applications'),
    path('<int:job_id>/applications/stats/', application_views.application_statistics, name='job-application-stats'),
    path('applications/<int:application_id>/', application_views.application_detail, name='application-detail'),
    path('applications/<int:application_id>/message/', application_views.initiate_conversation_with_applicant, name='application-message'),
    path('applications/bulk-update/', application_views.bulk_update_applications, name='application-bulk-update'),
    path('my-applications-summary/', application_views.my_job_applications_summary, name='my-applications-summary'),
    
    # Router URLs LAST - for standard CRUD operations (list, create, retrieve, update, delete)
    path('', include(router.urls)),
]