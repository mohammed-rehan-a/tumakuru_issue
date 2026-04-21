from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from reports import views as report_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', report_views.home, name='home'),
    path('dashboard/', report_views.dashboard, name='dashboard'),
    path('accounts/', include('accounts.urls')),
    path('reports/', include('reports.urls')),
    path('leaderboard/', report_views.leaderboard, name='leaderboard'),
    path('emergency/', report_views.emergency_contacts, name='emergency'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = "Tumakuru City Corporation — Admin"
admin.site.site_title = "TCC Admin Portal"
admin.site.index_title = "Civic Issue Management"
