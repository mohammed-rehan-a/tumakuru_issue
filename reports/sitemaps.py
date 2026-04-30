from django.contrib import sitemaps
from django.urls import reverse
from .models import IssueReport

class StaticViewSitemap(sitemaps.Sitemap):
    priority = 0.5
    changefreq = 'daily'

    def items(self):
        return ['home', 'leaderboard', 'statistics', 'emergency', 'report_list', 'volunteer_list']

    def location(self, item):
        return reverse(item)

class IssueReportSitemap(sitemaps.Sitemap):
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        return IssueReport.objects.all()

    def lastmod(self, obj):
        return obj.updated_at
