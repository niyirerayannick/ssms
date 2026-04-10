from dataclasses import dataclass
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q

from core.utils import normalize_identifier_value
from students.models import Student, StudentEnrollmentHistory, sync_student_enrollment_history

from .models import SchoolFee, SchoolFeeDisbursement, SchoolFeePayment


@dataclass(frozen=True)
class SchoolFeeScope:
    academic_year: object
    term: str
    district: object = None
    partner: object = None
    school: object = None
    category: str = 'all'


def get_or_create_fee_enrollment(student, academic_year):
    history = (
        StudentEnrollmentHistory.objects.select_related('school', 'academic_year', 'student')
        .filter(student=student, academic_year=academic_year)
        .first()
    )
    if history:
        return history
    return sync_student_enrollment_history(student, academic_year, overwrite=False)


def build_fee_snapshot_from_enrollment(enrollment_history, total_fees=None):
    school = enrollment_history.school if enrollment_history else None
    snapshot = {
        'enrollment_history': enrollment_history,
        'academic_year': enrollment_history.academic_year if enrollment_history else None,
        'school': school,
        'school_name': enrollment_history.display_school_name if enrollment_history else '',
        'class_level': enrollment_history.class_level if enrollment_history else '',
        'school_level': enrollment_history.school_level if enrollment_history else '',
        'bank_name': school.bank_name if school and school.bank_name else '',
        'bank_account_name': school.bank_account_name if school and school.bank_account_name else '',
        'bank_account_number': normalize_identifier_value(
            school.bank_account_number if school and school.bank_account_number else ''
        ).replace(' ', ''),
    }
    if total_fees is not None:
        snapshot['total_fees'] = total_fees
    return snapshot


def assign_fee_from_enrollment(fee, enrollment_history, *, total_fees=None, overwrite=True):
    snapshot = build_fee_snapshot_from_enrollment(enrollment_history, total_fees=total_fees)
    for field_name, value in snapshot.items():
        if overwrite or not getattr(fee, field_name):
            setattr(fee, field_name, value)
    fee.student = enrollment_history.student
    fee.academic_year = enrollment_history.academic_year
    return fee


def get_fee_queryset_with_context():
    return (
        SchoolFee.objects.select_related(
            'student',
            'student__family__district',
            'student__partner__district',
            'academic_year',
            'school',
            'enrollment_history',
            'enrollment_history__school',
        )
        .prefetch_related('payments')
    )


def filter_school_fee_queryset(queryset, *, params):
    search_query = (params.get('search') or '').strip()
    if search_query:
        queryset = queryset.filter(
            Q(student__first_name__icontains=search_query) |
            Q(student__last_name__icontains=search_query) |
            Q(school_name__icontains=search_query) |
            Q(class_level__icontains=search_query)
        )

    status_filter = (params.get('status') or '').strip()
    if status_filter:
        queryset = queryset.filter(payment_status=status_filter)

    academic_year_filter = (params.get('academic_year') or '').strip()
    if academic_year_filter:
        queryset = queryset.filter(academic_year_id=academic_year_filter)

    term_filter = (params.get('term') or '').strip()
    if term_filter:
        queryset = queryset.filter(term=term_filter)

    district_filter = (params.get('district') or '').strip()
    if district_filter:
        queryset = queryset.filter(
            Q(student__family__district_id=district_filter) |
            Q(student__partner__district_id=district_filter) |
            Q(school__district_id=district_filter)
        )

    school_filter = (params.get('school') or '').strip()
    if school_filter:
        queryset = queryset.filter(school_id=school_filter)

    return queryset.distinct(), {
        'search_query': search_query,
        'status_filter': status_filter,
        'academic_year_filter': academic_year_filter,
        'term_filter': term_filter,
        'district_filter': district_filter,
        'school_filter': school_filter,
    }


def get_bulk_enrollment_queryset(scope: SchoolFeeScope):
    queryset = (
        StudentEnrollmentHistory.objects.filter(
            academic_year=scope.academic_year,
            student__is_active=True,
        )
        .select_related(
            'student',
            'student__family__district',
            'student__partner__district',
            'school',
            'academic_year',
        )
    )

    if scope.partner:
        queryset = queryset.filter(student__partner=scope.partner)
    elif scope.district:
        queryset = queryset.filter(
            Q(student__family__district=scope.district) |
            Q(student__partner__district=scope.district) |
            Q(school__district=scope.district)
        )

    if scope.school:
        queryset = queryset.filter(school=scope.school)

    if scope.category in {'primary', 'secondary'}:
        queryset = queryset.filter(school_level=scope.category)

    return queryset.order_by('student__first_name', 'student__last_name').distinct()


