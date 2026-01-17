from django.contrib import admin
from .models import FamilyInsurance, HealthInsurance


@admin.register(FamilyInsurance)
class FamilyInsuranceAdmin(admin.ModelAdmin):
    list_display = ['family', 'insurance_year', 'required_amount', 'amount_paid', 'balance', 'coverage_status', 'created_at']
    list_filter = ['coverage_status', 'insurance_year']
    search_fields = ['family__head_of_family']
    readonly_fields = ['balance', 'created_at', 'updated_at']


@admin.register(HealthInsurance)
class HealthInsuranceAdmin(admin.ModelAdmin):
    list_display = ['student', 'required_amount', 'amount_paid', 'coverage_status', 'created_at']
    list_filter = ['coverage_status']
    search_fields = ['student__full_name']
    readonly_fields = ['created_at', 'updated_at']
    verbose_name = "Legacy Health Insurance"
    verbose_name_plural = "Legacy Health Insurance Records"
