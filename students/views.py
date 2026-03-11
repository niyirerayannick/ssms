from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.db import transaction
from django.db.models import (
    Q,
    Avg,
    Count,
    Sum,
    Case,
    When,
    Value,
    BooleanField,
    Prefetch,
    DecimalField,
)
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.views.generic import ListView, DetailView
from django.db.models.functions import Coalesce
from django.http import Http404, HttpResponse
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from core.models import District, School, Partner
from django.utils import timezone
from django.core import signing
from django.views.decorators.http import require_POST
from django.contrib.auth import get_user_model
from django.forms import formset_factory
from urllib.parse import urlencode
from .models import Student, StudentPhoto, StudentMark, StudentMaterial
from core.models import Notification, AcademicYear
from .forms import (
    StudentForm,
    StudentPhotoForm,
    StudentMarkForm,
    StudentMaterialForm,
    BulkPerformanceFilterForm,
    BulkStudentMarkForm,
)
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
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
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
        students = students.filter(
            Q(family__district_id=district_filter) |
            Q(partner__district_id=district_filter)
        )

    # Filter by partner
    partner_filter = request.GET.get('partner', '')
    if partner_filter:
        students = students.filter(partner_id=partner_filter)

    school_level_filter = request.GET.get('school_level', '')
    if school_level_filter:
        students = students.filter(school_level=school_level_filter)

    boarding_counts = {item['boarding_status']: item['total'] for item in students.values('boarding_status').annotate(total=Count('id'))}
    level_counts = {item['school_level']: item['total'] for item in students.values('school_level').annotate(total=Count('id'))}
    
    # Pagination
    paginator = Paginator(students.order_by('first_name', 'last_name'), 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'students': page_obj,
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'gender_filter': gender_filter,
        'district_filter': district_filter,
        'partner_filter': partner_filter,
        'school_level_filter': school_level_filter,
        'school_level_choices': Student.SCHOOL_LEVEL_CHOICES,
        'districts': District.objects.order_by('name'),
        'partners': Partner.objects.order_by('name'),
        'boarding_count': boarding_counts.get('boarding', 0),
        'non_boarding_count': boarding_counts.get('non_boarding', 0),
        'nursery_count': level_counts.get('nursery', 0),
        'primary_count': level_counts.get('primary', 0),
        'secondary_count': level_counts.get('secondary', 0),
        'tvet_count': level_counts.get('tvet', 0),
        'university_count': level_counts.get('university', 0),
    }
    return render(request, 'students/student_list.html', context)