def get_or_create_school_fee_for_enrollment(enrollment_history, term, *, total_fees=None, actor=None):
    default_total = total_fees
    if default_total is None:
        default_total = enrollment_history.school.fee_amount if enrollment_history and enrollment_history.school else Decimal('0')

    defaults = build_fee_snapshot_from_enrollment(enrollment_history, total_fees=default_total)
    if actor is not None:
        defaults['recorded_by'] = actor

    fee, created = SchoolFee.objects.get_or_create(
        student=enrollment_history.student,
        academic_year=enrollment_history.academic_year,
        term=term,
        defaults=defaults,
    )

    updated = False
    assign_fee_from_enrollment(fee, enrollment_history, total_fees=default_total, overwrite=False)
    if actor is not None and not fee.recorded_by_id:
        fee.recorded_by = actor
        updated = True
    if total_fees is not None and fee.total_fees != total_fees:
        fee.total_fees = total_fees
        updated = True
    if updated or not created:
        fee.save()
    return fee, created


def reconcile_fee_scope(*, academic_year, term, school=None):
    queryset = get_fee_queryset_with_context().filter(
        academic_year=academic_year,
        term=term,
    )
    if school is not None:
        queryset = queryset.filter(school=school)

    refreshed_count = 0
    for fee in queryset:
        if fee.enrollment_history_id:
            assign_fee_from_enrollment(fee, fee.enrollment_history, total_fees=fee.total_fees, overwrite=True)
            fee.save()
            refreshed_count += 1
        else:
            history = get_or_create_fee_enrollment(fee.student, fee.academic_year)
            if history:
                assign_fee_from_enrollment(fee, history, total_fees=fee.total_fees, overwrite=True)
                fee.save()
                refreshed_count += 1
        fee.refresh_payment_summary()
    return refreshed_count


def reconcile_disbursement_scope(*, academic_year, term='all', school=None):
    """Reconcile fee snapshots and disbursement artifacts for an explicit scope."""
    queryset = get_fee_queryset_with_context().filter(academic_year=academic_year)
    if term != 'all':
        queryset = queryset.filter(term=term)
    if school is not None:
        queryset = queryset.filter(school=school)

    processed_count = 0
    created_count = 0
    updated_count = 0
    cancelled_count = 0

    for fee in queryset:
        processed_count += 1
        original_snapshot = {
            'school_name': fee.school_name,
            'class_level': fee.class_level,
            'school_level': fee.school_level,
            'bank_name': fee.bank_name,
            'bank_account_name': fee.bank_account_name,
            'bank_account_number': fee.bank_account_number,
            'amount_paid': fee.amount_paid,
            'balance': fee.balance,
            'payment_status': fee.payment_status,
        }

        history = fee.enrollment_history or get_or_create_fee_enrollment(fee.student, fee.academic_year)
        if history:
            assign_fee_from_enrollment(fee, history, total_fees=fee.total_fees, overwrite=True)
        fee.save()
        fee.refresh_payment_summary()

        changed_fee = any(getattr(fee, field) != value for field, value in original_snapshot.items())
        if changed_fee:
            updated_count += 1

        disbursement = getattr(fee, 'disbursement', None)
        if fee.balance > 0:
            if disbursement is None:
                disbursement = SchoolFeeDisbursement.objects.create(
                    school_fee=fee,
                    status='pending',
                )
                created_count += 1
            else:
                original_status = disbursement.status
                original_amount = disbursement.amount_to_pay
                disbursement.status = 'pending'
                disbursement.save()
                if disbursement.status != original_status or disbursement.amount_to_pay != original_amount:
                    updated_count += 1
        elif disbursement is not None and disbursement.status in {'pending', 'exported'}:
            disbursement.status = 'cancelled'
            disbursement.save(update_fields=['status', 'updated_at'])
            cancelled_count += 1

    return {
        'processed_count': processed_count,
        'created_count': created_count,
        'updated_count': updated_count,
        'cancelled_count': cancelled_count,
    }


@transaction.atomic
def record_school_fee_payment(
    *,
    fee,
    amount_paid,
    payment_date,
    payment_method,
    reference_number='',
    recorded_by=None,
    notes='',
    idempotency_key=None,
):
    if amount_paid is None or amount_paid <= 0:
        raise ValidationError({'amount_paid': 'Payment amount must be greater than zero.'})

    locked_fee = (
        SchoolFee.objects.select_for_update()
        .select_related('student', 'academic_year', 'school', 'enrollment_history')
        .get(pk=fee.pk)
    )

    if idempotency_key:
        existing = SchoolFeePayment.objects.filter(idempotency_key=idempotency_key).first()
        if existing:
            return existing, False

    remaining_balance = locked_fee.balance
    if amount_paid > remaining_balance:
        raise ValidationError({
            'amount_paid': f'Payment amount cannot exceed the remaining balance of {remaining_balance}.'
        })

    payment = SchoolFeePayment.objects.create(
        school_fee=locked_fee,
        amount_paid=amount_paid,
        payment_date=payment_date,
        payment_method=payment_method,
        reference_number=reference_number or '',
        recorded_by=recorded_by,
        notes=notes or '',
        idempotency_key=idempotency_key,
    )
    return payment, True
