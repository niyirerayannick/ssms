from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.reports_index, name='index'),
    path('students/pdf/', views.students_pdf, name='students_pdf'),
    path('students/sponsored/', views.sponsored_students_report, name='sponsored_students_report'),
    path('fees/excel/', views.fees_excel, name='fees_excel'),
    path('insurance/pdf/', views.insurance_pdf, name='insurance_pdf'),
]

