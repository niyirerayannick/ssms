from django.contrib import admin
from .models import School, District, Sector, Cell, Village, Notification, AcademicYear, Partner


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_person', 'email', 'phone', 'created_at']
    search_fields = ['name', 'contact_person', 'email']
    list_filter = ['created_at']


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ['name', 'district', 'sector', 'created_at']
    search_fields = ['name', 'district__name']
    list_filter = ['district', 'created_at']


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'created_at']
    search_fields = ['name', 'code']
    ordering = ['name']


@admin.register(Sector)
class SectorAdmin(admin.ModelAdmin):
    list_display = ['name', 'district', 'code', 'created_at']
    search_fields = ['name', 'district__name']
    list_filter = ['district']
    ordering = ['district', 'name']


@admin.register(Cell)
class CellAdmin(admin.ModelAdmin):
    list_display = ['name', 'sector', 'code', 'created_at']
    search_fields = ['name', 'sector__name']
    list_filter = ['sector__district', 'sector']
    ordering = ['sector', 'name']


@admin.register(Village)
class VillageAdmin(admin.ModelAdmin):
    list_display = ['name', 'cell', 'code', 'created_at']
    search_fields = ['name', 'cell__name']
    list_filter = ['cell__sector__district', 'cell__sector', 'cell']
    ordering = ['cell', 'name']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'verb', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['recipient__username', 'verb', 'description']


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name']
