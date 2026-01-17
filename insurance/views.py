from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.db.models import Q
from .models import HealthInsurance
from .forms import InsuranceForm


@login_required
@permission_required('insurance.manage_insurance', raise_exception=True)
def insurance_list(request):
    """List all insurance records with filters."""
    insurance_records = HealthInsurance.objects.select_related('student').all()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        insurance_records = insurance_records.filter(
            Q(student__full_name__icontains=search_query)
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
            messages.success(request, f'Insurance record created for {insurance.student.full_name}!')
            return redirect('insurance:insurance_list')
    else:
        form = InsuranceForm()
    
    return render(request, 'insurance/insurance_form.html', {'form': form, 'title': 'Add Insurance'})


@login_required
@permission_required('insurance.manage_insurance', raise_exception=True)
def insurance_edit(request, pk):
    """Edit an existing insurance record."""
    insurance = get_object_or_404(HealthInsurance, pk=pk)
    
    if request.method == 'POST':
        form = InsuranceForm(request.POST, instance=insurance)
        if form.is_valid():
            insurance = form.save()
            messages.success(request, f'Insurance record updated for {insurance.student.full_name}!')
            return redirect('insurance:insurance_list')
    else:
        form = InsuranceForm(instance=insurance)
    
    return render(request, 'insurance/insurance_form.html', {'form': form, 'insurance': insurance, 'title': 'Edit Insurance'})


@login_required
@permission_required('insurance.manage_insurance', raise_exception=True)
def coverage_summary(request):
    """Show coverage vs not covered summary."""
    covered = HealthInsurance.objects.filter(coverage_status='covered').count()
    not_covered = HealthInsurance.objects.filter(coverage_status='not covered').count()
    
    context = {
        'covered': covered,
        'not_covered': not_covered,
        'total': covered + not_covered,
    }
    return render(request, 'insurance/coverage_summary.html', context)

