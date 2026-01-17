from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    path('', views.student_list, name='student_list'),
    path('add/', views.student_create, name='student_create'),
    path('<int:pk>/', views.student_detail, name='student_detail'),
    path('<int:pk>/edit/', views.student_edit, name='student_edit'),
    path('<int:pk>/add-photo/', views.add_photo, name='add_photo'),
    path('<int:pk>/add-academic-record/', views.add_academic_record, name='add_academic_record'),
]
