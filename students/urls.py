from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    path('photos/', views.photo_gallery, name='photo_gallery'),
    path('photos/<hashid:pk>/', views.student_photos, name='student_photo_album'),
    path('', views.student_list, name='student_list'),
    path('add/', views.student_create, name='student_create'),
    path('promotion/', views.academic_year_promotion, name='academic_year_promotion'),
    path('performance/', views.StudentPerformanceListView.as_view(), name='student_performance'),
    path('performance/bulk-entry/', views.student_performance_bulk_entry, name='student_performance_bulk_entry'),
    path('performance/<int:pk>/', views.StudentPerformanceDetailView.as_view(), name='student_performance_detail'),
    path('materials/', views.student_materials, name='student_materials'),
    path('materials/bulk-entry/', views.student_material_bulk_entry, name='student_material_bulk_entry'),
    path('materials/add/', views.student_material_create, name='student_material_create'),
    path('materials/<hashid:pk>/edit/', views.student_material_edit, name='student_material_edit'),
    path('<hashid:pk>/full-report/pdf/', views.student_full_report_pdf, name='student_full_report_pdf'),
    path('<hashid:pk>/', views.student_detail, name='student_detail'),
    path('<hashid:pk>/approve/', views.student_approve, name='student_approve'),
    path('<hashid:pk>/edit/', views.student_edit, name='student_edit'),
    path('<hashid:pk>/add-photo/', views.add_photo, name='add_photo'),
    path('<hashid:pk>/photos/', views.student_photos, name='student_photos'),
    path('<hashid:student_pk>/photos/<int:photo_pk>/edit/', views.edit_photo, name='edit_photo'),
    path('<hashid:student_pk>/photos/<int:photo_pk>/delete/', views.delete_photo, name='delete_photo'),
    path('photos/shared/<str:token>/', views.student_photos_public, name='student_photos_public'),
    path('<hashid:pk>/add-academic-record/', views.add_academic_record, name='add_academic_record'),
    path('<hashid:student_pk>/academic-records/<int:record_pk>/edit/', views.edit_academic_record, name='edit_academic_record'),
    path('<hashid:student_pk>/academic-records/<int:record_pk>/delete/', views.delete_academic_record, name='delete_academic_record'),
    path('<hashid:pk>/report-cards/', views.student_report_cards, name='student_report_cards'),
]
