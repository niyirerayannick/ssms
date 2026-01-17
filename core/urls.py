from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('api/districts/', views.get_districts, name='get_districts'),
    path('api/sectors/', views.get_sectors, name='get_sectors'),
    path('api/cells/', views.get_cells, name='get_cells'),
    path('api/villages/', views.get_villages, name='get_villages'),
]
