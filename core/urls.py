from django.urls import path
from . import views, api_views

app_name = 'core'

urlpatterns = [
    # Legacy views
    path('api/districts/', views.get_districts, name='get_districts'),
    path('api/sectors/', views.get_sectors, name='get_sectors'),
    path('api/cells/', views.get_cells, name='get_cells'),
    path('api/villages/', views.get_villages, name='get_villages'),
    
    # New JSON API endpoints for Rwanda location hierarchy
    path('api/locations/provinces/', api_views.get_provinces, name='api_provinces'),
    path('api/locations/districts/<int:province_id>/', api_views.get_districts, name='api_districts'),
    path('api/locations/sectors/<int:district_id>/', api_views.get_sectors, name='api_sectors'),
    path('api/locations/cells/<int:sector_id>/', api_views.get_cells, name='api_cells'),
    path('api/locations/villages/<int:cell_id>/', api_views.get_villages, name='api_villages'),
    path('api/locations/tree/', api_views.get_full_location_tree, name='api_location_tree'),
    path('api/locations/search/', api_views.search_locations, name='api_search_locations'),
    
    # School Management
    path('schools/', views.school_list, name='school_list'),
    path('schools/<int:pk>/', views.school_detail, name='school_detail'),
    path('schools/add/', views.school_create, name='school_create'),
    path('schools/<int:pk>/edit/', views.school_edit, name='school_edit'),
]
