"""
URL configuration for sims project.
"""
from django.contrib import admin
from django.urls import path, include, register_converter
from core.converters import HashidConverter
from django.views.generic import RedirectView, TemplateView
from django.conf import settings
from django.conf.urls.static import static

register_converter(HashidConverter, 'hashid')

handler404 = 'sims.views.custom_page_not_found'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/dashboard/', permanent=False)),
    path('', include('accounts.urls')),
    path('core/', include('core.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('students/', include(('students.urls', 'students'), namespace='students')),
    path('families/', include('families.urls')),
    path('finance/', include('finance.urls')),
    path('insurance/', include('insurance.urls')),
    path('reports/', include('reports.urls')),
    path('test-404/', TemplateView.as_view(template_name='404.html'), name='test_404'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

