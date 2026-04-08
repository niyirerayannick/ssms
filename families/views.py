from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from .models import Family, FamilyStudent, MutuelleContributionSettings
from core.models import District, Province
from .forms import FamilyForm, MutuelleContributionSettingsForm
from students.models import Student


@login_required
def family_create(request):
    """Create a new family."""
    settings_instance = MutuelleContributionSettings.get_solo()
    can_edit_mutuelle_amount = request.user.is_staff or request.user.is_superuser
    if request.method == 'POST':
        form = FamilyForm(request.POST)
        settings_form = (
            MutuelleContributionSettingsForm(request.POST, instance=settings_instance, prefix='mutuelle')
            if can_edit_mutuelle_amount else None
        )
        settings_valid = settings_form.is_valid() if settings_form is not None else True
        if form.is_valid() and settings_valid:
            family = form.save()
            if settings_form is not None:
                settings_form.save()
            messages.success(request, f'Family {family.family_code} created successfully!')
            return redirect('families:family_detail', pk=family.pk)
    else:
        form = FamilyForm()
        settings_form = (
            MutuelleContributionSettingsForm(instance=settings_instance, prefix='mutuelle')
            if can_edit_mutuelle_amount else None
        )

    return render(request, 'families/family_form.html', {
        'form': form,
        'settings_form': settings_form,
        'settings_form_amount_field_id': settings_form['amount_per_person'].id_for_label if settings_form else '',
        'mutuelle_amount_per_person': settings_instance.amount_per_person,
        'can_edit_mutuelle_amount': can_edit_mutuelle_amount,
        'title': 'Add New Family',
    })


@login_required
def family_edit(request, pk):
    """Edit family information."""
    family = get_object_or_404(Family, pk=pk)
    settings_instance = MutuelleContributionSettings.get_solo()
    can_edit_mutuelle_amount = request.user.is_staff or request.user.is_superuser
    
    if request.method == 'POST':
        form = FamilyForm(request.POST, instance=family)
        settings_form = (
            MutuelleContributionSettingsForm(request.POST, instance=settings_instance, prefix='mutuelle')
            if can_edit_mutuelle_amount else None
        )
        settings_valid = settings_form.is_valid() if settings_form is not None else True
        if form.is_valid() and settings_valid:
            form.save()
            if settings_form is not None:
                settings_form.save()
            messages.success(request, f'Family {family.family_code} updated successfully!')
            return redirect('families:family_detail', pk=family.pk)
    else:
        form = FamilyForm(instance=family)
        settings_form = (
            MutuelleContributionSettingsForm(instance=settings_instance, prefix='mutuelle')
            if can_edit_mutuelle_amount else None
        )

    return render(request, 'families/family_form.html', {
        'form': form,
        'family': family,
        'settings_form': settings_form,
        'settings_form_amount_field_id': settings_form['amount_per_person'].id_for_label if settings_form else '',
        'mutuelle_amount_per_person': settings_instance.amount_per_person,
        'can_edit_mutuelle_amount': can_edit_mutuelle_amount,
        'title': 'Edit Family',
    })


@login_required
def family_detail(request, pk):
    """View family profile with students, insurance, and location."""
    family = get_object_or_404(Family, pk=pk)
    linked_students = list(
        FamilyStudent.objects.filter(family=family).select_related('student')
    )
    linked_ids = {fs.student_id for fs in linked_students}
    direct_students = Student.objects.filter(family=family).exclude(id__in=linked_ids)
    family_students = [
        {'student': fs.student, 'relationship': fs.relationship, 'from_direct': False}
        for fs in linked_students
    ] + [
        {'student': student, 'relationship': 'Child', 'from_direct': True}
        for student in direct_students
    ]
    insurance_records = family.insurance_records.all().order_by('-insurance_year__name')
    
    context = {
        'family': family,
        'family_students': family_students,
        'insurance_records': insurance_records,
    }
    return render(request, 'families/family_detail.html', context)


@login_required
def family_list(request):
    """List all families."""
    families = Family.objects.select_related('province', 'district', 'sector', 'cell').all()
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        families = families.filter(
            Q(head_of_family__icontains=search_query) |
            Q(family_code__icontains=search_query) |
            Q(phone_number__icontains=search_query)
        )

    payment_ability_filter = request.GET.get('payment_ability', '')
    if payment_ability_filter:
        families = families.filter(payment_ability=payment_ability_filter)

    mutuelle_support_filter = request.GET.get('mutuelle_support_status', '')
    if mutuelle_support_filter:
        families = families.filter(mutuelle_support_status=mutuelle_support_filter)
    
    # Filter by province
    province_filter = request.GET.get('province', '')
    if province_filter:
        families = families.filter(province_id=province_filter)

    # Filter by district
    district_filter = request.GET.get('district', '')
    if district_filter:
        families = families.filter(district_id=district_filter)

    families = families.distinct()

    summary = families.aggregate(
        total_families=Count('id', distinct=True),
        supported_count=Count(
            'id',
            filter=Q(mutuelle_support_status=Family.MUTUELLE_SUPPORT_STATUS_SUPPORTED),
            distinct=True,
        ),
        unable_to_pay_count=Count(
            'id',
            filter=Q(payment_ability=Family.PAYMENT_ABILITY_UNABLE),
            distinct=True,
        ),
        total_members=Sum('total_family_members'),
        district_count=Count('district', distinct=True),
    )
    
    # Pagination
    paginator = Paginator(families.order_by('-created_at'), 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'families': page_obj,
        'page_obj': page_obj,
        'search_query': search_query,
        'province_filter': province_filter,
        'district_filter': district_filter,
        'payment_ability_filter': payment_ability_filter,
        'mutuelle_support_filter': mutuelle_support_filter,
        'payment_ability_choices': Family.PAYMENT_ABILITY_CHOICES,
        'mutuelle_support_choices': Family.MUTUELLE_SUPPORT_STATUS_CHOICES,
        'provinces': Province.objects.order_by('name'),
        'districts': District.objects.order_by('name'),
        'summary': {
            'total_families': summary['total_families'] or 0,
            'supported_count': summary['supported_count'] or 0,
            'unable_to_pay_count': summary['unable_to_pay_count'] or 0,
            'total_members': summary['total_members'] or 0,
            'district_count': summary['district_count'] or 0,
        },
    }
    return render(request, 'families/family_list.html', context)
