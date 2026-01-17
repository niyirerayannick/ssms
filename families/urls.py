from django.urls import path
from . import views

app_name = 'families'

urlpatterns = [
    path('', views.family_list, name='family_list'),
    path('add/', views.family_create, name='family_create'),
    path('<int:pk>/', views.family_detail, name='family_detail'),
    path('<int:pk>/edit/', views.family_edit, name='family_edit'),
]
