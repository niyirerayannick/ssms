from django.urls import path
from . import views

app_name = 'insurance'

urlpatterns = [
    path('', views.insurance_list, name='insurance_list'),
    path('add/', views.insurance_create, name='insurance_create'),
    path('<hashid:pk>/edit/', views.insurance_edit, name='insurance_edit'),
    path('coverage/', views.coverage_summary, name='coverage_summary'),
]

