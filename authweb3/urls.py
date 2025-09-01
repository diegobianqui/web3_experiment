from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('get-nonce/', views.get_nonce, name='get_nonce'),
    path('verify-signature/', views.verify_signature, name='verify_signature'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),
]
