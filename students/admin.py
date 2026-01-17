from django.contrib import admin
from .models import Student, StudentPhoto, StudentMark


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'gender', 'age', 'school', 'enrollment_status', 'program_officer']
    list_filter = ['gender', 'enrollment_status', 'school']
    search_fields = ['first_name', 'last_name', 'school__name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(StudentPhoto)
class StudentPhotoAdmin(admin.ModelAdmin):
    list_display = ['student', 'caption', 'created_at']
    search_fields = ['student__full_name', 'caption']
    list_filter = ['created_at']


@admin.register(StudentMark)
class AcademicRecordAdmin(admin.ModelAdmin):
    list_display = ['student', 'subject', 'marks', 'term', 'academic_year', 'created_at']
    search_fields = ['student__full_name', 'subject']
    list_filter = ['term', 'academic_year', 'created_at']
