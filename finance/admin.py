from django.contrib import admin
from .models import SchoolFee


@admin.register(SchoolFee)
class SchoolFeesAdmin(admin.ModelAdmin):
    list_display = ['student', 'academic_year', 'total_fees', 'amount_paid', 'balance', 'payment_status', 'created_at']
    list_filter = ['payment_status', 'academic_year']
    search_fields = ['student__full_name']
    readonly_fields = ['balance', 'created_at', 'updated_at']

