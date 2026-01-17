from django.contrib import admin
from .models import SchoolFees


@admin.register(SchoolFees)
class SchoolFeesAdmin(admin.ModelAdmin):
    list_display = ['student', 'term', 'required_fees', 'amount_paid', 'balance', 'status', 'payment_date']
    list_filter = ['status', 'term']
    search_fields = ['student__full_name']
    readonly_fields = ['balance', 'created_at', 'updated_at']

