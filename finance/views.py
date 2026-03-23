from collections import OrderedDict
from decimal import Decimal
from urllib.parse import urlencode

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Sum, Count
from django.core.paginator import Paginator
from django.forms import formset_factory
from django.urls import reverse
from django.utils import timezone
from core.models import District, AcademicYear, School
from django.http import JsonResponse
from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from .models import SchoolFee, SchoolFeePayment
from .forms import (
    FeeForm,
    FamilyInsuranceForm,
    BulkFeeFilterForm,
    BulkStudentFeeForm,
    SchoolFeePaymentForm,
)
from insurance.models import FamilyInsurance
from families.models import Family, FamilyStudent
from students.models import Student


def _get_filtered_fees(request):
    """Return school fees queryset with the same filters used by the list page."""

    fees = SchoolFee.objects.select_related('student', 'student__school', 'academic_year').all()

    search_query = request.GET.get('search', '')
    if search_query:
        fees = fees.filter(
            Q(student__first_name__icontains=search_query) |
            Q(student__last_name__icontains=search_query) |
            Q(student__school_name__icontains=search_query)
        )

    status_filter = request.GET.get('status', '')
    if status_filter:
        fees = fees.filter(payment_status=status_filter)

    academic_year_filter = request.GET.get('academic_year', '')
    if academic_year_filter:
        fees = fees.filter(academic_year_id=academic_year_filter)

    term_filter = request.GET.get('term', '')
    if term_filter:
        fees = fees.filter(term=term_filter)

    district_filter = request.GET.get('district', '')
    if district_filter:
        fees = fees.filter(
            Q(student__family__district_id=district_filter) |
            Q(student__school__district_id=district_filter)
        )

    return fees, {
        'search_query': search_query,
        'status_filter': status_filter,
        'academic_year_filter': academic_year_filter,
        'term_filter': term_filter,
        'district_filter': district_filter,
    }


def _build_fee_snapshot(student, total_fees=None):
    """Prepare school/class/bank snapshot defaults from the current student school."""
    school = student.school if student else None
    snapshot = {
        'school_name': school.name if school else getattr(student, 'school_name', ''),
        'class_level': getattr(student, 'class_level', ''),
        'bank_name': school.bank_name if school and school.bank_name else '',
        'bank_account_name': school.bank_account_name if school and school.bank_account_name else '',
        'bank_account_number': school.bank_account_number if school and school.bank_account_number else '',
    }
    if total_fees is not None:
        snapshot['total_fees'] = total_fees
    return snapshot


def _get_or_create_school_fee(student, academic_year, term, total_fees=None):
    """Return the fee plan for a student term, creating it when needed."""
    defaults = _build_fee_snapshot(
        student,
        total_fees if total_fees is not None else (student.school.fee_amount if student and student.school else Decimal('0'))
    )
    fee, created = SchoolFee.objects.get_or_create(
        student=student,
        academic_year=academic_year,
        term=term,
        defaults=defaults,
    )
    if not created:
        needs_save = False
        snapshot = _build_fee_snapshot(student)
        for field, value in snapshot.items():
            if not getattr(fee, field):
                setattr(fee, field, value)
                needs_save = True
        if total_fees is not None and fee.total_fees != total_fees:
            fee.total_fees = total_fees
            needs_save = True
        if needs_save:
            fee.save()
    return fee


@login_required
@permission_required('finance.manage_fees', raise_exception=True)
def fees_list(request):
    """List all school fees with filters."""
    fees, filters = _get_filtered_fees(request)
    
    # Pagination
    paginator = Paginator(fees.order_by('-created_at'), 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'fees': page_obj,
        'page_obj': page_obj,
        **filters,
        'districts': District.objects.order_by('name'),
        'academic_years': AcademicYear.objects.order_by('-name'),
    }
    return render(request, 'finance/fees_list.html', context)


