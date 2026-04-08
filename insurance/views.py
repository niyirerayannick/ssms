from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.db.models import Q, Sum
from django.core.paginator import Paginator
from core.models import District, AcademicYear
from .models import FamilyInsurance
from .forms import InsuranceForm
from families.models import Family, FamilyStudent, MutuelleContributionSettings


@login_required
@permission_required('insurance.manage_insurance', raise_exception=True)
def mutuelle_dashboard(request):
    """Dashboard focused on Mutuelle de Santé only."""
    total_families = Family.objects.count()
    families_with_insurance = FamilyInsurance.objects.filter(coverage_status='covered').count()
    families_partially_covered = FamilyInsurance.objects.filter(coverage_status='partially_covered').count()
    families_not_covered = FamilyInsurance.objects.filter(coverage_status='not_covered').count()

    total_members_all = Family.objects.aggregate(Sum('total_family_members'))['total_family_members__sum'] or 0
    amount_per_person = MutuelleContributionSettings.current_amount()
    total_insurance_required = total_members_all * amount_per_person
    total_insurance_collected = FamilyInsurance.objects.aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
    total_insurance_outstanding = total_insurance_required - total_insurance_collected
    insurance_collection_percentage = round((total_insurance_collected / total_insurance_required * 100) if total_insurance_required > 0 else 0, 1)

    families_covered_ids = FamilyInsurance.objects.filter(coverage_status='covered').values_list('family_id', flat=True)
    students_covered = FamilyStudent.objects.filter(family_id__in=families_covered_ids).count()
    coverage_percentage = round((students_covered / total_members_all * 100) if total_members_all > 0 else 0, 1)

    from django.utils import timezone
    from datetime import timedelta
    seven_days_ago = timezone.now() - timedelta(days=7)
    recent_insurance = FamilyInsurance.objects.filter(updated_at__gte=seven_days_ago).count()

    insurance_queryset = FamilyInsurance.objects.select_related('family', 'insurance_year').order_by('-created_at')
    paginator = Paginator(insurance_queryset, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'total_families': total_families,
        'families_with_insurance': families_with_insurance,
        'families_partially_covered': families_partially_covered,
        'families_not_covered': families_not_covered,
        'amount_per_person': amount_per_person,
        'total_insurance_required': total_insurance_required,
        'total_insurance_collected': total_insurance_collected,
        'total_insurance_outstanding': total_insurance_outstanding,
        'insurance_collection_percentage': insurance_collection_percentage,
        'students_covered': students_covered,
        'total_members_all': total_members_all,
        'coverage_percentage': coverage_percentage,
        'recent_insurance': recent_insurance,
        'insurance_records': page_obj,
        'page_obj': page_obj,
    }
    return render(request, 'insurance/mutuelle_dashboard.html', context)


@login_required
@permission_required('insurance.manage_insurance', raise_exception=True)
def insurance_list(request):
    """List all insurance records with filters."""
    insurance_records = FamilyInsurance.objects.select_related('family').all()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        insurance_records = insurance_records.filter(
            Q(family__head_of_family__icontains=search_query) |
            Q(family__family_code__icontains=search_query)
        )
    
    # Filter by coverage status
    status_filter = request.GET.get('status', '')
    if status_filter:
        insurance_records = insurance_records.filter(coverage_status=status_filter)

    # Filter by academic year
    academic_year_filter = request.GET.get('academic_year', '')
    if academic_year_filter:
        insurance_records = insurance_records.filter(insurance_year_id=academic_year_filter)

    # Filter by district
    district_filter = request.GET.get('district', '')
    if district_filter:
        insurance_records = insurance_records.filter(family__district_id=district_filter)
    
    # Pagination
    paginator = Paginator(insurance_records.order_by('-created_at'), 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'insurance_records': page_obj,
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'district_filter': district_filter,
        'districts': District.objects.order_by('name'),
        'academic_year_filter': academic_year_filter,
        'academic_years': AcademicYear.objects.order_by('-name'),
    }
    return render(request, 'insurance/insurance_list.html', context)


@login_required
@permission_required('insurance.manage_insurance', raise_exception=True)
def insurance_create(request):
    """Create a new insurance record."""
    if request.method == 'POST':
        form = InsuranceForm(request.POST)
        if form.is_valid():
            insurance = form.save()
            messages.success(request, f'Mutuelle de Santé payment recorded for family {insurance.family.family_code}!')
            return redirect('insurance:insurance_list')
    else:
        form = InsuranceForm()
    
    return render(request, 'insurance/insurance_form.html', {'form': form, 'title': 'Add Mutuelle Payment'})


@login_required
@permission_required('insurance.manage_insurance', raise_exception=True)
def insurance_edit(request, pk):
    """Edit an existing insurance record."""
    insurance = get_object_or_404(FamilyInsurance, pk=pk)
    
    if request.method == 'POST':
        form = InsuranceForm(request.POST, instance=insurance)
        if form.is_valid():
            insurance = form.save()
            messages.success(request, f'Mutuelle record updated for family {insurance.family.family_code}!')
            return redirect('insurance:insurance_list')
    else:
        form = InsuranceForm(instance=insurance)
    
    return render(request, 'insurance/insurance_form.html', {'form': form, 'insurance': insurance, 'title': 'Edit Mutuelle Payment'})


@login_required
@permission_required('insurance.manage_insurance', raise_exception=True)
def coverage_summary(request):
    """Show coverage vs not covered summary."""
    covered = FamilyInsurance.objects.filter(coverage_status='covered').count()
    partially_covered = FamilyInsurance.objects.filter(coverage_status='partially_covered').count()
    not_covered = FamilyInsurance.objects.filter(coverage_status='not_covered').count()
    
    context = {
        'covered': covered,
        'partially_covered': partially_covered,
        'not_covered': not_covered,
        'total': covered + partially_covered + not_covered,
    }
    return render(request, 'insurance/coverage_summary.html', context)

