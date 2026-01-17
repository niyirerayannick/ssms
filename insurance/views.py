from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.db.models import Q
from .models import FamilyInsurance
from .forms import InsuranceForm


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
    
    context = {
        'insurance_records': insurance_records,
        'search_query': search_query,
        'status_filter': status_filter,
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

