from django.contrib import admin
from .models import SchoolFee, SchoolFeePayment, SchoolFeeDisbursement


@admin.register(SchoolFee)
class SchoolFeesAdmin(admin.ModelAdmin):
    list_display = ['student', 'academic_year', 'total_fees', 'amount_paid', 'balance', 'payment_status', 'created_at']
    list_filter = ['payment_status', 'academic_year']
    search_fields = ['student__first_name', 'student__last_name']
    readonly_fields = ['balance', 'created_at', 'updated_at']


@admin.register(SchoolFeePayment)
class SchoolFeePaymentAdmin(admin.ModelAdmin):
    list_display = ['school_fee', 'amount_paid', 'payment_date', 'payment_method', 'reference_number', 'recorded_by']
    list_filter = ['payment_method', 'payment_date']
    search_fields = ['school_fee__student__first_name', 'school_fee__student__last_name', 'reference_number']


@admin.register(SchoolFeeDisbursement)
class SchoolFeeDisbursementAdmin(admin.ModelAdmin):
    list_display = ['student_name', 'school_name', 'amount_to_pay', 'status', 'requested_at', 'paid_at']
    list_filter = ['status', 'school_fee__academic_year']
    search_fields = ['student_name', 'school_name', 'bank_account_name', 'bank_account_number', 'payment_reference']

