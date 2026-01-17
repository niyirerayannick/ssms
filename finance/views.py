from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.db.models import Q, Sum
from .models import SchoolFee
from .forms import FeeForm


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
    year_filter = request.GET.get('year', '')
    if year_filter:
        fees = fees.filter(academic_year=year_filter)
    
    context = {
        'fees': fees,
        'search_query': search_query,
        'status_filter': status_filter,
        'year_filter': year_filter,
    }
    return render(request, 'finance/fees_list.html', context)


@login_required
@permission_required('finance.manage_fees', raise_exception=True)
def fee_create(request):
    """Create a new fee record."""
    if request.method == 'POST':
        form = FeeForm(request.POST)
        if form.is_valid():
            fee = form.save()
            messages.success(request, f'Fee record created for {fee.student.full_name}!')
            return redirect('finance:fees_list')
    else:
        form = FeeForm()
    
    return render(request, 'finance/fee_form.html', {'form': form, 'title': 'Add Fee Payment'})


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
