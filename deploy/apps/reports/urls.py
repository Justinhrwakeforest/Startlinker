from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    # User report endpoints
    path('users/', views.UserReportCreateView.as_view(), name='create_user_report'),
    path('users/my-reports/', views.UserReportListView.as_view(), name='my_user_reports'),
    path('users/my-reports/<int:pk>/', views.UserReportDetailView.as_view(), name='my_user_report_detail'),
    path('users/check-exists/<int:user_id>/', views.check_report_exists, name='check_user_report_exists'),
    
    # Post report endpoints
    path('posts/', views.PostReportCreateView.as_view(), name='create_post_report'),
    path('posts/my-reports/', views.PostReportListView.as_view(), name='my_post_reports'),
    path('posts/my-reports/<int:pk>/', views.PostReportDetailView.as_view(), name='my_post_report_detail'),
    path('posts/check-exists/<str:post_id>/', views.check_post_report_exists, name='check_post_report_exists'),
    
    # Admin user report endpoints
    path('admin/users/', views.AdminReportListView.as_view(), name='admin_user_report_list'),
    path('admin/users/<int:pk>/', views.AdminReportDetailView.as_view(), name='admin_user_report_detail'),
    path('admin/user-history/<int:user_id>/', views.user_report_history, name='user_report_history'),
    
    # Admin post report endpoints
    path('admin/posts/', views.AdminPostReportListView.as_view(), name='admin_post_report_list'),
    path('admin/posts/<int:pk>/', views.AdminPostReportDetailView.as_view(), name='admin_post_report_detail'),
    
    # Admin general endpoints
    path('admin/dashboard/', views.admin_dashboard_stats, name='admin_dashboard'),
    path('admin/bulk-action/', views.bulk_report_action, name='bulk_report_action'),
    path('admin/user-action/', views.admin_user_action, name='admin_user_action'),
    
    # Report actions
    path('actions/', views.ReportActionCreateView.as_view(), name='create_report_action'),
]