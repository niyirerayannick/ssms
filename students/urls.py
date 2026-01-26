from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    path('', views.student_list, name='student_list'),
    path('add/', views.student_create, name='student_create'),
    path('performance/', views.student_performance, name='student_performance'),
    path('materials/', views.student_materials, name='student_materials'),
    path('materials/add/', views.student_material_create, name='student_material_create'),
    path('materials/<int:pk>/edit/', views.student_material_edit, name='student_material_edit'),
    path('<int:pk>/', views.student_detail, name='student_detail'),
    path('<int:pk>/approve/', views.student_approve, name='student_approve'),
    path('<int:pk>/edit/', views.student_edit, name='student_edit'),
    path('<int:pk>/add-photo/', views.add_photo, name='add_photo'),
    path('<int:pk>/photos/', views.student_photos, name='student_photos'),
    path('photos/shared/<str:token>/', views.student_photos_public, name='student_photos_public'),
    path('photos/', views.photo_gallery, name='photo_gallery'),
    path('<int:pk>/add-academic-record/', views.add_academic_record, name='add_academic_record'),
    path('<int:pk>/report-cards/', views.student_report_cards, name='student_report_cards'),
]
