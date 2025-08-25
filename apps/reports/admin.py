from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import UserReport, PostReport, ReportAction, ReportStatistics

@admin.register(UserReport)
class UserReportAdmin(admin.ModelAdmin):
    list_display = [
        'id', 
        'reporter_link', 
        'reported_user_link', 
        'report_type', 
        'status_badge', 
        'priority_badge',
        'assigned_admin',
        'created_at',
        'age_days'
    ]
    list_filter = [
        'status', 
        'priority', 
        'report_type', 
        'created_at',
        'assigned_admin'
    ]
    search_fields = [
        'reporter__username', 
        'reported_user__username', 
        'reason',
        'admin_notes'
    ]
    readonly_fields = [
        'created_at', 
        'updated_at', 
        'response_time_display',
        'age_days'
    ]
    
    fieldsets = (
        ('Report Information', {
            'fields': (
                'reporter', 
                'reported_user', 
                'report_type', 
                'reason',
                'evidence_urls'
            )
        }),
        ('Status & Priority', {
            'fields': (
                'status', 
                'priority', 
                'assigned_admin'
            )
        }),
        ('Admin Notes', {
            'fields': ('admin_notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': (
                'created_at', 
                'updated_at', 
                'resolved_at',
                'response_time_display'
            ),
            'classes': ('collapse',)
        }),
    )
    
    actions = [
        'mark_as_investigating',
        'mark_as_resolved', 
        'mark_as_dismissed',
        'set_high_priority',
        'set_medium_priority'
    ]
    
    def reporter_link(self, obj):
        url = reverse('admin:users_user_change', args=[obj.reporter.id])
        return format_html('<a href="{}">{}</a>', url, obj.reporter.username)
    reporter_link.short_description = 'Reporter'
    
    def reported_user_link(self, obj):
        url = reverse('admin:users_user_change', args=[obj.reported_user.id])
        return format_html('<a href="{}">{}</a>', url, obj.reported_user.username)
    reported_user_link.short_description = 'Reported User'
    
    def status_badge(self, obj):
        color = obj.get_status_color()
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def priority_badge(self, obj):
        color = obj.get_priority_color()
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px;">{}</span>',
            color, obj.get_priority_display()
        )
    priority_badge.short_description = 'Priority'
    
    def age_days(self, obj):
        return f"{obj.age_in_days} days"
    age_days.short_description = 'Age'
    
    def response_time_display(self, obj):
        if obj.response_time:
            return str(obj.response_time)
        return "Not resolved yet"
    response_time_display.short_description = 'Response Time'
    
    # Admin actions
    def mark_as_investigating(self, request, queryset):
        updated = queryset.update(status='investigating')
        self.message_user(request, f'{updated} reports marked as investigating.')
    mark_as_investigating.short_description = "Mark selected reports as investigating"
    
    def mark_as_resolved(self, request, queryset):
        updated = queryset.update(status='resolved', resolved_at=timezone.now())
        self.message_user(request, f'{updated} reports marked as resolved.')
    mark_as_resolved.short_description = "Mark selected reports as resolved"
    
    def mark_as_dismissed(self, request, queryset):
        updated = queryset.update(status='dismissed', resolved_at=timezone.now())
        self.message_user(request, f'{updated} reports marked as dismissed.')
    mark_as_dismissed.short_description = "Mark selected reports as dismissed"
    
    def set_high_priority(self, request, queryset):
        updated = queryset.update(priority='high')
        self.message_user(request, f'{updated} reports set to high priority.')
    set_high_priority.short_description = "Set selected reports to high priority"
    
    def set_medium_priority(self, request, queryset):
        updated = queryset.update(priority='medium')
        self.message_user(request, f'{updated} reports set to medium priority.')
    set_medium_priority.short_description = "Set selected reports to medium priority"


@admin.register(ReportAction)
class ReportActionAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'report_link',
        'admin',
        'action_type',
        'description_short',
        'created_at'
    ]
    list_filter = [
        'action_type',
        'created_at',
        'admin'
    ]
    search_fields = [
        'report__id',
        'admin__username',
        'description'
    ]
    readonly_fields = ['created_at']
    
    def report_link(self, obj):
        url = reverse('admin:reports_userreport_change', args=[obj.report.id])
        return format_html('<a href="{}">Report #{}</a>', url, obj.report.id)
    report_link.short_description = 'Report'
    
    def description_short(self, obj):
        return obj.description[:100] + "..." if len(obj.description) > 100 else obj.description
    description_short.short_description = 'Description'


