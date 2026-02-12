from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    path('photos/', views.photo_gallery, name='photo_gallery'),
    path('', views.student_list, name='student_list'),
    path('add/', views.student_create, name='student_create'),
    path('performance/', views.student_performance, name='student_performance'),
    path('materials/', views.student_materials, name='student_materials'),
    path('materials/add/', views.student_material_create, name='student_material_create'),
    path('materials/<hashid:pk>/edit/', views.student_material_edit, name='student_material_edit'),
    path('<hashid:pk>/', views.student_detail, name='student_detail'),
    path('<hashid:pk>/approve/', views.student_approve, name='student_approve'),
    path('<hashid:pk>/edit/', views.student_edit, name='student_edit'),
    path('<hashid:pk>/add-photo/', views.add_photo, name='add_photo'),
    path('<hashid:pk>/photos/', views.student_photos, name='student_photos'),
    path('photos/shared/<str:token>/', views.student_photos_public, name='student_photos_public'),
    path('<hashid:pk>/add-academic-record/', views.add_academic_record, name='add_academic_record'),
    path('<hashid:pk>/report-cards/', views.student_report_cards, name='student_report_cards'),
]
