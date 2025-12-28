from django.urls import path
from . import views

urlpatterns = [
    path('diseases/', views.diseases_list, name='diseases-list'),
    path('diseases/<int:pk>/', views.disease_detail, name='disease-detail'),
    path('predict/', views.predict, name='predict'),
    path('diseases/<int:pk>/options/', views.disease_options, name='disease-options'),
    path('contact/', views.contact_view, name='contact'),
    path('chat/', views.chat_view, name='chat'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('me/', views.me_view, name='me'),
]
