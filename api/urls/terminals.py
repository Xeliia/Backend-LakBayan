from django.urls import path
from ..views.terminals import (
    TerminalsByCityView,
    TerminalsByRegionView,
    nearby_terminals,
)

urlpatterns = [
    path('city/<int:city_id>/', TerminalsByCityView.as_view(), name='terminals-by-city'),
    path('region/<int:region_id>/', TerminalsByRegionView.as_view(), name='terminals-by-region'),
    path('nearby/', nearby_terminals, name='nearby-terminals'),
]