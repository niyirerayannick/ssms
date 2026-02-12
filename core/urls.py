from django.urls import path
from . import views, api_views, import_export

app_name = 'core'

urlpatterns = [
    # Legacy views
    path('api/districts/', views.get_districts, name='get_districts'),
    path('api/sectors/', views.get_sectors, name='get_sectors'),
    path('api/cells/', views.get_cells, name='get_cells'),
    path('api/villages/', views.get_villages, name='get_villages'),
    
    # New JSON API endpoints for Rwanda location hierarchy
    path('api/locations/provinces/', api_views.get_provinces, name='api_provinces'),
    path('api/locations/districts/<hashid:province_id>/', api_views.get_districts, name='api_districts'),
    path('api/locations/sectors/<hashid:district_id>/', api_views.get_sectors, name='api_sectors'),
    path('api/locations/cells/<hashid:sector_id>/', api_views.get_cells, name='api_cells'),
    path('api/locations/villages/<hashid:cell_id>/', api_views.get_villages, name='api_villages'),
    path('api/locations/tree/', api_views.get_full_location_tree, name='api_location_tree'),
    path('api/locations/search/', api_views.search_locations, name='api_search_locations'),
    
    # School Management
    path('schools/', views.school_list, name='school_list'),
    path('schools/add/', views.school_create, name='school_create'),
    path('schools/<hashid:pk>/', views.school_detail, name='school_detail'),
    path('schools/<hashid:pk>/edit/', views.school_edit, name='school_edit'),
    
    # Partner Management
    path('partners/', views.partner_list, name='partner_list'),
    path('partners/add/', views.partner_create, name='partner_create'),
    path('partners/<hashid:pk>/', views.partner_detail, name='partner_detail'),
    path('partners/<hashid:pk>/edit/', views.partner_edit, name='partner_edit'),
    
    # Excel Import/Export
    path('import/students/', import_export.import_students, name='import_students'),
    path('import/families/', import_export.import_families, name='import_families'),
    path('import/schools/', import_export.import_schools, name='import_schools'),
    path('templates/students/', import_export.download_student_template, name='download_student_template'),
    path('templates/families/', import_export.download_family_template, name='download_family_template'),
    path('templates/schools/', import_export.download_school_template, name='download_school_template'),
    path('notifications/mark-all/', views.notifications_mark_all_read, name='notifications_mark_all_read'),
    path('notifications/<hashid:pk>/go/', views.notification_go, name='notification_go'),
]
