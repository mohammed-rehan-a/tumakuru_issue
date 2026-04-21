from django.urls import path
from . import views

urlpatterns = [
    path('', views.report_list, name='report_list'),
    path('submit/', views.submit_report, name='submit_report'),
    path('<int:pk>/', views.report_detail, name='report_detail'),
    path('<int:pk>/upvote/', views.upvote_report, name='upvote_report'),
    path('my-reports/', views.my_reports, name='my_reports'),
    path('certificate/<int:pk>/', views.certificate_detail, name='certificate_detail'),
    path('certificate/<int:pk>/download/', views.download_certificate, name='download_certificate'),
]
