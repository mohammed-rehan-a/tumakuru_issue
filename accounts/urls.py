from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.citizen_login, name='login'),
    path('logout/', views.citizen_logout, name='logout'),
    path('profile/', views.profile, name='profile'),
]
