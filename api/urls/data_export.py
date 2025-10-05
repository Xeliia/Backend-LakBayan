from django.urls import path
from ..views.data_export import (
    complete_data_export,
    data_export_metadata
)

urlpatterns = [
    path('complete/', complete_data_export, name='complete-data-export'),
    path('metadata/', data_export_metadata, name='data-export-metadata'),
]