def _notify_admins_and_exec(request, actor, verb, link, send_email=False):
    User = get_user_model()
    # Users who should receive notifications and emails (Admins, Execs, Superusers)
    admin_exec_users = User.objects.filter(
        Q(groups__name__in=['Admin', 'Executive Secretary']) |
        Q(is_superuser=True)
    ).distinct()

    # Set of IDs for notification creation
    recipient_ids = set(admin_exec_users.values_list('id', flat=True))
    
    # Also include staff in notifications (but maybe not email if not admin/exec)
    staff_ids = User.objects.filter(is_staff=True).values_list('id', flat=True)
    recipient_ids.update(staff_ids)

    if actor:
        recipient_ids.add(actor.id)
    
    recipients = User.objects.filter(id__in=recipient_ids)
    
    # Create DB Notifications
    notifications = [
        Notification(recipient=user, actor=actor, verb=verb, link=link)
        for user in recipients
    ]
    if notifications:
        Notification.objects.bulk_create(notifications)

    # Send Email if requested (Only to Admins and Executive Secretaries)
    if send_email:
        email_recipients = admin_exec_users.exclude(email='').values_list('email', flat=True)
        
        if email_recipients:
            subject = f"SIMS Notification: {verb}"
            full_link = request.build_absolute_uri(link)
            actor_name = actor.get_full_name() or actor.username
            
            # Prepare HTML content
            context = {
                'verb': verb,
                'actor_name': actor_name,
                'full_link': full_link,
            }
            html_message = render_to_string('emails/notification.html', context)
            plain_message = strip_tags(html_message)
            
            try:
                send_mail(
                    subject=subject,
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=list(email_recipients),
                    html_message=html_message,
                    fail_silently=True
                )
            except Exception as e:
                print(f"Failed to send email: {e}")


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
                request=request,
                actor=request.user,
                verb=f"Added student {student.full_name}",
                link=reverse('students:student_detail', kwargs={'pk': student.pk}),
                send_email=True
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
                request=request,
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
    academic_year_param = request.GET.get('academic_year', '').strip()
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')

    active_year = AcademicYear.objects.filter(is_active=True).first()
    academic_year_id = None
    if academic_year_param:
        try:
            academic_year_id = int(academic_year_param)
        except (TypeError, ValueError):
            academic_year_id = None
    if academic_year_id is None and active_year:
        academic_year_id = active_year.id
    if academic_year_id is None:
        academic_year_id = AcademicYear.objects.order_by('-name').values_list('id', flat=True).first()

    selected_academic_year = (
        AcademicYear.objects.filter(id=academic_year_id).first()
        if academic_year_id else None
    )

    students_qs = Student.objects.filter(sponsorship_status='active')
    if search_query:
        students_qs = students_qs.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(family__family_code__icontains=search_query)
        )

    materials_qs = StudentMaterial.objects.select_related('student')
    if academic_year_id:
        materials_qs = materials_qs.filter(academic_year_id=academic_year_id)
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

    available_years = AcademicYear.objects.order_by('-name')

    context = {
        'rows': rows,
        'selected_academic_year_id': academic_year_id,
        'selected_academic_year': selected_academic_year,
        'status_filter': status_filter,
        'search_query': search_query,
        'available_years': available_years,
        'academic_year_label': selected_academic_year.name if selected_academic_year else 'All Years',
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
        try:
            initial['student'] = int(student_id)
        except (TypeError, ValueError):
            initial['student'] = student_id
    academic_year_param = request.GET.get('academic_year')
    if academic_year_param:
        try:
            initial['academic_year'] = int(academic_year_param)
        except (TypeError, ValueError):
            pass
    if request.method == 'POST':
        form = StudentMaterialForm(request.POST)
        if form.is_valid():
            record = form.save()
            messages.success(request, f"Materials saved for {record.student.full_name}.")
            redirect_url = reverse('students:student_materials')
            if record.academic_year_id:
                redirect_url = f"{redirect_url}?academic_year={record.academic_year_id}"
            return redirect(redirect_url)
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
            redirect_url = reverse('students:student_materials')
            if record.academic_year_id:
                redirect_url = f"{redirect_url}?academic_year={record.academic_year_id}"
            return redirect(redirect_url)
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
        request=request,
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
    district_filter = request.GET.get('district')
    school_filter = request.GET.get('school')
    level_filter = request.GET.get('level')

    photos = StudentPhoto.objects.select_related('student', 'student__family__district', 'student__school').all()

    if district_filter:
        photos = photos.filter(student__family__district_id=district_filter)
    if school_filter:
        photos = photos.filter(student__school_id=school_filter)
    if level_filter:
        photos = photos.filter(student__school_level=level_filter)

    photos = photos.order_by('-created_at')

    context = {
        'photos': photos,
        'districts': District.objects.order_by('name'),
        'schools': School.objects.order_by('name'),
        'levels': Student.SCHOOL_LEVELS,
        'selected_district': int(district_filter) if district_filter else None,
        'selected_school': int(school_filter) if school_filter else None,
        'selected_level': level_filter,
    }
    return render(request, 'students/photo_gallery.html', context)


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
@permission_required('students.add_studentmark', raise_exception=True)
def student_performance_bulk_entry(request):
    """Bulk capture student marks filtered by school, year, and term."""

    data_source = request.POST if request.method == 'POST' else request.GET
    filter_form = BulkPerformanceFilterForm(data_source or None)
    StudentBulkFormSet = formset_factory(BulkStudentMarkForm, extra=0)

    formset = None
    students_loaded = False
    table_rows = []
    selected_filters = {}
    selected_school = None
    selected_year = None
    term_display = None
    subject_label = None
    category_label = None
    class_label = None
    summary = {
        'student_count': 0,
        'records_existing': 0,
        'pending_records': 0,
        'average_marks': 0,
    }

    if filter_form.is_valid():
        students_loaded = True
        academic_year = filter_form.cleaned_data['academic_year']
        school = filter_form.cleaned_data.get('school')
        partner = filter_form.cleaned_data.get('partner')
        term = filter_form.cleaned_data['term']
        term_slug = term.lower().replace(' ', '')
        subject_value = f"{academic_year.name}-{term_slug}-marks"
        category = filter_form.cleaned_data['category']
        class_level = filter_form.cleaned_data.get('class_level', '').strip()

        selected_school = school
        selected_partner = partner
        selected_year = academic_year
        term_display = term
        subject_label = subject_value
        class_label = class_level or None
        category_label = dict(filter_form.fields['category'].choices).get(category, category)

        # If a partner is selected, load students associated with that partner.
        if partner:
            student_qs = (
                Student.objects.filter(is_active=True, partner=partner)
                .select_related('school', 'partner')
                .order_by('first_name', 'last_name')
            )
        else:
            student_qs = (
                Student.objects.filter(is_active=True, school=school)
                .select_related('school', 'partner')
                .order_by('first_name', 'last_name')
            )
        if category == 'primary':
            student_qs = student_qs.filter(school_level='primary')
        elif category == 'secondary':
            student_qs = student_qs.filter(school_level='secondary')
        if class_level:
            student_qs = student_qs.filter(class_level__iexact=class_level)

        students = list(student_qs)
        student_lookup = {student.id: student for student in students}

        existing_marks_qs = StudentMark.objects.filter(
            student__in=students,
            academic_year=academic_year,
            term=term,
        )
        existing_map = {}
        for mark in existing_marks_qs:
            current = existing_map.get(mark.student_id)
            if not current:
                existing_map[mark.student_id] = mark
                continue
            if current.subject != subject_value and mark.subject == subject_value:
                existing_map[mark.student_id] = mark
        existing_values = [float(mark.marks) for mark in existing_map.values() if mark.marks is not None]
        existing_count = len(existing_map)
        summary = {
            'student_count': len(students),
            'records_existing': existing_count,
            'pending_records': max(len(students) - existing_count, 0),
            'average_marks': round(sum(existing_values) / len(existing_values), 1) if existing_values else 0,
        }

        initial_data = []
        for student in students:
            mark = existing_map.get(student.id)
            initial_data.append({
                'student_id': student.id,
                'marks': mark.marks if mark else None,
                'teacher_remark': mark.teacher_remark if mark else '',
            })

        if request.method == 'POST':
            formset = StudentBulkFormSet(request.POST)
            if formset.is_valid():
                created_count = 0
                updated_count = 0
                with transaction.atomic():
                    for form in formset:
                        student_id = form.cleaned_data.get('student_id')
                        marks = form.cleaned_data.get('marks')
                        remark = form.cleaned_data.get('teacher_remark', '')

                        if not student_id or student_id not in student_lookup:
                            continue
                        if marks in (None, ''):
                            continue

                        existing_mark = existing_map.get(student_id)
                        if existing_mark:
                            existing_mark.subject = subject_value
                            existing_mark.marks = marks
                            existing_mark.teacher_remark = remark or ''
                            existing_mark.academic_year = academic_year
                            existing_mark.term = term
                            existing_mark.save(update_fields=['subject', 'marks', 'teacher_remark', 'academic_year', 'term', 'updated_at'])
                            updated_count += 1
                        else:
                            StudentMark.objects.create(
                                student=student_lookup[student_id],
                                academic_year=academic_year,
                                term=term,
                                subject=subject_value,
                                marks=marks,
                                teacher_remark=remark or '',
                            )
                            created_count += 1

                messages.success(
                    request,
                    f"Bulk marks saved{f' for {partner.name}' if partner else f' for {school.name}'}: {created_count} new, {updated_count} updated."
                )
                params = {
                    'academic_year': academic_year.id,
                    'term': term,
                    'category': category,
                }
                if partner:
                    params['partner'] = partner.id
                else:
                    if school:
                        params['school'] = school.id
                if class_level:
                    params['class_level'] = class_level
                query = urlencode(params)
                return redirect(f"{reverse('students:student_performance_bulk_entry')}?{query}")
        else:
            formset = StudentBulkFormSet(initial=initial_data)

        if formset is not None:
            for idx, student in enumerate(students):
                if idx >= len(formset.forms):
                    break
                table_rows.append({
                    'student': student,
                    'form': formset.forms[idx],
                    'existing_mark': existing_map.get(student.id),
                })

        selected_filters = {
            'academic_year': academic_year.id,
            'term': term,
            'category': category,
        }
        if partner:
            selected_filters['partner'] = partner.id
        else:
            if school:
                selected_filters['school'] = school.id
        if class_level:
            selected_filters['class_level'] = class_level

    context = {
        'filter_form': filter_form,
        'formset': formset,
        'table_rows': table_rows,
        'students_loaded': students_loaded,
        'selected_filters': selected_filters,
        'selected_school': selected_school,
        'selected_partner': selected_partner if 'selected_partner' in locals() else None,
        'selected_year': selected_year,
        'term_display': term_display,
        'subject_label': subject_label,
        'category_label': category_label,
        'class_label': class_label,
        'summary': summary,
    }
    return render(request, 'students/student_performance_bulk_entry.html', context)

class StudentPerformanceListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Paginated student performance dashboard."""

    template_name = 'students/student_performance.html'
    context_object_name = 'performance_rows'
    paginate_by = 10
    permission_required = 'students.view_studentmark'
    raise_exception = True

    def get(self, request, *args, **kwargs):
        export_format = request.GET.get('export')
        if export_format in {'pdf', 'excel'}:
            self.object_list = self.get_queryset()
            return self.export_data(export_format)
        return super().get(request, *args, **kwargs)

    def get_filters(self):
        status = self.request.GET.get('status', 'all').lower()
        if status not in {'passed', 'failed'}:
            status = 'all'
        return {
            'academic_year': self.request.GET.get('academic_year', '').strip(),
            'term': self.request.GET.get('term', '').strip(),
            'class_level': self.request.GET.get('class_level', '').strip(),
            'search': self.request.GET.get('search', '').strip(),
            'status': status,
        }

    def get_queryset(self):
        if hasattr(self, '_performance_qs'):
            return self._performance_qs

        filters = self.get_filters()
        queryset = Student.objects.select_related('school').filter(academic_records__isnull=False)
        mark_filter = Q()

        if filters['class_level']:
            queryset = queryset.filter(class_level=filters['class_level'])

        if filters['search']:
            for term in filters['search'].split():
                queryset = queryset.filter(
                    Q(first_name__icontains=term) | Q(last_name__icontains=term)
                )

        if filters['academic_year']:
            queryset = queryset.filter(academic_records__academic_year_id=filters['academic_year'])
            mark_filter &= Q(academic_records__academic_year_id=filters['academic_year'])

        if filters['term']:
            queryset = queryset.filter(academic_records__term=filters['term'])
            mark_filter &= Q(academic_records__term=filters['term'])

        mark_filter = mark_filter if mark_filter.children else Q()

        queryset = queryset.annotate(
            avg_marks=Avg('academic_records__marks', filter=mark_filter),
            total_marks=Coalesce(
                Sum('academic_records__marks', filter=mark_filter),
                Value(0, output_field=DecimalField(max_digits=10, decimal_places=2))
            ),
            records_count=Count('academic_records', filter=mark_filter, distinct=True),
        )

        queryset = queryset.annotate(
            has_passed=Case(
                When(avg_marks__gte=Value(50), then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            )
        )

        if filters['status'] == 'passed':
            queryset = queryset.filter(has_passed=True)
        elif filters['status'] == 'failed':
            queryset = queryset.filter(has_passed=False)

        queryset = queryset.order_by('first_name', 'last_name').distinct()

        self._performance_qs = queryset
        return queryset

    def get_summary_stats(self):
        if hasattr(self, '_summary_stats'):
            return self._summary_stats

        queryset = self.get_queryset()
        total_students = queryset.count()
        passed = queryset.filter(has_passed=True).count()
        failed = max(total_students - passed, 0)
        pass_rate = round((passed / total_students) * 100, 1) if total_students else 0

        self._summary_stats = {
            'total_students': total_students,
            'passed': passed,
            'failed': failed,
            'pass_rate': pass_rate,
        }
        return self._summary_stats

    def get_trend_data(self):
        filters = self.get_filters()
        trend_qs = StudentMark.objects.all()
        if filters['academic_year']:
            trend_qs = trend_qs.filter(academic_year_id=filters['academic_year'])
        if filters['class_level']:
            trend_qs = trend_qs.filter(student__class_level=filters['class_level'])
        if filters['search']:
            for term in filters['search'].split():
                trend_qs = trend_qs.filter(
                    Q(student__first_name__icontains=term) | Q(student__last_name__icontains=term)
                )

        trend_map = {
            row['term']: round(float(row['avg_marks'] or 0), 1)
            for row in trend_qs.values('term').annotate(avg_marks=Avg('marks'))
        }
        labels = [choice[0] for choice in StudentMark.TERM_CHOICES]
        values = [trend_map.get(label, 0) for label in labels]
        return labels, values

    def build_url(self, **overrides):
        params = self.request.GET.copy()
        params.pop('page', None)
        params.pop('export', None)
        for key, value in overrides.items():
            if key == 'status' and value == 'all':
                params.pop('status', None)
                continue
            if value in (None, ''):
                params.pop(key, None)
            else:
                params[key] = value
        query = params.urlencode()
        return f"{self.request.path}?{query}" if query else self.request.path

    def get_preserved_querystring(self):
        params = self.request.GET.copy()
        params.pop('page', None)
        params.pop('export', None)
        return params.urlencode()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        filters = self.get_filters()
        summary = self.get_summary_stats()
        trend_labels, trend_values = self.get_trend_data()

        available_classes = (
            StudentMark.objects.values_list('student__class_level', flat=True)
            .exclude(student__class_level__isnull=True)
            .exclude(student__class_level__exact='')
            .distinct()
            .order_by('student__class_level')
        )

        status_options = [
            {'label': 'All Students', 'value': 'all'},
            {'label': 'Passed Students', 'value': 'passed'},
            {'label': 'Failed Students', 'value': 'failed'},
        ]
        for option in status_options:
            option['url'] = self.build_url(status=option['value'])
            option['active'] = option['value'] == filters['status']

        filters_applied = any(
            value for key, value in filters.items() if key != 'status'
        ) or filters['status'] in {'passed', 'failed'}

        context.update({
            'available_years': AcademicYear.objects.order_by('-name'),
            'available_terms': [choice[0] for choice in StudentMark.TERM_CHOICES],
            'available_classes': available_classes,
            'selected_year': filters['academic_year'],
            'selected_term': filters['term'],
            'selected_class': filters['class_level'],
            'search_query': filters['search'],
            'status_filter': filters['status'],
            'status_filter_options': status_options,
            'trend_labels': trend_labels,
            'trend_values': trend_values,
            'querystring': self.get_preserved_querystring(),
            'filters_applied': filters_applied,
            'export_pdf_url': self.build_url(export='pdf'),
            'export_excel_url': self.build_url(export='excel'),
        })
        context.update(summary)
        return context

    def get_export_rows(self):
        rows = []
        for student in self.get_queryset():
            avg = student.avg_marks or 0
            rows.append({
                'name': student.full_name,
                'class_level': student.class_level or 'N/A',
                'terms_count': student.records_count or 0,
                'avg_marks': float(avg),
                'status': 'Pass' if student.has_passed else 'Fail',
            })
        return rows

    def describe_filters(self):
        filters = self.get_filters()
        year_label = 'All Years'
        if filters['academic_year']:
            year = AcademicYear.objects.filter(id=filters['academic_year']).values_list('name', flat=True).first()
            year_label = year or 'Selected Year'

        term_label = filters['term'] or 'All Terms'
        class_label = filters['class_level'] or 'All Classes'
        search_label = filters['search'] or 'All Students'
        status_map = {
            'all': 'All Students',
            'passed': 'Passed Students',
            'failed': 'Failed Students',
        }
        status_label = status_map.get(filters['status'], 'All Students')
        return f"Year: {year_label} | Term: {term_label} | Class: {class_label} | Search: {search_label} | Status: {status_label}"

    def export_data(self, export_format):
        rows = self.get_export_rows()
        if export_format == 'pdf':
            return self.generate_pdf(rows)
        return self.generate_excel(rows)

    def generate_pdf(self, rows):
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            title='Student Performance Report',
            leftMargin=24,
            rightMargin=24,
            topMargin=24,
            bottomMargin=24,
        )
        styles = getSampleStyleSheet()
        elements = [
            Paragraph('Student Performance Report', styles['Title']),
            Spacer(1, 12),
            Paragraph(
                f"Generated on {timezone.now().strftime('%Y-%m-%d %H:%M')} | {self.describe_filters()}",
                styles['BodyText']
            ),
            Spacer(1, 18),
        ]

        table_data = [['Student Name', 'Class', 'Total Terms Recorded', 'Average (%)', 'Status']]
        for row in rows:
            table_data.append([
                row['name'],
                row['class_level'],
                str(row['terms_count']),
                f"{row['avg_marks']:.1f}",
                row['status'],
            ])

        table = Table(table_data, repeatRows=1, colWidths=[220, 120, 120, 120, 100])
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('ALIGN', (2, 1), (3, -1), 'RIGHT'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#cbd5f5')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.white]),
        ])

        for idx, row in enumerate(rows, start=1):
            bg_color = colors.HexColor('#d1fae5') if row['status'] == 'Pass' else colors.HexColor('#fee2e2')
            style.add('BACKGROUND', (0, idx), (-1, idx), bg_color)

        table.setStyle(style)
        elements.append(table)
        doc.build(elements)
        pdf = buffer.getvalue()
        buffer.close()
        response = HttpResponse(content_type='application/pdf')
        filename = timezone.now().strftime('student_performance_%Y%m%d_%H%M%S.pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response.write(pdf)
        return response

    def generate_excel(self, rows):
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = 'Performance'

        worksheet.merge_cells('A1:E1')
        worksheet['A1'] = 'Student Performance Report'
        worksheet['A1'].font = Font(size=14, bold=True)
        worksheet['A1'].alignment = Alignment(horizontal='center')

        worksheet.merge_cells('A2:E2')
        worksheet['A2'] = f"Generated on {timezone.now().strftime('%Y-%m-%d %H:%M')} | {self.describe_filters()}"
        worksheet['A2'].alignment = Alignment(horizontal='center')

        worksheet.append([])
        headers = ['Student Name', 'Class', 'Total Terms Recorded', 'Average (%)', 'Status']
        worksheet.append(headers)
        header_row_idx = worksheet.max_row
        for col_idx, header in enumerate(headers, start=1):
            cell = worksheet.cell(row=header_row_idx, column=col_idx)
            cell.font = Font(bold=True, color='FFFFFF')
            cell.fill = PatternFill(start_color='0F172A', end_color='0F172A', fill_type='solid')
            cell.alignment = Alignment(horizontal='center')

        for record in rows:
            worksheet.append([
                record['name'],
                record['class_level'],
                record['terms_count'],
                round(record['avg_marks'], 1),
                record['status'],
            ])
            status_cell = worksheet.cell(row=worksheet.max_row, column=5)
            fill_color = 'D1FAE5' if record['status'] == 'Pass' else 'FEE2E2'
            status_cell.fill = PatternFill(start_color=fill_color, end_color=fill_color, fill_type='solid')

        column_widths = [32, 18, 18, 18, 14]
        for idx, width in enumerate(column_widths, start=1):
            worksheet.column_dimensions[chr(64 + idx)].width = width

        buffer = BytesIO()
        workbook.save(buffer)
        buffer.seek(0)
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        filename = timezone.now().strftime('student_performance_%Y%m%d_%H%M%S.xlsx')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response.write(buffer.read())
        buffer.close()
        return response


class StudentPerformanceDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Detailed performance history for a single student."""

    model = Student
    template_name = 'students/student_performance_detail.html'
    context_object_name = 'student'
    permission_required = 'students.view_studentmark'
    raise_exception = True

    def get_queryset(self):
        return (
            Student.objects.select_related('school')
            .prefetch_related(
                Prefetch(
                    'academic_records',
                    queryset=StudentMark.objects.select_related('academic_year')
                    .order_by('-academic_year__name', '-term', 'subject')
                )
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        records = self.object.academic_records.all()
        stats = records.aggregate(
            total_marks=Coalesce(
                Sum('marks'),
                Value(0, output_field=DecimalField(max_digits=10, decimal_places=2)),
            ),
            avg_marks=Avg('marks'),
            subjects_count=Count('id'),
        )
        avg_marks = stats.get('avg_marks') or 0
        context.update({
            'performance_history': records,
            'total_marks': stats.get('total_marks') or 0,
            'average_marks': avg_marks,
            'subjects_count': stats.get('subjects_count') or 0,
            'has_passed': avg_marks >= 50,
        })
        return context


@login_required
@permission_required('students.view_student', raise_exception=True)
def photo_gallery(request):
    """
    View all student photos with filtering options.
    """
    photos = StudentPhoto.objects.select_related('student', 'student__family__district', 'student__school').order_by('-created_at')
    
    # Filter by District
    district_id = request.GET.get('district')
    if district_id:
        photos = photos.filter(student__family__district_id=district_id)
        
    # Filter by School
    school_id = request.GET.get('school')
    if school_id:
        photos = photos.filter(student__school_id=school_id)
        
    # Filter by Level
    level = request.GET.get('level')
    if level:
        photos = photos.filter(student__school_level=level)

    context = {
        'photos': photos,
        'districts': District.objects.order_by('name'),
        'schools': School.objects.order_by('name'),
        'levels': Student.SCHOOL_LEVEL_CHOICES,
        'selected_district': int(district_id) if district_id and district_id.isdigit() else None,
        'selected_school': int(school_id) if school_id and school_id.isdigit() else None,
        'selected_level': level,
    }
    return render(request, 'students/photo_gallery.html', context)
