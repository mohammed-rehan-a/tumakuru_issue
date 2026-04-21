from django.contrib import admin
from .models import CitizenProfile, CitizenCertificate


@admin.register(CitizenProfile)
class CitizenProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'get_full_name', 'ward_number', 'points', 'total_reports', 'is_verified', 'joined_date']
    list_filter = ['ward_number', 'is_verified', 'joined_date']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'phone']
    readonly_fields = ['points', 'total_reports', 'joined_date']
    actions = ['verify_citizens']

    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    get_full_name.short_description = 'Full Name'

    def verify_citizens(self, request, queryset):
        queryset.update(is_verified=True)
        self.message_user(request, f'{queryset.count()} citizens verified.')
    verify_citizens.short_description = "Mark selected as Verified"


@admin.register(CitizenCertificate)
class CitizenCertificateAdmin(admin.ModelAdmin):
    list_display = ['certificate_number', 'get_citizen_name', 'milestone', 'issued_date', 'is_downloaded']
    list_filter = ['milestone', 'issued_date', 'is_downloaded']
    search_fields = ['certificate_number', 'citizen__user__first_name']
    readonly_fields = ['certificate_number', 'issued_date', 'points_at_issue']

    def get_citizen_name(self, obj):
        return obj.citizen.user.get_full_name()
    get_citizen_name.short_description = 'Citizen Name'
