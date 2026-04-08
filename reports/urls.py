from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.reports_index, name='index'),
    path('analysis/', views.analysis_dashboard, name='analysis'),
    path('students/pdf/', views.students_pdf, name='students_pdf'),
    path('students/excel/', views.students_excel, name='students_excel'),
    path('students/sponsored/', views.sponsored_students_report, name='sponsored_students_report'),
    path('families/pdf/', views.families_pdf, name='families_pdf'),
    path('families/excel/', views.families_excel, name='families_excel'),
    path('schools/pdf/', views.schools_pdf, name='schools_pdf'),
    path('schools/excel/', views.schools_excel, name='schools_excel'),
    path('fees/pdf/', views.fees_pdf, name='fees_pdf'),
    path('fees/excel/', views.fees_excel, name='fees_excel'),
    path('financial/pdf/', views.financial_report_pdf, name='financial_report_pdf'),
    path('insurance/pdf/', views.insurance_pdf, name='insurance_pdf'),
    path('insurance/supported-families/pdf/', views.supported_mutuelle_families_pdf, name='supported_mutuelle_families_pdf'),
]

