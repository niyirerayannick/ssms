from django.urls import path
from . import views

app_name = 'finance'

urlpatterns = [
    path('dashboard/', views.finance_dashboard, name='dashboard'),
    path('', views.fees_list, name='fees_list'),
    path('add/', views.fee_create, name='fee_create'),
    path('<int:pk>/edit/', views.fee_edit, name='fee_edit'),
    path('overdue/', views.overdue_fees, name='overdue_fees'),
    path('student/<int:student_id>/payments/', views.student_payment_history, name='student_payments'),
    path('student/<int:student_id>/add/', views.add_student_payment, name='add_student_payment'),
    path('api/student/<int:student_id>/details/', views.get_student_details, name='api_student_details'),
    path('api/family/<int:family_id>/insurance/', views.get_family_insurance_details, name='api_family_insurance'),
    path('api/district/<int:district_id>/families/', views.get_families_by_district, name='api_families_by_district'),
    path('api/district/<int:district_id>/students/', views.get_students_by_district, name='api_students_by_district'),
]