@admin.register(ReportStatistics)
class ReportStatisticsAdmin(admin.ModelAdmin):
    list_display = [
        'date',
        'total_reports',
        'pending_reports', 
        'resolved_reports',
        'avg_response_time_hours',
        'updated_at'
    ]
    list_filter = ['date']
    readonly_fields = ['created_at', 'updated_at']
    
    def has_add_permission(self, request):
        # Prevent manual creation - should be generated automatically
        return False


@admin.register(PostReport)
class PostReportAdmin(admin.ModelAdmin):
    list_display = [
        'id', 
        'reporter_link', 
        'post_link', 
        'report_type', 
        'status_badge', 
        'priority_badge',
        'assigned_admin',
        'created_at',
        'age_days'
    ]
    list_filter = [
        'status', 
        'priority', 
        'report_type', 
        'created_at',
        'assigned_admin'
    ]
    search_fields = [
        'reporter__username', 
        'post__title',
        'post__content',
        'reason',
        'admin_notes'
    ]
    readonly_fields = [
        'created_at', 
        'updated_at', 
        'response_time_display',
        'age_days'
    ]
    
    fieldsets = (
        ('Report Information', {
            'fields': (
                'reporter', 
                'post', 
                'report_type', 
                'reason',
                'additional_context'
            )
        }),
        ('Status & Priority', {
            'fields': (
                'status', 
                'priority', 
                'assigned_admin'
            )
        }),
        ('Admin Actions', {
            'fields': ('action_taken', 'admin_notes'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': (
                'created_at', 
                'updated_at', 
                'resolved_at',
                'response_time_display'
            ),
            'classes': ('collapse',)
        }),
    )
    
    actions = [
        'mark_as_investigating',
        'mark_as_resolved', 
        'mark_as_dismissed',
        'set_high_priority',
        'set_medium_priority'
    ]
    
    def reporter_link(self, obj):
        url = reverse('admin:users_user_change', args=[obj.reporter.id])
        return format_html('<a href="{}">{}</a>', url, obj.reporter.username)
    reporter_link.short_description = 'Reporter'
    
    def post_link(self, obj):
        # Create a link to view the post (you might want to create a post admin if it doesn't exist)
        return format_html(
            '<a href="#" title="{}">{}</a>', 
            obj.post.content[:100] if obj.post.content else 'No content',
            obj.post.title or f'Post {str(obj.post.id)[:8]}...'
        )
    post_link.short_description = 'Post'
    
    def status_badge(self, obj):
        color = obj.get_status_color() if hasattr(obj, 'get_status_color') else 'gray'
        colors = {
            'pending': '#fbbf24',
            'investigating': '#3b82f6',
            'resolved': '#10b981',
            'dismissed': '#6b7280',
            'escalated': '#ef4444'
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def priority_badge(self, obj):
        colors = {
            'low': '#10b981',
            'medium': '#fbbf24', 
            'high': '#f97316',
            'critical': '#ef4444'
        }
        color = colors.get(obj.priority, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px;">{}</span>',
            color, obj.get_priority_display()
        )
    priority_badge.short_description = 'Priority'
    
    def age_days(self, obj):
        return f"{obj.age_in_days} days"
    age_days.short_description = 'Age'
    
    def response_time_display(self, obj):
        if obj.response_time:
            return str(obj.response_time)
        return "Not resolved yet"
    response_time_display.short_description = 'Response Time'
    
    # Admin actions
    def mark_as_investigating(self, request, queryset):
        updated = queryset.update(status='investigating')
        self.message_user(request, f'{updated} post reports marked as investigating.')
    mark_as_investigating.short_description = "Mark selected reports as investigating"
    
    def mark_as_resolved(self, request, queryset):
        updated = queryset.update(status='resolved', resolved_at=timezone.now())
        self.message_user(request, f'{updated} post reports marked as resolved.')
    mark_as_resolved.short_description = "Mark selected reports as resolved"
    
    def mark_as_dismissed(self, request, queryset):
        updated = queryset.update(status='dismissed', resolved_at=timezone.now())
        self.message_user(request, f'{updated} post reports marked as dismissed.')
    mark_as_dismissed.short_description = "Mark selected reports as dismissed"
    
    def set_high_priority(self, request, queryset):
        updated = queryset.update(priority='high')
        self.message_user(request, f'{updated} post reports set to high priority.')
    set_high_priority.short_description = "Set selected reports to high priority"
    
    def set_medium_priority(self, request, queryset):
        updated = queryset.update(priority='medium')
        self.message_user(request, f'{updated} post reports set to medium priority.')
    set_medium_priority.short_description = "Set selected reports to medium priority"