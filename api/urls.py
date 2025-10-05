# lakbayan/urls.py
from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    # Accounts
    path('accounts/register/', views.RegisterView.as_view(), name='register'),
    path('accounts/login/', views.LoginView.as_view(), name='login'),
    path('accounts/logout/', views.LogoutView.as_view(), name='logout'),
    path('accounts/profile/', views.ProfileView.as_view(), name='profile'),
    path('accounts/delete/', views.DeleteAccountView.as_view(), name='delete-account'),
    
    # Data Export
    path('complete/', views.complete_data_export, name='complete-data-export'),
    path('metadata/', views.data_export_metadata, name='data-export-metadata'),
    
    # Terminals
    path('terminals/city/<int:city_id>/', views.TerminalsByCityView.as_view(), name='terminals-by-city'),
    path('terminals/region/<int:region_id>/', views.TerminalsByRegionView.as_view(), name='terminals-by-region'),
    path('terminals/nearby/', views.nearby_terminals, name='nearby-terminals'),
]