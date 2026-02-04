from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.db.models import Q, Count
from django.db import models
from .models import District, Sector, Cell, Village, Province, School, Notification
from students.models import Student
from .forms import SchoolForm


@require_http_methods(["GET"])
def get_districts(request):
    """Get districts for a given province."""
    province_id = request.GET.get('province_id')
    if not province_id:
        return JsonResponse({'error': 'province_id required'}, status=400)
    
    districts = District.objects.filter(province_id=province_id).values('id', 'name')
    return JsonResponse({'districts': list(districts)})


@require_http_methods(["GET"])
def get_sectors(request):
    """Get sectors for a given district."""
    district_id = request.GET.get('district_id')
    if not district_id:
        return JsonResponse({'error': 'district_id required'}, status=400)
    
    sectors = Sector.objects.filter(district_id=district_id).values('id', 'name')
    return JsonResponse({'sectors': list(sectors)})


@require_http_methods(["GET"])
def get_cells(request):
    """Get cells for a given sector."""
    sector_id = request.GET.get('sector_id')
    if not sector_id:
        return JsonResponse({'error': 'sector_id required'}, status=400)
    
    cells = Cell.objects.filter(sector_id=sector_id).values('id', 'name')
    return JsonResponse({'cells': list(cells)})


@require_http_methods(["GET"])
def get_villages(request):
    """Get villages for a given cell."""
    cell_id = request.GET.get('cell_id')
    if not cell_id:
        return JsonResponse({'error': 'cell_id required'}, status=400)
    
    villages = Village.objects.filter(cell_id=cell_id).values('id', 'name')
    return JsonResponse({'villages': list(villages)})


# School Management Views

@login_required
def school_list(request):
    """List all schools with search and filter."""
    schools = School.objects.select_related('province', 'district', 'sector').all()
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        schools = schools.filter(
            Q(name__icontains=search_query) |
            Q(headteacher_name__icontains=search_query) |
            Q(headteacher_email__icontains=search_query)
        )
    
    # Filter by district
    district_filter = request.GET.get('district', '')
    if district_filter:
        schools = schools.filter(district_id=district_filter)

    summary = schools.aggregate(total_students=Count('students'))
    total_schools = schools.count()
    with_bank = schools.exclude(bank_account_number__isnull=True).exclude(bank_account_number__exact='').count()
    total_districts = schools.values('district_id').distinct().count()
    
    context = {
        'schools': schools,
        'search_query': search_query,
        'district_filter': district_filter,
        'total_schools': total_schools,
        'total_students': summary.get('total_students', 0),
        'with_bank': with_bank,
        'without_bank': max(total_schools - with_bank, 0),
        'total_districts': total_districts,
    }
    return render(request, 'core/school_list.html', context)


@login_required
def school_detail(request, pk):
    """View school profile with students and banking info."""
    school = get_object_or_404(School, pk=pk)
    students = Student.objects.select_related('family', 'school').filter(
        models.Q(school=school) | models.Q(school_name=school.name)
    ).distinct()
    
    context = {
        'school': school,
        'students': students,
        'student_count': students.count(),
    }
    return render(request, 'core/school_detail.html', context)


@login_required
def school_create(request):
    """Create a new school."""
    if request.method == 'POST':
        form = SchoolForm(request.POST)
        if form.is_valid():
            school = form.save()
            messages.success(request, f'School {school.name} created successfully!')
            return redirect('core:school_detail', pk=school.pk)
    else:
        form = SchoolForm()
    
    return render(request, 'core/school_form.html', {'form': form, 'title': 'Add New School'})


@login_required
def school_edit(request, pk):
    """Edit school information."""
    school = get_object_or_404(School, pk=pk)
    
    if request.method == 'POST':
        form = SchoolForm(request.POST, instance=school)
        if form.is_valid():
            form.save()
            messages.success(request, f'School {school.name} updated successfully!')
            return redirect('core:school_detail', pk=school.pk)
    else:
        form = SchoolForm(instance=school)
    
    return render(request, 'core/school_form.html', {'form': form, 'school': school, 'title': 'Edit School'})


@login_required
@require_POST
def notifications_mark_all_read(request):
    """Mark all notifications as read for current user."""
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    messages.success(request, 'All notifications marked as read.')
    return redirect(request.META.get('HTTP_REFERER', 'dashboard:index'))


@login_required
def notification_go(request, pk):
    """Mark a notification as read and redirect."""
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    if not notification.is_read:
        notification.is_read = True
        notification.save(update_fields=['is_read'])
    if notification.link:
        return redirect(notification.link)
    return redirect('dashboard:index')
