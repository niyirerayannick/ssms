from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.db.models import Q, Avg, Count
from core.models import District
from django.utils import timezone
from django.core import signing
from django.http import Http404
from django.views.decorators.http import require_POST
from django.contrib.auth import get_user_model
from .models import Student, StudentPhoto, StudentMark, StudentMaterial
from core.models import Notification, AcademicYear
from .forms import StudentForm, StudentPhotoForm, StudentMarkForm, StudentMaterialForm
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

    # Filter by district (family district)
    district_filter = request.GET.get('district', '')
    if district_filter:
        students = students.filter(family__district_id=district_filter)

    boarding_counts = {item['boarding_status']: item['total'] for item in students.values('boarding_status').annotate(total=Count('id'))}
    level_counts = {item['school_level']: item['total'] for item in students.values('school_level').annotate(total=Count('id'))}
    
    context = {
        'students': students,
        'search_query': search_query,
        'status_filter': status_filter,
        'gender_filter': gender_filter,
        'district_filter': district_filter,
        'districts': District.objects.order_by('name'),
        'boarding_count': boarding_counts.get('boarding', 0),
        'non_boarding_count': boarding_counts.get('non_boarding', 0),
        'nursery_count': level_counts.get('nursery', 0),
        'primary_count': level_counts.get('primary', 0),
        'secondary_count': level_counts.get('secondary', 0),
        'tvet_count': level_counts.get('tvet', 0),
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


def _can_approve_student(user):
    return (
        user.is_superuser or
        user.groups.filter(name__in=['Admin', 'Executive Secretary']).exists()
    )


@login_required
@permission_required('students.add_student', raise_exception=True)
def student_create(request):
    """Create a new student."""
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES)
        if form.is_valid():
            student = form.save(commit=False)
            student.sponsorship_status = 'pending'
            student.save()
            form.save_m2m()
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
@permission_required('students.view_studentmaterial', raise_exception=True)
def student_materials(request):
    """List sponsored students and their school material status."""
    academic_year = request.GET.get('academic_year', str(timezone.now().year))
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')

    students_qs = Student.objects.filter(sponsorship_status='active')
    if search_query:
        students_qs = students_qs.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(family__family_code__icontains=search_query)
        )

    materials_qs = StudentMaterial.objects.filter(academic_year=academic_year).select_related('student')
    materials_by_student = {material.student_id: material for material in materials_qs}

    rows = []
    for student in students_qs.order_by('first_name', 'last_name'):
        material = materials_by_student.get(student.id)
        has_all_required = material.all_required_received if material else False
        if status_filter == 'complete' and not has_all_required:
            continue
        if status_filter == 'missing' and has_all_required:
            continue
        rows.append({
            'student': student,
            'material': material,
            'has_all_required': has_all_required,
        })

    boarding_counts = {item['boarding_status']: item['total'] for item in students_qs.values('boarding_status').annotate(total=Count('id'))}
    level_counts = {item['school_level']: item['total'] for item in students_qs.values('school_level').annotate(total=Count('id'))}

    total_rows = len(rows)
    complete_rows = sum(1 for row in rows if row['has_all_required'])
    missing_rows = total_rows - complete_rows

    available_years = list(
        StudentMaterial.objects.values_list('academic_year', flat=True)
        .distinct().order_by('-academic_year')
    )
    if academic_year and academic_year not in available_years:
        available_years.insert(0, academic_year)

    context = {
        'rows': rows,
        'academic_year': academic_year,
        'status_filter': status_filter,
        'search_query': search_query,
        'available_years': available_years,
        'total_rows': total_rows,
        'complete_rows': complete_rows,
        'missing_rows': missing_rows,
        'boarding_count': boarding_counts.get('boarding', 0),
        'non_boarding_count': boarding_counts.get('non_boarding', 0),
        'nursery_count': level_counts.get('nursery', 0),
        'primary_count': level_counts.get('primary', 0),
        'secondary_count': level_counts.get('secondary', 0),
        'tvet_count': level_counts.get('tvet', 0),
    }
    return render(request, 'students/student_materials.html', context)


@login_required
@permission_required('students.add_studentmaterial', raise_exception=True)
def student_material_create(request):
    """Create a school material record."""
    initial = {}
    student_id = request.GET.get('student')
    if student_id:
        initial['student'] = student_id
    if request.method == 'POST':
        form = StudentMaterialForm(request.POST)
        if form.is_valid():
            record = form.save()
            messages.success(request, f"Materials saved for {record.student.full_name}.")
            return redirect('students:student_materials')
    else:
        form = StudentMaterialForm(initial=initial)
    return render(request, 'students/student_material_form.html', {'form': form, 'title': 'Add School Materials'})


