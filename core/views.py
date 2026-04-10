from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Count
from django.db import models
from django.utils import timezone
from django.core.paginator import Paginator
from .activity import set_audit_context
from .models import District, Sector, Cell, Village, Province, School, Notification, Partner, SystemActivityLog
from students.models import Student
from .forms import SchoolForm, PartnerForm


from .utils import encode_id, decode_id

@require_http_methods(["GET"])
def get_districts(request):
    """Get districts for a given province."""
    province_id = decode_id(request.GET.get('province_id'))
    if not province_id:
        return JsonResponse({'error': 'province_id required'}, status=400)
    
    districts = District.objects.filter(province_id=province_id)
    data = [{'id': encode_id(d.id), 'name': d.name} for d in districts]
    return JsonResponse({'districts': data})


@require_http_methods(["GET"])
def get_sectors(request):
    """Get sectors for a given district."""
    district_id = decode_id(request.GET.get('district_id'))
    if not district_id:
        return JsonResponse({'error': 'district_id required'}, status=400)
    
    sectors = Sector.objects.filter(district_id=district_id)
    data = [{'id': encode_id(s.id), 'name': s.name} for s in sectors]
    return JsonResponse({'sectors': data})


@require_http_methods(["GET"])
def get_cells(request):
    """Get cells for a given sector."""
    sector_id = decode_id(request.GET.get('sector_id'))
    if not sector_id:
        return JsonResponse({'error': 'sector_id required'}, status=400)
    
    cells = Cell.objects.filter(sector_id=sector_id)
    data = [{'id': encode_id(c.id), 'name': c.name} for c in cells]
    return JsonResponse({'cells': data})


@require_http_methods(["GET"])
def get_villages(request):
    """Get villages for a given cell."""
    cell_id = decode_id(request.GET.get('cell_id'))
    if not cell_id:
        return JsonResponse({'error': 'cell_id required'}, status=400)
    
    villages = Village.objects.filter(cell_id=cell_id)
    data = [{'id': encode_id(v.id), 'name': v.name} for v in villages]
    return JsonResponse({'villages': data})


# School Management Views

