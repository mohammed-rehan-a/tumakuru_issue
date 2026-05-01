from django.urls import path
from . import views

urlpatterns = [
    path('', views.report_list, name='report_list'),
    path('submit/', views.submit_report, name='submit_report'),
    path('save-environment/', views.save_environment, name='save_environment'),
    path('tree-certificate/<int:pk>/', views.tree_certificate_detail, name='tree_certificate_detail'),
    path('tree-milestone/<int:pk>/', views.tree_milestone_certificate_detail, name='tree_milestone_certificate_detail'),
    path('tree-milestone/<int:pk>/download/', views.download_tree_milestone_certificate, name='download_tree_milestone_certificate'),
    path('<int:pk>/', views.report_detail, name='report_detail'),
    path('<int:pk>/upvote/', views.upvote_report, name='upvote_report'),
    path('<int:pk>/feedback/', views.submit_feedback, name='submit_feedback'),
    path('my-reports/', views.my_reports, name='my_reports'),
    path('certificate/<int:pk>/', views.certificate_detail, name='certificate_detail'),
    path('certificate/<int:pk>/download/', views.download_certificate, name='download_certificate'),
    path('ai-suggest/', views.ai_suggest_category, name='ai_suggest_category'),
    path('chatbot/', views.chatbot_response, name='chatbot_response'),
    path('analytics/', views.analytics_dashboard, name='analytics_dashboard'),
    path('volunteer/', views.volunteer_list, name='volunteer_list'),
    path('volunteer/<int:task_id>/signup/', views.volunteer_signup, name='volunteer_signup'),
]
