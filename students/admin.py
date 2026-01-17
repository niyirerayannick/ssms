from django.contrib import admin
from .models import Student, StudentPhoto, AcademicRecord


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'gender', 'age', 'school', 'district', 'sponsorship_status', 'program_officer']
    list_filter = ['gender', 'sponsorship_status', 'district', 'school']
    search_fields = ['full_name', 'district__name', 'school__name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(StudentPhoto)
class StudentPhotoAdmin(admin.ModelAdmin):
    list_display = ['student', 'caption', 'created_at']
    search_fields = ['student__full_name', 'caption']
    list_filter = ['created_at']


@admin.register(AcademicRecord)
class AcademicRecordAdmin(admin.ModelAdmin):
    list_display = ['student', 'subject', 'marks', 'term', 'academic_year', 'created_at']
    search_fields = ['student__full_name', 'subject']
    list_filter = ['term', 'academic_year', 'created_at']
