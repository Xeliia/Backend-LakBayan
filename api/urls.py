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
    path('metadata/', views.metadata, name='metadata'),
    path('export/regions-cities/', views.export_regions_cities, name='export-regions-cities'),
    path('export/terminals/', views.export_terminals, name='export-terminals'),
    path('export/routes-stops/', views.export_routes_stops, name='export-routes-stops'),
    
    # Terminals
    path('terminals/city/<int:city_id>/', views.TerminalsByCityView.as_view(), name='terminals-by-city'),
    path('terminals/region/<int:region_id>/', views.TerminalsByRegionView.as_view(), name='terminals-by-region'),
    path('terminals/nearby/', views.nearby_terminals, name='nearby-terminals'),

    # User Contributions
    path('contribute/terminal/', views.contribute_terminal, name='contribute-terminal'),
    path('contribute/route/', views.contribute_route, name='contribute-route'),
    path('contribute/stop/', views.contribute_route_stop, name='contribute-stop'),
    path('contribute/complete-route/', views.contribute_complete_route, name='contribute-complete-route'),
    path('contribute/contribute-all/', views.contribute_all, name='contribute-all'),
    path('my-contributions/', views.my_contributions, name='my-contributions'),
    
    # Helper
    path('cities/region/<int:region_id>/', views.get_cities_by_region, name='cities-by-region'),
    path('transport-modes/', views.get_transport_modes, name='transport-modes'),

    #Email Verificaiton
    path('email-verification/status/', views.check_email_verification_status, name='email-verification-status'),
    path('email-verification/resend/', views.resend_verification_email, name='resend-verification'),

    # Password management
    path('accounts/forgot-password/', views.forgot_password, name='forgot-password'),
    path('accounts/reset-password/', views.reset_password, name='reset-password'),
    path('accounts/change-password/', views.change_password, name='change-password'),

    path('cached/complete/', views.cached_complete_export, name='cached-complete'),
    path('cached/terminals/', views.cached_terminals_export, name='cached-terminals'),
    path('cached/routes/', views.cached_routes_export, name='cached-routes'),
    path('cached/regions/', views.cached_regions_export, name='cached-regions'),
    path('cached/metadata/', views.cached_metadata, name='cached-metadata'),
]