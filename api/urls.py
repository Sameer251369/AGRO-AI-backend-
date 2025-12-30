from django.urls import path
from . import views

urlpatterns = [
    # Disease Data
    path('diseases/', views.diseases_list, name='diseases-list'),
    path('diseases/<int:pk>/', views.disease_detail, name='disease-detail'),
    path('diseases/<int:pk>/options/', views.disease_options, name='disease-options'),
    
    # AI & Tools
    path('predict/', views.predict, name='predict'),
    path('chat/', views.chat_view, name='chat'),
    path('contact/', views.contact_view, name='contact'),
    
    # Authentication
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('me/', views.me_view, name='me'),
]