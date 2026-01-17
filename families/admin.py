from django.contrib import admin
from .models import Family, FamilyStudent


@admin.register(Family)
class FamilyAdmin(admin.ModelAdmin):
    list_display = ['head_of_family', 'phone_number', 'district', 'created_at']
    search_fields = ['head_of_family', 'phone_number', 'district__name']
    list_filter = ['district', 'created_at']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(FamilyStudent)
class FamilyStudentAdmin(admin.ModelAdmin):
    list_display = ['family', 'student', 'relationship', 'created_at']
    search_fields = ['family__guardian_name', 'student__full_name']
    list_filter = ['relationship', 'created_at']
