from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import routers
from reports import views as report_views
from reports.api import IssueCategoryViewSet, IssueReportViewSet, CitizenProfileViewSet
from django.contrib.sitemaps.views import sitemap
from reports.sitemaps import StaticViewSitemap, IssueReportSitemap
from django.views.generic import TemplateView

sitemaps = {
    'static': StaticViewSitemap,
    'reports': IssueReportSitemap,
}

# API Router
router = routers.DefaultRouter()
router.register(r'categories', IssueCategoryViewSet, basename='category')
router.register(r'reports', IssueReportViewSet, basename='report')
router.register(r'profile', CitizenProfileViewSet, basename='profile')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', report_views.home, name='home'),
    path('dashboard/', report_views.dashboard, name='dashboard'),
    path('accounts/', include('accounts.urls')),
    path('reports/', include('reports.urls')),
    path('leaderboard/', report_views.leaderboard, name='leaderboard'),
    path('emergency/', report_views.emergency_contacts, name='emergency'),
    path('statistics/', report_views.ward_statistics, name='statistics'),
    path('api/v1/', include(router.urls)),
    path('i18n/', include('django.conf.urls.i18n')),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', report_views.robots_txt),
    path('portfolio/', report_views.portfolio, name='portfolio'),
    path('nagesh-portfolio/', report_views.nagesh_portfolio, name='nagesh_portfolio'),
    path('google1ce7ce4bdb96776c.html', TemplateView.as_view(template_name="google1ce7ce4bdb96776c.html", content_type="text/html")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = "Tumakuru City Corporation — Admin"
admin.site.site_title = "TCC Admin Portal"
admin.site.index_title = "Civic Issue Management"
