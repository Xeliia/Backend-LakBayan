from django.urls import path, include

urlpatterns = [
    path('accounts/', include('api.urls.accounts')),
    path('terminals/', include('api.urls.terminals')), 
    path('routes/', include('api.urls.routes')),
]