from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from students.models import Student
from finance.models import SchoolFees
from insurance.models import FamilyInsurance
from families.models import Family, FamilyStudent
from django.db.models import Count, Q


@login_required
def index(request):
    """Dashboard home with statistics and charts."""
    
    # Total students
    total_students = Student.objects.count()
    
    # Gender distribution
    boys = Student.objects.filter(gender='M').count()
    girls = Student.objects.filter(gender='F').count()
    
    # Fees statistics
    total_fees = SchoolFees.objects.count()
    paid_fees = SchoolFees.objects.filter(status='paid').count()
    unpaid_fees = SchoolFees.objects.filter(status__in=['pending', 'overdue']).count()
    
    # Insurance statistics - based on Family Insurance
    # Students covered = students whose family has insurance status = 'covered'
    families_covered = FamilyInsurance.objects.filter(coverage_status='covered').values_list('family_id', flat=True)
    students_covered = FamilyStudent.objects.filter(family_id__in=families_covered).count()
    
    families_not_covered = FamilyInsurance.objects.exclude(coverage_status='covered').values_list('family_id', flat=True)
    students_not_covered = FamilyStudent.objects.filter(family_id__in=families_not_covered).count()
    
    # If student has no family insurance record, count as not covered
    students_without_family = Student.objects.filter(family_member__isnull=True).count()
    students_not_covered += students_without_family
    
    # Sponsorship status distribution
    active_students = Student.objects.filter(sponsorship_status='active').count()
    pending_students = Student.objects.filter(sponsorship_status='pending').count()
    graduated_students = Student.objects.filter(sponsorship_status='graduated').count()
    
    context = {
        'total_students': total_students,
        'boys': boys,
        'girls': girls,
        'total_fees': total_fees,
        'paid_fees': paid_fees,
        'unpaid_fees': unpaid_fees,
        'total_insurance': students_covered + students_not_covered,
        'covered_insurance': students_covered,
        'not_covered_insurance': students_not_covered,
        'active_students': active_students,
        'pending_students': pending_students,
        'graduated_students': graduated_students,
    }
    
    return render(request, 'dashboard/index.html', context)
