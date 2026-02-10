from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.db.models import Q, Sum, Count
from core.models import District, AcademicYear
from django.http import JsonResponse
from .models import SchoolFee
from .forms import FeeForm, FamilyInsuranceForm
from insurance.models import FamilyInsurance
from families.models import Family, FamilyStudent
from students.models import Student


@login_required
@permission_required('finance.manage_fees', raise_exception=True)
def fees_list(request):
    """List all school fees with filters."""
    fees = SchoolFee.objects.select_related('student').all()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        fees = fees.filter(
            Q(student__first_name__icontains=search_query) |
            Q(student__last_name__icontains=search_query) |
            Q(student__school_name__icontains=search_query)
        )
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        fees = fees.filter(payment_status=status_filter)
    
    # Filter by academic year
    academic_year_filter = request.GET.get('academic_year', '')
    if academic_year_filter:
        fees = fees.filter(academic_year_id=academic_year_filter)

    # Filter by term
    term_filter = request.GET.get('term', '')
    if term_filter:
        fees = fees.filter(term=term_filter)

    # Filter by district (family or school district)
    district_filter = request.GET.get('district', '')
    if district_filter:
        fees = fees.filter(
            Q(student__family__district_id=district_filter) |
            Q(student__school__district_id=district_filter)
        )
    
    context = {
        'fees': fees,
        'search_query': search_query,
        'status_filter': status_filter,
        'academic_year_filter': academic_year_filter,
        'term_filter': term_filter,
        'district_filter': district_filter,
        'districts': District.objects.order_by('name'),
        'academic_years': AcademicYear.objects.order_by('-name'),
    }
    return render(request, 'finance/fees_list.html', context)


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
                return redirect('finance:dashboard')
        else:
            # Handle School Fee payment
            form = FeeForm(request.POST)
            # Allow any student to be selected (since they are loaded dynamically via JS)
            form.fields['student'].queryset = Student.objects.all()
            
            if form.is_valid():
                fee = form.save()
                messages.success(request, f'School fee recorded for {fee.student.full_name}!')
                return redirect('finance:dashboard')
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
            fee = form.save()
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
    """Comprehensive finance dashboard showing both school fees and insurance payments."""
    
    # ===== SCHOOL FEES STATISTICS =====
    total_school_fees = SchoolFee.objects.count()
    paid_school_fees = SchoolFee.objects.filter(payment_status='paid').count()
    partial_school_fees = SchoolFee.objects.filter(payment_status='partial').count()
    pending_school_fees = SchoolFee.objects.filter(payment_status='pending').count()
    overdue_school_fees = SchoolFee.objects.filter(payment_status='overdue').count()
    
    # Financial aggregates for school fees
    total_fees_required = SchoolFee.objects.aggregate(Sum('total_fees'))['total_fees__sum'] or 0
    total_fees_collected = SchoolFee.objects.aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
    total_fees_outstanding = SchoolFee.objects.aggregate(Sum('balance'))['balance__sum'] or 0
    
    # Calculate percentage
    fees_collection_percentage = round((total_fees_collected / total_fees_required * 100) if total_fees_required > 0 else 0, 1)
    
    # ===== MUTUELLE DE SANTÉ (INSURANCE) STATISTICS =====
    total_families = Family.objects.count()
    families_with_insurance = FamilyInsurance.objects.filter(coverage_status='covered').count()
    families_partially_covered = FamilyInsurance.objects.filter(coverage_status='partially_covered').count()
    families_not_covered = FamilyInsurance.objects.filter(coverage_status='not_covered').count()
    
    # Financial aggregates for insurance
    # Calculate total insurance required for ALL families (Total Members * 3000)
    total_members_all = Family.objects.aggregate(Sum('total_family_members'))['total_family_members__sum'] or 0
    total_insurance_required = total_members_all * 3000
    
    total_insurance_collected = FamilyInsurance.objects.aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
    total_insurance_outstanding = total_insurance_required - total_insurance_collected
    
    # Calculate insurance collection percentage
    insurance_collection_percentage = round((total_insurance_collected / total_insurance_required * 100) if total_insurance_required > 0 else 0, 1)
    
    # Helper to format numbers with k/M
    def format_compact(val):
        if val >= 1_000_000:
            val = val / 1_000_000
            return f"{val:.1f}M".replace('.0M', 'M')
        elif val >= 1_000:
            val = val / 1_000
            return f"{val:.1f}k".replace('.0k', 'k')
        return f"{val}"

    total_insurance_required_display = format_compact(total_insurance_required)
    
    # Students covered via family insurance
    families_covered_ids = FamilyInsurance.objects.filter(coverage_status='covered').values_list('family_id', flat=True)
    students_covered = FamilyStudent.objects.filter(family_id__in=families_covered_ids).count()
    
    # Recent payments (last 7 days)
    from django.utils import timezone
    from datetime import timedelta
    seven_days_ago = timezone.now() - timedelta(days=7)
    
    recent_school_fees = SchoolFee.objects.filter(updated_at__gte=seven_days_ago).count()
    recent_insurance = FamilyInsurance.objects.filter(updated_at__gte=seven_days_ago).count()
    
    # Top 5 families by insurance balance (need to pay more)
    families_top_outstanding = FamilyInsurance.objects.select_related('family').order_by('-balance')[:5]
    
    # Top 5 students by school fee balance (need to pay more)
    students_top_outstanding = SchoolFee.objects.select_related('student').order_by('-balance')[:5]
    
    context = {
        # School Fees
        'total_school_fees': total_school_fees,
        'paid_school_fees': paid_school_fees,
        'partial_school_fees': partial_school_fees,
        'pending_school_fees': pending_school_fees,
        'overdue_school_fees': overdue_school_fees,
        'total_fees_required': total_fees_required,
        'total_fees_collected': total_fees_collected,
        'total_fees_outstanding': total_fees_outstanding,
        'fees_collection_percentage': fees_collection_percentage,
        
        # Insurance (Mutuelle de Santé)
        'total_families': total_families,
        'families_with_insurance': families_with_insurance,
        'families_partially_covered': families_partially_covered,
        'families_not_covered': families_not_covered,
        'total_insurance_required': total_insurance_required,
        'total_insurance_required_display': total_insurance_required_display,
        'total_insurance_collected': total_insurance_collected,
        'total_insurance_outstanding': total_insurance_outstanding,
        'insurance_collection_percentage': insurance_collection_percentage,
        'students_covered': students_covered,
        
        # Recent activity
        'recent_school_fees': recent_school_fees,
        'recent_insurance': recent_insurance,
        
        # Top outstanding
        'families_top_outstanding': families_top_outstanding,
        'students_top_outstanding': students_top_outstanding,
    }
    
    return render(request, 'finance/finance_dashboard.html', context)


