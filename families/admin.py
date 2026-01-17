from django.contrib import admin
from .models import Family, FamilyStudent


@admin.register(Family)
class FamilyAdmin(admin.ModelAdmin):
    list_display = ['guardian_name', 'guardian_phone', 'family_size', 'district', 'created_at']
    search_fields = ['guardian_name', 'guardian_phone', 'district__name']
    list_filter = ['district', 'created_at']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(FamilyStudent)
class FamilyStudentAdmin(admin.ModelAdmin):
    list_display = ['family', 'student', 'relationship', 'created_at']
    search_fields = ['family__guardian_name', 'student__full_name']
    list_filter = ['relationship', 'created_at']