@login_required
@permission_required('students.change_studentmaterial', raise_exception=True)
def student_material_edit(request, pk):
    """Edit a school material record."""
    record = get_object_or_404(StudentMaterial, pk=pk)
    if request.method == 'POST':
        form = StudentMaterialForm(request.POST, instance=record)
        if form.is_valid():
            form.save()
            messages.success(request, f"Materials updated for {record.student.full_name}.")
            return redirect('students:student_materials')
    else:
        form = StudentMaterialForm(instance=record)
    return render(request, 'students/student_material_form.html', {'form': form, 'title': 'Edit School Materials'})


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
        'can_approve_student': _can_approve_student(request.user),
    }
    return render(request, 'students/student_detail.html', context)


@login_required
@require_POST
def student_approve(request, pk):
    """Approve a student (Executive Secretary or Admin)."""
    if not _can_approve_student(request.user):
        raise Http404()
    student = get_object_or_404(Student, pk=pk)
    student.sponsorship_status = 'active'
    student.save(update_fields=['sponsorship_status'])
    _notify_admins_and_exec(
        actor=request.user,
        verb=f"Approved student {student.full_name}",
        link=reverse('students:student_detail', kwargs={'pk': student.pk})
    )
    messages.success(request, f'Student {student.full_name} approved successfully!')
    return redirect('students:student_detail', pk=student.pk)


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
@permission_required('students.view_student', raise_exception=True)
def student_photos(request, pk):
    """View photos for a specific student."""
    student = get_object_or_404(Student, pk=pk)
    photos = student.photos.all().order_by('-created_at')
    token = signing.dumps({'student_id': student.pk}, salt='student-photos')
    share_url = request.build_absolute_uri(
        reverse('students:student_photos_public', kwargs={'token': token})
    )
    return render(request, 'students/student_photos.html', {'student': student, 'photos': photos, 'share_url': share_url})


def student_photos_public(request, token):
    """Public view for student photos via signed link."""
    try:
        data = signing.loads(token, salt='student-photos', max_age=60 * 60 * 24 * 7)
    except signing.SignatureExpired as exc:
        raise Http404('Share link expired.') from exc
    except signing.BadSignature as exc:
        raise Http404('Invalid share link.') from exc

    student_id = data.get('student_id')
    student = get_object_or_404(Student, pk=student_id)
    photos = student.photos.all().order_by('-created_at')
    return render(request, 'students/student_photos_public.html', {'student': student, 'photos': photos})

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
@permission_required('students.view_student', raise_exception=True)
def student_report_cards(request, pk):
    """View report card images for a specific student."""
    student = get_object_or_404(Student, pk=pk)
    records = student.academic_records.exclude(report_card_image='').exclude(report_card_image__isnull=True)
    return render(request, 'students/student_report_cards.html', {'student': student, 'records': records})

@login_required
@permission_required('students.view_studentmark', raise_exception=True)
def student_performance(request):
    """View student performance with filters and charts."""
    academic_year = request.GET.get('academic_year', '')
    term = request.GET.get('term', '')
    class_level = request.GET.get('class_level', '')

    marks_qs = StudentMark.objects.select_related('student')
    if academic_year:
        marks_qs = marks_qs.filter(academic_year_id=academic_year)
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
            'academic_year__name',
            'term'
        ).annotate(avg_marks=Avg('marks')).order_by('student__first_name', 'student__last_name')
    )

    total_records = len(performance_rows)
    passed = sum(1 for row in performance_rows if (row.get('avg_marks') or 0) >= 50)
    failed = total_records - passed
    pass_rate = round((passed / total_records) * 100, 1) if total_records else 0

    available_years = AcademicYear.objects.order_by('-name')
    available_classes = (
        StudentMark.objects.values_list('student__class_level', flat=True)
        .exclude(student__class_level__isnull=True)
        .exclude(student__class_level__exact='')
        .distinct().order_by('student__class_level')
    )
    term_choices = [choice[0] for choice in StudentMark.TERM_CHOICES]

    trend_qs = StudentMark.objects.all()
    if academic_year:
        trend_qs = trend_qs.filter(academic_year_id=academic_year)
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
