from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Family, FamilyStudent
from core.models import District
from .forms import FamilyForm
from students.models import Student


@login_required
def family_create(request):
    """Create a new family."""
    if request.method == 'POST':
        form = FamilyForm(request.POST)
        if form.is_valid():
            family = form.save()
            messages.success(request, f'Family {family.family_code} created successfully!')
            return redirect('families:family_detail', pk=family.pk)
    else:
        form = FamilyForm()
    
    return render(request, 'families/family_form.html', {'form': form, 'title': 'Add New Family'})


@login_required
def family_edit(request, pk):
    """Edit family information."""
    family = get_object_or_404(Family, pk=pk)
    
    if request.method == 'POST':
        form = FamilyForm(request.POST, instance=family)
        if form.is_valid():
            form.save()
            messages.success(request, f'Family {family.family_code} updated successfully!')
            return redirect('families:family_detail', pk=family.pk)
    else:
        form = FamilyForm(instance=family)
    
    return render(request, 'families/family_form.html', {'form': form, 'family': family, 'title': 'Edit Family'})


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
    families = Family.objects.all()
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        families = families.filter(
            head_of_family__icontains=search_query
        ) | families.filter(
            family_code__icontains=search_query
        ) | families.filter(
            phone_number__icontains=search_query
        )
    
    # Filter by province
    province_filter = request.GET.get('province', '')
    if province_filter:
        families = families.filter(province_id=province_filter)

    # Filter by district
    district_filter = request.GET.get('district', '')
    if district_filter:
        families = families.filter(district_id=district_filter)
    
    context = {
        'families': families,
        'search_query': search_query,
        'province_filter': province_filter,
        'district_filter': district_filter,
        'districts': District.objects.order_by('name'),
    }
    return render(request, 'families/family_list.html', context)
