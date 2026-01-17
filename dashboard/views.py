from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from students.models import Student
from finance.models import SchoolFee
from insurance.models import FamilyInsurance
from families.models import Family, FamilyStudent
from core.models import School
from django.db.models import Count, Q, Sum
from django.utils import timezone
from datetime import timedelta


@login_required
def index(request):
    """Dashboard home with comprehensive system statistics."""
    
    # ===== STUDENT STATISTICS =====
    total_students = Student.objects.count()
    boys = Student.objects.filter(gender='M').count()
    girls = Student.objects.filter(gender='F').count()
    
    # Enrollment status distribution
    active_students = Student.objects.filter(enrollment_status='enrolled').count()
    transferred_students = Student.objects.filter(enrollment_status='transferred').count()
    graduated_students = Student.objects.filter(enrollment_status='graduated').count()
    dropped_out = Student.objects.filter(enrollment_status='dropped_out').count()
    
    # Disability statistics
    students_with_disability = Student.objects.filter(has_disability=True).count()
    students_without_disability = Student.objects.filter(has_disability=False).count()
    
    # ===== FAMILY STATISTICS =====
    total_families = Family.objects.count()
    total_family_members = Family.objects.aggregate(Sum('total_family_members'))['total_family_members__sum'] or 0
    total_family_contribution = Family.objects.count() * 3000  # Each family contributes member_count * 3000
    
    # ===== SCHOOL STATISTICS =====
    total_schools = School.objects.count()
    
    # ===== FEES STATISTICS =====
    total_fees = SchoolFee.objects.count()
    paid_fees = SchoolFee.objects.filter(payment_status='paid').count()
    unpaid_fees = SchoolFee.objects.filter(payment_status__in=['pending', 'overdue']).count()
    
    # ===== INSURANCE STATISTICS =====
    # Students covered = students whose family has insurance status = 'covered'
    families_covered = FamilyInsurance.objects.filter(coverage_status='covered').values_list('family_id', flat=True)
    students_covered = FamilyStudent.objects.filter(family_id__in=families_covered).count()
    
    families_not_covered = FamilyInsurance.objects.exclude(coverage_status='covered').values_list('family_id', flat=True)
    students_not_covered = FamilyStudent.objects.filter(family_id__in=families_not_covered).count()
    
    # If student has no family insurance record, count as not covered
    students_without_family = Student.objects.filter(family_member__isnull=True).count()
    students_not_covered += students_without_family
    
    # Family insurance statistics
    families_with_insurance = FamilyInsurance.objects.filter(coverage_status='covered').count()
    families_without_insurance = Family.objects.exclude(
        insurance_records__coverage_status='covered'
    ).distinct().count()
    
    # ===== RECENT DATA =====
    # Recent students (last 7 days)
    seven_days_ago = timezone.now() - timedelta(days=7)
    recent_students = Student.objects.filter(created_at__gte=seven_days_ago).count()
    recent_families = Family.objects.filter(created_at__gte=seven_days_ago).count()
    recent_schools = School.objects.filter(created_at__gte=seven_days_ago).count()
    
    # Total schools with students
    schools_with_students = School.objects.filter(students__isnull=False).distinct().count()
    
    # ===== FINANCIAL SUMMARY =====
    # Calculate total school fees from all schools
    total_school_fees_per_student = School.objects.aggregate(Count('fee_amount'))
    
    context = {
        # Student Stats
        'total_students': total_students,
        'boys': boys,
        'girls': girls,
        'active_students': active_students,
        'transferred_students': transferred_students,
        'graduated_students': graduated_students,
        'dropped_out': dropped_out,
        'students_with_disability': students_with_disability,
        'students_without_disability': students_without_disability,
        
        # Family Stats
        'total_families': total_families,
        'total_family_members': total_family_members,
        'total_family_contribution': total_family_contribution,
        
        # School Stats
        'total_schools': total_schools,
        'schools_with_students': schools_with_students,
        
        # Fees Stats
        'total_fees': total_fees,
        'paid_fees': paid_fees,
        'unpaid_fees': unpaid_fees,
        'unpaid_percentage': round((unpaid_fees / total_fees * 100) if total_fees > 0 else 0, 1),
        'paid_percentage': round((paid_fees / total_fees * 100) if total_fees > 0 else 0, 1),
        
        # Insurance Stats
        'total_insurance': students_covered + students_not_covered,
        'covered_insurance': students_covered,
        'not_covered_insurance': students_not_covered,
        'families_with_insurance': families_with_insurance,
        'families_without_insurance': families_without_insurance,
        
        # Recent Activity
        'recent_students': recent_students,
        'recent_families': recent_families,
        'recent_schools': recent_schools,
        'has_recent_activity': recent_students + recent_families + recent_schools > 0,
    }
    
    return render(request, 'dashboard/index.html', context)
