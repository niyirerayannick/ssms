from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.db.models import Q, Avg
from django.contrib.auth import get_user_model
from .models import Student, StudentPhoto, StudentMark
from core.models import Notification
from .forms import StudentForm, StudentPhotoForm, StudentMarkForm
from families.models import FamilyStudent


@login_required
@permission_required('students.view_student', raise_exception=True)
def student_list(request):
    """List all students with search and filters."""
    students = Student.objects.all()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        students = students.filter(
            Q(full_name__icontains=search_query) |
            Q(family__district__name__icontains=search_query) |
            Q(school__name__icontains=search_query)
        )
    
    # Filter by sponsorship status
    status_filter = request.GET.get('status', '')
    if status_filter:
        students = students.filter(sponsorship_status=status_filter)
    
    # Filter by gender
    gender_filter = request.GET.get('gender', '')
    if gender_filter:
        students = students.filter(gender=gender_filter)
    
    context = {
        'students': students,
        'search_query': search_query,
        'status_filter': status_filter,
        'gender_filter': gender_filter,
    }
    return render(request, 'students/student_list.html', context)


def _notify_admins_and_exec(actor, verb, link):
    User = get_user_model()
    recipient_ids = set(
        User.objects.filter(
            Q(groups__name__in=['Admin', 'Executive Secretary']) |
            Q(is_superuser=True) |
            Q(is_staff=True)
        ).values_list('id', flat=True)
    )
    if actor:
        recipient_ids.add(actor.id)
    recipients = User.objects.filter(id__in=recipient_ids)
    notifications = [
        Notification(recipient=user, actor=actor, verb=verb, link=link)
        for user in recipients
    ]
    if notifications:
        Notification.objects.bulk_create(notifications)


@login_required
@permission_required('students.add_student', raise_exception=True)
def student_create(request):
    """Create a new student."""
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES)
        if form.is_valid():
            student = form.save()
            _notify_admins_and_exec(
                actor=request.user,
                verb=f"Added student {student.full_name}",
                link=reverse('students:student_detail', kwargs={'pk': student.pk})
            )
            messages.success(request, f'Student {student.full_name} created successfully!')
            return redirect('students:student_detail', pk=student.pk)
    else:
        form = StudentForm()
    
    return render(request, 'students/student_form.html', {'form': form, 'title': 'Add Student'})


@login_required
@permission_required('students.change_student', raise_exception=True)
def student_edit(request, pk):
    """Edit an existing student."""
    student = get_object_or_404(Student, pk=pk)
    
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            student = form.save()
            _notify_admins_and_exec(
                actor=request.user,
                verb=f"Updated student {student.full_name}",
                link=reverse('students:student_detail', kwargs={'pk': student.pk})
            )
            messages.success(request, f'Student {student.full_name} updated successfully!')
            return redirect('students:student_detail', pk=student.pk)
    else:
        form = StudentForm(instance=student)
    
    return render(request, 'students/student_form.html', {'form': form, 'student': student, 'title': 'Edit Student'})


@login_required
@permission_required('students.view_student', raise_exception=True)
def student_detail(request, pk):
    """View student profile with family, fees, and insurance information."""
    student = get_object_or_404(Student, pk=pk)
    
    # Get related data
    family_member = getattr(student, 'family_member', None)
    family = student.family or (family_member.family if family_member else None)
    fees = student.fees.all()
    insurance_records = family.insurance_records.all() if family else []
    
    context = {
        'student': student,
        'family': family,
        'family_member': family_member,
        'fees': fees,
        'insurance_records': insurance_records,
    }
    return render(request, 'students/student_detail.html', context)


@login_required
@permission_required('students.view_student', raise_exception=True)
def photo_gallery(request):
    """View all student photos in a gallery."""
    photos = (
        StudentPhoto.objects.select_related('student')
        .order_by('-created_at')
    )
    return render(request, 'students/photo_gallery.html', {'photos': photos})


@login_required
def add_photo(request, pk):
    """Add photo to student."""
    student = get_object_or_404(Student, pk=pk)
    
    if request.method == 'POST':
        form = StudentPhotoForm(request.POST, request.FILES)
        if form.is_valid():
            photo = form.save(commit=False)
            photo.student = student
            photo.save()
            messages.success(request, 'Photo added successfully!')
            return redirect('students:student_detail', pk=student.pk)
    else:
        form = StudentPhotoForm()
    
    return render(request, 'students/add_photo.html', {'form': form, 'student': student})


@login_required
def add_academic_record(request, pk):
    """Add academic record to student."""
    student = get_object_or_404(Student, pk=pk)
    
    if request.method == 'POST':
        form = StudentMarkForm(request.POST, request.FILES)
        if form.is_valid():
            record = form.save(commit=False)
            record.student = student
            record.save()
            messages.success(request, 'Academic record added successfully!')
            return redirect('students:student_detail', pk=student.pk)
    else:
        form = StudentMarkForm()
    
    return render(request, 'students/add_academic_record.html', {'form': form, 'student': student})


@login_required
@permission_required('students.view_studentmark', raise_exception=True)
def student_performance(request):
    """View student performance with filters and charts."""
    academic_year = request.GET.get('academic_year', '')
    term = request.GET.get('term', '')
    class_level = request.GET.get('class_level', '')

    marks_qs = StudentMark.objects.select_related('student')
    if academic_year:
        marks_qs = marks_qs.filter(academic_year=academic_year)
    if term:
        marks_qs = marks_qs.filter(term=term)
    if class_level:
        marks_qs = marks_qs.filter(student__class_level=class_level)

    performance_rows = list(
        marks_qs.values(
            'student_id',
            'student__first_name',
            'student__last_name',
            'student__class_level',
            'academic_year',
            'term'
        ).annotate(avg_marks=Avg('marks')).order_by('student__first_name', 'student__last_name')
    )

    total_records = len(performance_rows)
    passed = sum(1 for row in performance_rows if (row.get('avg_marks') or 0) >= 50)
    failed = total_records - passed
    pass_rate = round((passed / total_records) * 100, 1) if total_records else 0

    available_years = (
        StudentMark.objects.values_list('academic_year', flat=True)
        .distinct().order_by('-academic_year')
    )
    available_classes = (
        StudentMark.objects.values_list('student__class_level', flat=True)
        .exclude(student__class_level__isnull=True)
        .exclude(student__class_level__exact='')
        .distinct().order_by('student__class_level')
    )
    term_choices = [choice[0] for choice in StudentMark.TERM_CHOICES]

    trend_qs = StudentMark.objects.all()
    if academic_year:
        trend_qs = trend_qs.filter(academic_year=academic_year)
    if class_level:
        trend_qs = trend_qs.filter(student__class_level=class_level)
    trend_data = {
        item['term']: float(item['avg_marks'] or 0)
        for item in trend_qs.values('term').annotate(avg_marks=Avg('marks'))
    }
    trend_labels = term_choices
    trend_values = [round(trend_data.get(label, 0), 1) for label in trend_labels]

    context = {
        'performance_rows': performance_rows,
        'total_records': total_records,
        'passed': passed,
        'failed': failed,
        'pass_rate': pass_rate,
        'available_years': available_years,
        'available_terms': term_choices,
        'available_classes': available_classes,
        'selected_year': academic_year,
        'selected_term': term,
        'selected_class': class_level,
        'trend_labels': trend_labels,
        'trend_values': trend_values,
    }
    return render(request, 'students/student_performance.html', context)
