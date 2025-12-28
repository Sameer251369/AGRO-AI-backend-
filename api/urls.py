from django.urls import path
from . import views

# Standardized as v1 for better scalability
urlpatterns = [
    # Disease Data
    path('v1/diseases/', views.diseases_list, name='diseases-list'),
    path('v1/diseases/<int:pk>/', views.disease_detail, name='disease-detail'),
    path('v1/diseases/<int:pk>/options/', views.disease_options, name='disease-options'),
    
    # AI & Tools
    path('v1/predict/', views.predict, name='predict'),
    path('v1/chat/', views.chat_view, name='chat'),
    path('v1/contact/', views.contact_view, name='contact'),
    
    # Authentication
    path('v1/register/', views.register_view, name='register'),
    path('v1/login/', views.login_view, name='login'),
    path('v1/logout/', views.logout_view, name='logout'),
    path('v1/me/', views.me_view, name='me'),
]