@login_required
def school_list(request):
    """List all schools with search and filters."""
    schools = (
        School.objects.select_related('province', 'district', 'sector')
        .annotate(student_count=Count('students', distinct=True))
        .all()
    )

    search_query = request.GET.get('search', '')
    if search_query:
        schools = schools.filter(
            Q(name__icontains=search_query) |
            Q(headteacher_name__icontains=search_query) |
            Q(headteacher_email__icontains=search_query) |
            Q(bank_name__icontains=search_query)
        )

    province_filter = request.GET.get('province', '')
    district_filter = request.GET.get('district', '')
    sector_filter = request.GET.get('sector', '')
    bank_filter = request.GET.get('bank_status', '')

    if province_filter:
        schools = schools.filter(province_id=province_filter)

    if district_filter:
        schools = schools.filter(district_id=district_filter)

    if sector_filter:
        schools = schools.filter(sector_id=sector_filter)

    if bank_filter == 'with_bank':
        schools = schools.exclude(bank_account_number__isnull=True).exclude(bank_account_number__exact='')
    elif bank_filter == 'without_bank':
        schools = schools.filter(Q(bank_account_number__isnull=True) | Q(bank_account_number__exact=''))

    paginator = Paginator(schools.order_by('name'), 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'schools': page_obj,
        'page_obj': page_obj,
        'search_query': search_query,
        'province_filter': province_filter,
        'district_filter': district_filter,
        'sector_filter': sector_filter,
        'bank_filter': bank_filter,
        'provinces': Province.objects.order_by('name'),
        'districts': District.objects.order_by('name'),
        'sectors': Sector.objects.order_by('name'),
        'filtered_count': paginator.count,
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
            set_audit_context(
                request,
                action='Created school',
                description=f'Created school {school.name}.',
            )
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
            set_audit_context(
                request,
                action='Updated school',
                description=f'Updated school {school.name}.',
            )
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
    set_audit_context(
        request,
        action='Marked notifications as read',
        description='Marked all notifications as read.',
    )
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


# Partner Management Views

@login_required
def partner_list(request):
    """List all partners with search."""
    partners = Partner.objects.annotate(student_count=Count('students')).all()
    
    search_query = request.GET.get('search', '')
    if search_query:
        partners = partners.filter(
            Q(name__icontains=search_query) |
            Q(contact_person__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    context = {
        'partners': partners,
        'search_query': search_query,
        'total_partners': partners.count(),
    }
    return render(request, 'core/partner_list.html', context)


@login_required
def partner_detail(request, pk):
    """View partner details and linked students."""
    partner = get_object_or_404(Partner, pk=pk)
    students = partner.students.select_related('family', 'school').all()
    
    context = {
        'partner': partner,
        'students': students,
        'student_count': students.count(),
    }
    return render(request, 'core/partner_detail.html', context)


@login_required
def partner_create(request):
    """Create a new partner."""
    if request.method == 'POST':
        form = PartnerForm(request.POST)
        if form.is_valid():
            partner = form.save()
            set_audit_context(
                request,
                action='Created partner',
                description=f'Created partner {partner.name}.',
            )
            messages.success(request, f'Partner {partner.name} created successfully!')
            return redirect('core:partner_detail', pk=partner.pk)
    else:
        form = PartnerForm()
    
    return render(request, 'core/partner_form.html', {'form': form, 'title': 'Add New Partner'})


@login_required
def partner_edit(request, pk):
    """Edit partner information."""
    partner = get_object_or_404(Partner, pk=pk)
    
    if request.method == 'POST':
        form = PartnerForm(request.POST, instance=partner)
        if form.is_valid():
            form.save()
            set_audit_context(
                request,
                action='Updated partner',
                description=f'Updated partner {partner.name}.',
            )
            messages.success(request, f'Partner {partner.name} updated successfully!')
            return redirect('core:partner_detail', pk=partner.pk)
    else:
        form = PartnerForm(instance=partner)
    
    return render(request, 'core/partner_form.html', {'form': form, 'partner': partner, 'title': 'Edit Partner'})


def is_staff_user(user):
    return user.is_staff or user.is_superuser


@login_required
@user_passes_test(is_staff_user)
def system_activity_logs(request):
    """Admin activity view for authentication and user actions."""
    logs = SystemActivityLog.objects.select_related('user').all()

    search_query = request.GET.get('search', '').strip()
    event_filter = request.GET.get('event_type', '').strip()
    user_filter = request.GET.get('user', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()

    if search_query:
        logs = logs.filter(
            Q(username__icontains=search_query) |
            Q(action__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(path__icontains=search_query)
        )
    if event_filter:
        logs = logs.filter(event_type=event_filter)
    if user_filter:
        logs = logs.filter(user_id=user_filter)
    if date_from:
        logs = logs.filter(created_at__date__gte=date_from)
    if date_to:
        logs = logs.filter(created_at__date__lte=date_to)

    paginator = Paginator(logs, 30)
    page_obj = paginator.get_page(request.GET.get('page'))

    today = timezone.localdate()
    today_logs = SystemActivityLog.objects.filter(created_at__date=today)
    context = {
        'logs': page_obj,
        'page_obj': page_obj,
        'search_query': search_query,
        'event_filter': event_filter,
        'user_filter': user_filter,
        'date_from': date_from,
        'date_to': date_to,
        'event_choices': SystemActivityLog.EVENT_TYPE_CHOICES,
        'users': SystemActivityLog.objects.exclude(user__isnull=True).values('user_id', 'username').distinct().order_by('username'),
        'total_logs': SystemActivityLog.objects.count(),
        'today_logs_count': today_logs.count(),
        'today_logins_count': today_logs.filter(event_type=SystemActivityLog.EVENT_AUTH).count(),
        'today_exports_count': today_logs.filter(event_type=SystemActivityLog.EVENT_EXPORT).count(),
    }
    return render(request, 'core/system_activity_logs.html', context)
