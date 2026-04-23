from django.contrib import admin
from django.utils.html import format_html
from .models import IssueReport, IssueCategory, IssueComment


@admin.register(IssueCategory)
class IssueCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'department', 'is_active']
    list_editable = ['is_active']


@admin.register(IssueReport)
class IssueReportAdmin(admin.ModelAdmin):
    list_display = [
        'report_id', 'title', 'get_citizen', 'category',
        'ward_number', 'status', 'priority', 'created_at', 'is_points_given'
    ]
    list_filter = ['status', 'priority', 'category', 'ward_number', 'created_at']
    search_fields = ['report_id', 'title', 'citizen__username', 'location']
    readonly_fields = ['report_id', 'created_at', 'updated_at', 'points_awarded', 'is_points_given']
    list_editable = ['status']
    date_hierarchy = 'created_at'
    actions = ['mark_resolved', 'mark_in_progress', 'mark_acknowledged']

    fieldsets = (
        ('Report Info', {
            'fields': ('report_id', 'citizen', 'category', 'title', 'description')
        }),
        ('Location', {
            'fields': ('location', 'ward_number', 'landmark', 'latitude', 'longitude')
        }),
        ('Status & Priority', {
            'fields': ('status', 'priority', 'assigned_to', 'admin_remarks')
        }),
        ('Media', {
            'fields': ('image', 'image2')
        }),
        ('Points', {
            'fields': ('points_awarded', 'is_points_given')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'resolved_at'),
            'classes': ('collapse',)
        }),
    )

    def get_citizen(self, obj):
        return obj.citizen.get_full_name() or obj.citizen.username
    get_citizen.short_description = 'Citizen'

    def colored_status(self, obj):
        colors = {
            'pending': '#FFA500',
            'acknowledged': '#2196F3',
            'in_progress': '#9C27B0',
            'resolved': '#4CAF50',
            'closed': '#607D8B',
            'rejected': '#F44336',
        }
        color = colors.get(obj.status, '#999')
        return format_html(
            '<span style="background:{};color:white;padding:3px 8px;border-radius:12px;font-size:11px">{}</span>',
            color, obj.get_status_display()
        )
    colored_status.short_description = 'Status'

    def mark_resolved(self, request, queryset):
        from django.utils import timezone
        for report in queryset:
            report.status = 'resolved'
            report.resolved_at = timezone.now()
            report.save()
    mark_resolved.short_description = "Mark as Resolved"

    def mark_in_progress(self, request, queryset):
        for report in queryset:
            report.status = 'in_progress'
            report.save()
    mark_in_progress.short_description = "Mark as In Progress"

    def mark_acknowledged(self, request, queryset):
        for report in queryset:
            report.status = 'acknowledged'
            report.save()
    mark_acknowledged.short_description = "Mark as Acknowledged"


@admin.register(IssueComment)
class IssueCommentAdmin(admin.ModelAdmin):
    list_display = ['issue', 'author' ,'is_official', 'created_at']
    list_filter = ['is_official', 'created_at']
