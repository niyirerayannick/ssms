from django.urls import path
from . import views

app_name = 'finance'

urlpatterns = [
    path('', views.fees_list, name='fees_list'),
    path('add/', views.fee_create, name='fee_create'),
    path('<int:pk>/edit/', views.fee_edit, name='fee_edit'),
    path('overdue/', views.overdue_fees, name='overdue_fees'),
]