@login_required
@permission_required('finance.manage_fees', raise_exception=True)
def student_payment_history(request, student_id):
    """View all school fee payments for a specific student."""
    student = get_object_or_404(Student, pk=student_id)
    
    # Get all fees for this student
    fees = SchoolFee.objects.filter(student=student).order_by('-academic_year__name', '-created_at')
    
    # Calculate totals for this student
    total_required = fees.aggregate(Sum('total_fees'))['total_fees__sum'] or 0
    total_paid = fees.aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
    total_outstanding = fees.aggregate(Sum('balance'))['balance__sum'] or 0
    
    # Payment percentage
    payment_percentage = round((total_paid / total_required * 100) if total_required > 0 else 0, 1)
    
    context = {
        'student': student,
        'fees': fees,
        'total_required': total_required,
        'total_paid': total_paid,
        'total_outstanding': total_outstanding,
        'payment_percentage': payment_percentage,
    }
    return render(request, 'finance/student_payment_history.html', context)


@login_required
@permission_required('finance.manage_fees', raise_exception=True)
def add_student_payment(request, student_id):
    """Add a school fee payment for a specific student."""
    student = get_object_or_404(Student, pk=student_id)
    
    if request.method == 'POST':
        form = FeeForm(request.POST)
        if form.is_valid():
            fee = form.save(commit=False)
            # Ensure the student is set correctly
            if fee.student != student:
                fee.student = student
            fee.save()
            messages.success(request, f'School fee payment recorded for {student.full_name}!')
            return redirect('finance:student_payments', student_id=student.id)
    else:
        # Pre-fill the student field and school name
        initial_data = {
            'student': student,
            'school_name': student.school.name if student.school else '',
            'class_level': student.class_level if hasattr(student, 'class_level') else ''
        }
        form = FeeForm(initial=initial_data)
        # Disable student field since it's pre-selected
        form.fields['student'].widget.attrs['readonly'] = True
        form.fields['student'].disabled = True
    
    context = {
        'form': form,
        'student': student,
        'title': f'Add School Fee Payment - {student.full_name}'
    }
    return render(request, 'finance/student_fee_form.html', context)


@login_required
@permission_required('finance.manage_fees', raise_exception=True)
def get_student_details(request, student_id):
    """API endpoint to fetch student details including school and class information."""
    try:
        student = get_object_or_404(Student, pk=student_id)
        
        # Get latest fee record for payment dates
        latest_fee = SchoolFee.objects.filter(student=student).order_by('-created_at').first()
        payment_dates = latest_fee.payment_dates if latest_fee else ''
        
        data = {
            'success': True,
            'student_id': student.id,
            'student_name': student.full_name,
            'school_name': student.school_name or (student.school.name if student.school else ''),
            'school_id': student.school.id if student.school else None,
            'class_level': student.class_level,
            'enrollment_status': student.get_enrollment_status_display(),
            'total_fees': str(student.school.fee_amount) if student.school else '0',
            'payment_dates': payment_dates,
        }
        return JsonResponse(data)
    except Student.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Student not found'}, status=404)


@login_required
@permission_required('finance.manage_fees', raise_exception=True)
def get_family_insurance_details(request, family_id):
    """API endpoint to fetch family insurance details including amounts."""
    try:
        family = get_object_or_404(Family, pk=family_id)
        
        # Get the latest insurance record for this family
        latest_insurance = FamilyInsurance.objects.filter(family=family).order_by('-insurance_year__name').first()
        
        # Calculate total contribution across all years
        total_contribution = FamilyInsurance.objects.filter(family=family).aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
        
        # Calculate total required across all years
        total_required_all_years = FamilyInsurance.objects.filter(family=family).aggregate(Sum('required_amount'))['required_amount__sum'] or 0
        
        data = {
            'success': True,
            'family_id': family.id,
            'family_code': family.family_code,
            'family_name': (family.head_of_family or '').strip(),
            'total_members': family.total_family_members or 0,
            'total_contribution': str(total_contribution),
            'total_required_all_years': str(total_required_all_years),
        }
        
        if latest_insurance:
            data['insurance_year_id'] = latest_insurance.insurance_year_id
            data['insurance_year'] = latest_insurance.insurance_year.name if latest_insurance.insurance_year else ''
            data['required_amount'] = str(latest_insurance.required_amount)
            data['amount_paid'] = str(latest_insurance.amount_paid)
            data['balance'] = str(latest_insurance.balance)
            data['coverage_status'] = latest_insurance.get_coverage_status_display()
            data['payment_dates'] = latest_insurance.payment_dates
            data['has_existing_record'] = True
        else:
            active_year = AcademicYear.objects.filter(is_active=True).order_by('-name').first()
            data['insurance_year_id'] = active_year.id if active_year else ''
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