@login_required
@permission_required('finance.manage_fees', raise_exception=True)
def export_fees_excel(request):
    """Export filtered school fee records with student and school banking details."""

    fees, _filters = _get_filtered_fees(request)
    fees = fees.order_by('student__last_name', 'student__first_name', '-academic_year__name', 'term')

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = 'School Fees Export'

    headers = [
        'Student Name',
        'Academic Year',
        'Term',
        'Level',
        'School',
        'Bank Name',
        'Bank Account Name',
        'Bank Account Number',
        'Required Amount',
        'Amount Paid',
        'Balance To Pay',
        'Status',
    ]
    worksheet.append(headers)

    header_fill = PatternFill(start_color='0F766E', end_color='0F766E', fill_type='solid')
    header_font = Font(bold=True, color='FFFFFF')
    for cell in worksheet[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center')

    for fee in fees:
        worksheet.append([
            fee.student.full_name if fee.student else 'N/A',
            fee.academic_year.name if fee.academic_year else 'N/A',
            fee.get_term_display(),
            fee.class_level or (fee.student.class_level if fee.student else 'N/A'),
            fee.school_name or (fee.student.school.name if fee.student and fee.student.school else 'N/A'),
            fee.bank_name or 'N/A',
            fee.bank_account_name or 'N/A',
            fee.bank_account_number or 'N/A',
            float(fee.total_fees),
            float(fee.amount_paid),
            float(fee.balance),
            fee.get_payment_status_display(),
        ])

    for column_cells in worksheet.columns:
        max_length = 0
        column_letter = column_cells[0].column_letter
        for cell in column_cells:
            value = '' if cell.value is None else str(cell.value)
            if len(value) > max_length:
                max_length = len(value)
        worksheet.column_dimensions[column_letter].width = min(max_length + 2, 30)

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="school_fees_students_export.xlsx"'
    workbook.save(response)
    return response


@login_required
@permission_required('finance.manage_fees', raise_exception=True)
def school_fees_dashboard(request):
    """Dashboard focused on school fees only."""
    total_school_fees = SchoolFee.objects.count()
    students_paid_count = Student.objects.filter(fees__payment_status='paid').distinct().count()
    academic_year_count = AcademicYear.objects.filter(school_fees__isnull=False).distinct().count()
    term_record_count = total_school_fees

    total_fees_required = SchoolFee.objects.aggregate(Sum('total_fees'))['total_fees__sum'] or 0
    total_fees_collected = SchoolFee.objects.aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
    total_fees_outstanding = SchoolFee.objects.aggregate(Sum('balance'))['balance__sum'] or 0
    fees_collection_percentage = round((total_fees_collected / total_fees_required * 100) if total_fees_required > 0 else 0, 1)

    from django.utils import timezone
    from datetime import timedelta
    seven_days_ago = timezone.now() - timedelta(days=7)
    recent_school_fees = SchoolFee.objects.filter(updated_at__gte=seven_days_ago).count()

    fees_queryset = (
        SchoolFee.objects.select_related('student', 'student__school')
        .order_by('student__school__name', 'student__last_name')
    )

    school_groups_map = OrderedDict()
    for fee in fees_queryset:
        student = fee.student
        school = student.school if student else None
        school_name = school.name if school else (fee.school_name or 'Unassigned School')
        key = ('school', school.id) if school else ('external', school_name.lower())
        if key not in school_groups_map:
            school_groups_map[key] = {
                'school_id': school.id if school else None,
                'school_name': school_name,
                'student_ids': set(),
                'total_required': Decimal('0'),
                'total_paid': Decimal('0'),
                'total_balance': Decimal('0'),
                'status_counts': {
                    'paid': 0,
                    'partial': 0,
                    'pending': 0,
                    'overdue': 0,
                },
            }

        entry = school_groups_map[key]
        entry['student_ids'].add(student.id if student else None)
        entry['total_required'] += fee.total_fees
        entry['total_paid'] += fee.amount_paid
        entry['total_balance'] += fee.balance
        status = fee.payment_status or 'pending'
        if status in entry['status_counts']:
            entry['status_counts'][status] += 1

    school_fee_groups = []
    for entry in school_groups_map.values():
        school_fee_groups.append({
            'school_id': entry['school_id'],
            'school_name': entry['school_name'],
            'student_count': len({sid for sid in entry['student_ids'] if sid}),
            'total_required': entry['total_required'],
            'total_paid': entry['total_paid'],
            'total_balance': entry['total_balance'],
            'status_counts': entry['status_counts'],
            'has_linked_school': entry['school_id'] is not None,
        })

    paginator = Paginator(school_fee_groups, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'students_paid_count': students_paid_count,
        'academic_year_count': academic_year_count,
        'term_record_count': term_record_count,
        'total_fees_required': total_fees_required,
        'total_fees_collected': total_fees_collected,
        'total_fees_outstanding': total_fees_outstanding,
        'fees_collection_percentage': fees_collection_percentage,
        'recent_school_fees': recent_school_fees,
        'school_fee_groups': page_obj,
        'page_obj': page_obj,
    }
    return render(request, 'finance/school_fees_dashboard.html', context)


@login_required
@permission_required('finance.manage_fees', raise_exception=True)
def school_fee_students(request, school_id):
    """Display aggregated fee information for students within a school."""
    school = get_object_or_404(School, pk=school_id)

    school_fees = (
        SchoolFee.objects.filter(student__school=school)
        .select_related('student', 'academic_year')
        .order_by('student__first_name', 'student__last_name')
    )

    student_map = OrderedDict()
    for fee in school_fees:
        student = fee.student
        if not student:
            continue
        entry = student_map.setdefault(
            student.id,
            {
                'student': student,
                'total_required': Decimal('0'),
                'total_paid': Decimal('0'),
                'total_balance': Decimal('0'),
                'latest_status': fee.payment_status,
                'status_display': fee.get_payment_status_display(),
            },
        )
        entry['total_required'] += fee.total_fees
        entry['total_paid'] += fee.amount_paid
        entry['total_balance'] += fee.balance
        entry['latest_status'] = fee.payment_status
        entry['status_display'] = fee.get_payment_status_display()

    student_summaries = list(student_map.values())
    school_totals = {
        'required': sum((item['total_required'] for item in student_summaries), Decimal('0')),
        'paid': sum((item['total_paid'] for item in student_summaries), Decimal('0')),
        'balance': sum((item['total_balance'] for item in student_summaries), Decimal('0')),
        'student_count': len(student_summaries),
    }

    context = {
        'school': school,
        'student_summaries': student_summaries,
        'school_totals': school_totals,
    }
    return render(request, 'finance/school_fee_students.html', context)


@login_required
@permission_required('finance.manage_fees', raise_exception=True)
def bulk_fee_entry(request):
    """Allow finance admins to record or update many school fee entries at once."""

    data_source = request.POST if request.method == 'POST' else request.GET
    filter_form = BulkFeeFilterForm(data_source or None)
    formset = None
    table_rows = []
    students_loaded = False
    selected_filters = {}
    selected_school = None
    selected_year = None
    term_display = None
    category_label = None
    summary = {
        'student_count': 0,
        'total_required': Decimal('0'),
        'total_paid': Decimal('0'),
    }

    if filter_form.is_valid():
        students_loaded = True
        academic_year = filter_form.cleaned_data['academic_year']
        school = filter_form.cleaned_data.get('school')
        partner = filter_form.cleaned_data.get('partner')
        term = filter_form.cleaned_data['term']
        category = filter_form.cleaned_data['category']
        payment_date = filter_form.cleaned_data.get('payment_date') or timezone.now().date()

        selected_school = school
        selected_partner = partner
        selected_year = academic_year
        term_display = dict(SchoolFee.TERM_CHOICES).get(term, term)
        category_label = dict(filter_form.fields['category'].choices).get(category, category)

        # If partner selected, load students for partner; otherwise load by school
        if partner:
            student_qs = (
                Student.objects.filter(partner=partner, is_active=True)
                .select_related('school', 'partner')
                .order_by('first_name', 'last_name')
            )
        else:
            student_qs = (
                Student.objects.filter(school=school, is_active=True)
                .select_related('school', 'partner')
                .order_by('first_name', 'last_name')
            )
        if category in ['primary', 'secondary']:
            student_qs = student_qs.filter(school_level=category)

        students = list(student_qs)
        existing_fee_map = {
            fee.student_id: fee
            for fee in SchoolFee.objects.filter(
                student__in=students,
                academic_year=academic_year,
                term=term,
            )
        }

        initial_data = []
        total_required_sum = Decimal('0')
        total_paid_sum = Decimal('0')
        for student in students:
            existing_fee = existing_fee_map.get(student.id)
            default_total = existing_fee.total_fees if existing_fee else (student.school.fee_amount if student.school else Decimal('0'))
            default_paid = existing_fee.amount_paid if existing_fee else Decimal('0')
            total_required_sum += default_total or Decimal('0')
            total_paid_sum += default_paid or Decimal('0')
            initial_data.append({
                'student_id': student.id,
                'total_fees': default_total,
                'amount_paid': default_paid,
            })

        BulkFormSet = formset_factory(BulkStudentFeeForm, extra=0)
        formset_valid = False
        if request.method == 'POST':
            formset = BulkFormSet(request.POST)
            formset_valid = formset.is_valid()
            if formset_valid:
                created_count = 0
                updated_count = 0
                student_lookup = {student.id: student for student in students}
                with transaction.atomic():
                    for form in formset:
                        student_id = form.cleaned_data.get('student_id')
                        total_fees = form.cleaned_data.get('total_fees')
                        amount_paid = form.cleaned_data.get('amount_paid')

                        if not student_id or student_id not in student_lookup:
                            continue
                        if total_fees is None:
                            continue
                        if amount_paid is None:
                            amount_paid = Decimal('0')

                        student_instance = student_lookup[student_id]
                        defaults = {
                            'total_fees': total_fees,
                            'school_name': student_instance.school.name if student_instance.school else student_instance.school_name,
                            'class_level': student_instance.class_level,
                            'bank_name': student_instance.school.bank_name if student_instance.school and student_instance.school.bank_name else '',
                            'bank_account_name': student_instance.school.bank_account_name if student_instance.school and student_instance.school.bank_account_name else '',
                            'bank_account_number': student_instance.school.bank_account_number if student_instance.school and student_instance.school.bank_account_number else '',
                            'recorded_by': request.user,
                            'payment_date': payment_date,
                        }

                        fee, created = SchoolFee.objects.update_or_create(
                            student=student_instance,
                            academic_year=academic_year,
                            term=term,
                            defaults=defaults,
                        )
                        if amount_paid and amount_paid > 0:
                            existing_payment = fee.payments.filter(
                                payment_date=payment_date,
                                amount_paid=amount_paid,
                                recorded_by=request.user,
                            ).first()
                            if not existing_payment:
                                SchoolFeePayment.objects.create(
                                    school_fee=fee,
                                    amount_paid=amount_paid,
                                    payment_date=payment_date,
                                    recorded_by=request.user,
                                    payment_method='bank',
                                )
                        if created:
                            created_count += 1
                        else:
                            updated_count += 1

                messages.success(
                    request,
                    f"Bulk fees saved{f' for {partner.name}' if partner else f' for {school.name}'}: {created_count} new, {updated_count} updated.",
                )
                params_dict = {
                    'academic_year': academic_year.id,
                    'term': term,
                    'category': category,
                    'payment_date': payment_date.isoformat(),
                }
                if partner:
                    params_dict['partner'] = partner.id
                else:
                    if school:
                        params_dict['school'] = school.id
                params = urlencode(params_dict)
                return redirect(f"{reverse('finance:bulk_fee_entry')}?{params}")
        else:
            formset = BulkFormSet(initial=initial_data)

        if formset is not None:
            for idx, student in enumerate(students):
                if idx >= len(formset.forms):
                    break
                table_rows.append({
                    'student': student,
                    'form': formset.forms[idx],
                    'existing_fee': existing_fee_map.get(student.id),
                })

        summary = {
            'student_count': len(students),
            'total_required': total_required_sum,
            'total_paid': total_paid_sum,
        }
        selected_filters = {
            'academic_year': academic_year.id,
            'term': term,
            'category': category,
            'payment_date': payment_date.isoformat(),
        }
        if partner:
            selected_filters['partner'] = partner.id
        else:
            if school:
                selected_filters['school'] = school.id

    context = {
        'filter_form': filter_form,
        'formset': formset,
        'table_rows': table_rows,
        'students_loaded': students_loaded,
        'selected_filters': selected_filters,
        'selected_school': selected_school,
        'selected_year': selected_year,
        'term_display': term_display,
        'category_label': category_label,
        'summary': summary,
    }
    return render(request, 'finance/bulk_fee_entry.html', context)


@login_required
@permission_required('finance.manage_fees', raise_exception=True)
def fee_create(request):
    """Create a new fee record - for both school fees and Mutuelle de Santé."""
    payment_type = request.GET.get('type', 'school_fee')  # 'school_fee' or 'insurance'
    
    if request.method == 'POST':
        if payment_type == 'insurance':
            # Handle Mutuelle de Santé (Family Insurance) payment
            form = FamilyInsuranceForm(request.POST)
            # Allow any family to be selected (since they are loaded dynamically via JS)
            # This ensures validation passes even if the initial queryset was empty
            form.fields['family'].queryset = Family.objects.all()
            
            if form.is_valid():
                insurance = form.save()
                messages.success(request, f'Mutuelle de Santé payment recorded for family {insurance.family.family_code}!')
                return redirect('insurance:mutuelle_dashboard')
        else:
            # Handle School Fee payment
            form = FeeForm(request.POST)
            # Allow any student to be selected (since they are loaded dynamically via JS)
            form.fields['student'].queryset = Student.objects.all()
            
            if form.is_valid():
                fee = form.save(commit=False)
                if not fee.payment_date:
                    fee.payment_date = timezone.now().date()
                fee.recorded_by = request.user
                fee.save()
                messages.success(request, f'School fee recorded for {fee.student.full_name}!')
                return redirect('finance:school_fees_dashboard')
    else:
        if payment_type == 'insurance':
            form = FamilyInsuranceForm()
            # Initialize with empty queryset - families will be loaded via AJAX based on district
            form.fields['family'].queryset = Family.objects.none()
        else:
            form = FeeForm()
            # Initialize with empty queryset - students will be loaded via AJAX based on district
            form.fields['student'].queryset = Student.objects.none()
    
    context = {
        'form': form,
        'payment_type': payment_type,
        'districts': District.objects.order_by('name'),
        'title': 'Add Mutuelle Payment' if payment_type == 'insurance' else 'Add School Fee Payment'
    }
    return render(request, 'finance/fee_form.html', context)


@login_required
@permission_required('finance.manage_fees', raise_exception=True)
def fee_edit(request, pk):
    """Edit an existing fee record."""
    fee = get_object_or_404(SchoolFee, pk=pk)
    
    if request.method == 'POST':
        form = FeeForm(request.POST, instance=fee)
        if form.is_valid():
            fee = form.save(commit=False)
            if not fee.payment_date:
                fee.payment_date = timezone.now().date()
            if not fee.recorded_by:
                fee.recorded_by = request.user
            fee.save()
            messages.success(request, f'Fee record updated for {fee.student.full_name}!')
            return redirect('finance:fees_list')
    else:
        form = FeeForm(instance=fee)
    
    return render(request, 'finance/fee_form.html', {'form': form, 'fee': fee, 'title': 'Edit Fee Payment'})


@login_required
@permission_required('finance.manage_fees', raise_exception=True)
def overdue_fees(request):
    """List all overdue fees."""
    overdue = SchoolFee.objects.filter(payment_status='overdue').select_related('student')
    
    context = {
        'overdue_fees': overdue,
    }
    return render(request, 'finance/overdue_fees.html', context)


@login_required
@permission_required('finance.manage_fees', raise_exception=True)
def finance_dashboard(request):
    """Legacy finance dashboard endpoint redirected to School Fees dashboard."""
    return redirect('finance:school_fees_dashboard')


@login_required
@permission_required('finance.manage_fees', raise_exception=True)
def student_payment_history(request, student_id):
    """View all school fee payments for a specific student."""
    student = get_object_or_404(Student, pk=student_id)
    
    # Get all fees for this student
    fees_qs = (
        SchoolFee.objects.filter(student=student)
        .select_related('academic_year')
        .prefetch_related('payments')
        .order_by('-academic_year__name', '-term')
    )
    
    # Calculate totals for this student
    total_required = fees_qs.aggregate(Sum('total_fees'))['total_fees__sum'] or 0
    total_paid = fees_qs.aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
    total_outstanding = fees_qs.aggregate(Sum('balance'))['balance__sum'] or 0
    
    # Payment percentage
    payment_percentage = round((total_paid / total_required * 100) if total_required > 0 else 0, 1)

    fees = list(fees_qs)
    payment_records = list(
        SchoolFeePayment.objects.filter(school_fee__student=student)
        .select_related('school_fee', 'school_fee__academic_year')
        .order_by('-payment_date', '-created_at')
    )
    
    context = {
        'student': student,
        'fees': fees,
        'total_required': total_required,
        'total_paid': total_paid,
        'total_outstanding': total_outstanding,
        'payment_percentage': payment_percentage,
        'payment_records': payment_records,
    }
    return render(request, 'finance/student_payment_history.html', context)


@login_required
@permission_required('finance.manage_fees', raise_exception=True)
def add_student_payment(request, student_id):
    """Add a school fee payment transaction for a specific student."""
    student = get_object_or_404(Student, pk=student_id)
    
    if request.method == 'POST':
        form = SchoolFeePaymentForm(request.POST, student=student)
        if form.is_valid():
            academic_year = form.cleaned_data['academic_year']
            term = form.cleaned_data['term']
            total_fees = form.cleaned_data['total_fees']
            fee = _get_or_create_school_fee(student, academic_year, term, total_fees=total_fees)

            payment = form.save(commit=False)
            payment.school_fee = fee
            payment.recorded_by = request.user
            payment.save()
            messages.success(request, f'School fee payment recorded for {student.full_name}!')
            return redirect('finance:student_payments', student_id=student.id)
    else:
        form = SchoolFeePaymentForm(student=student)
    
    context = {
        'form': form,
        'student': student,
        'title': f'Add School Fee Payment - {student.full_name}',
        'student_school_name': student.school.name if student.school else student.school_name,
        'student_bank_name': student.school.bank_name if student.school and student.school.bank_name else '',
        'student_bank_account_name': student.school.bank_account_name if student.school and student.school.bank_account_name else '',
        'student_bank_account_number': student.school.bank_account_number if student.school and student.school.bank_account_number else '',
    }
    return render(request, 'finance/student_fee_form.html', context)


from core.utils import encode_id, decode_id


@login_required
@permission_required('finance.manage_fees', raise_exception=True)
def get_student_details(request, student_id):
    """API endpoint to fetch student details including school and class information."""
    try:
        # Support both raw integer ID and HashID
        student_id = decode_id(student_id)
        student = get_object_or_404(Student, pk=student_id)
        
        # Get latest fee record for payment dates
        latest_fee = SchoolFee.objects.filter(student=student).order_by('-created_at').first()
        payment_dates = latest_fee.payment_dates if latest_fee else ''
        
        data = {
            'success': True,
            'student_id': encode_id(student.id),
            'student_name': student.full_name,
            'school_name': student.school_name or (student.school.name if student.school else ''),
            'school_id': encode_id(student.school.id) if student.school else None,
            'class_level': student.class_level,
            'enrollment_status': student.get_enrollment_status_display(),
            'total_fees': str(student.school.fee_amount) if student.school else '0',
            'payment_dates': payment_dates,
            'bank_name': student.school.bank_name if student.school and student.school.bank_name else '',
            'bank_account_name': student.school.bank_account_name if student.school and student.school.bank_account_name else '',
            'bank_account_number': student.school.bank_account_number if student.school and student.school.bank_account_number else '',
        }
        return JsonResponse(data)
    except Student.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Student not found'}, status=404)


@login_required
@permission_required('finance.manage_fees', raise_exception=True)
def get_family_insurance_details(request, family_id):
    """API endpoint to fetch family insurance details including amounts."""
    try:
        # Support both raw integer ID and HashID
        family_id = decode_id(family_id)
        family = get_object_or_404(Family, pk=family_id)
        
        # Get the latest insurance record for this family
        latest_insurance = FamilyInsurance.objects.filter(family=family).order_by('-insurance_year__name').first()
        
        # Calculate total contribution across all years
        total_contribution = FamilyInsurance.objects.filter(family=family).aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
        
        # Calculate total required across all years
        total_required_all_years = FamilyInsurance.objects.filter(family=family).aggregate(Sum('required_amount'))['required_amount__sum'] or 0
        
        data = {
            'success': True,
            'family_id': encode_id(family.id),
            'family_code': family.family_code,
            'family_name': (family.head_of_family or '').strip(),
            'total_members': family.total_family_members or 0,
            'total_contribution': str(total_contribution),
            'total_required_all_years': str(total_required_all_years),
        }
        
        if latest_insurance:
            data['insurance_year_id'] = encode_id(latest_insurance.insurance_year_id) if latest_insurance.insurance_year_id else None
            data['insurance_year'] = latest_insurance.insurance_year.name if latest_insurance.insurance_year else ''
            data['required_amount'] = str(latest_insurance.required_amount)
            data['amount_paid'] = str(latest_insurance.amount_paid)
            data['balance'] = str(latest_insurance.balance)
            data['coverage_status'] = latest_insurance.get_coverage_status_display()
            data['payment_dates'] = latest_insurance.payment_dates
            data['has_existing_record'] = True
        else:
            active_year = AcademicYear.objects.filter(is_active=True).order_by('-name').first()
            data['insurance_year_id'] = encode_id(active_year.id) if active_year else None
            data['insurance_year'] = active_year.name if active_year else ''
            data['required_amount'] = str(family.total_contribution)
            data['amount_paid'] = '0'
            data['balance'] = str(family.total_contribution)
            data['coverage_status'] = 'Not Covered'
            data['payment_dates'] = ''
            data['has_existing_record'] = False
        
        return JsonResponse(data)
    except Family.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Family not found'}, status=404)


@login_required
@permission_required('finance.manage_fees', raise_exception=True)
def get_families_by_district(request, district_id):
    """API endpoint to fetch families in a district."""
    families = Family.objects.filter(district_id=district_id).values('id', 'family_code', 'head_of_family')
    data = [{'id': f['id'], 'text': f"{f['family_code']} - {f['head_of_family']}"} for f in families]
    return JsonResponse({'success': True, 'results': data})


@login_required
@permission_required('finance.manage_fees', raise_exception=True)
def get_students_by_district(request, district_id):
    """API endpoint to fetch students in a district."""
    students = Student.objects.filter(
        Q(family__district_id=district_id) | Q(school__district_id=district_id)
    ).distinct().values('id', 'first_name', 'last_name', 'school_name')
    
    data = []
    for s in students:
        full_name = f"{s['first_name']} {s['last_name']}"
        school = s['school_name'] or "No School"
        data.append({'id': s['id'], 'text': f"{full_name} ({school})"})
        
    return JsonResponse({'success': True, 'results': data})
