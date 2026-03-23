from django.db import models
from django.conf import settings
from django.utils import timezone
from django.db.models import Sum
from students.models import Student
from core.models import AcademicYear


class SchoolFee(models.Model):
    """Term fee plan and cached payment summary for a student."""
    TERM_CHOICES = [
        ('1', 'TERM 1'),
        ('2', 'TERM 2'),
        ('3', 'TERM 3'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('paid', 'Paid'),
        ('partial', 'Partial'),
        ('pending', 'Pending'),
        ('overdue', 'Overdue'),
    ]
    
    student = models.ForeignKey(
        Student, 
        on_delete=models.CASCADE, 
        related_name='fees'
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='school_fees'
    )
    term = models.CharField(max_length=1, choices=TERM_CHOICES, default='1')
    school_name = models.CharField(max_length=200, blank=True, help_text="School name for this fee record")
    class_level = models.CharField(max_length=50, blank=True)
    bank_name = models.CharField(max_length=200, blank=True, help_text="Bank name snapshot for this fee record")
    bank_account_name = models.CharField(max_length=200, blank=True, help_text="Bank account holder snapshot")
    bank_account_number = models.CharField(max_length=50, blank=True, help_text="Bank account number snapshot")
    total_fees = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_dates = models.TextField(blank=True, help_text="Dates of payments (comma-separated)")
    payment_date = models.DateField(
        default=timezone.now,
        null=True,
        blank=True,
        help_text="Date the payment was recorded"
    )
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recorded_school_fees',
        help_text="User who recorded this payment"
    )
    comments = models.TextField(blank=True, help_text="Additional comments or notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'School Fees'
        ordering = ['-academic_year__name', '-created_at']
        permissions = [
            ('manage_fees', 'Can manage fees'),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'academic_year', 'term'],
                name='unique_student_term_year_fee',
            ),
        ]

    def update_bank_snapshot(self):
        """Copy current school bank details onto the fee record."""
        school = self.student.school if self.student_id and self.student and self.student.school else None
        if school:
            self.bank_name = school.bank_name or ''
            self.bank_account_name = school.bank_account_name or ''
            self.bank_account_number = school.bank_account_number or ''

    def refresh_payment_summary(self, commit=True):
        """Refresh cached totals from recorded payment transactions."""
        total_paid = self.payments.aggregate(total=Sum('amount_paid'))['total'] or 0
        self.amount_paid = total_paid
        if not self.payment_date:
            self.payment_date = timezone.now().date()

        payment_dates = (
            self.payments.order_by('payment_date', 'created_at')
            .values_list('payment_date', flat=True)
        )
        self.payment_dates = ", ".join(date.isoformat() for date in payment_dates if date)
        self.balance = self.total_fees - self.amount_paid

        if self.balance <= 0:
            self.payment_status = 'paid'
        elif self.amount_paid > 0:
            self.payment_status = 'partial'
        elif self.balance > 0:
            if self.payment_status != 'overdue':
                self.payment_status = 'pending'

        if commit:
            self.save(update_fields=[
                'amount_paid',
                'balance',
                'payment_status',
                'payment_dates',
                'payment_date',
                'updated_at',
            ])

    def save(self, *args, **kwargs):
        """Auto-calculate balance and update payment status."""
        if self.student_id and (not self.school_name or not self.class_level):
            self.school_name = self.school_name or (self.student.school.name if self.student.school else self.student.school_name)
            self.class_level = self.class_level or self.student.class_level
        if self.student_id and (not self.bank_name or not self.bank_account_name or not self.bank_account_number):
            self.update_bank_snapshot()

        self.balance = self.total_fees - self.amount_paid
        if self.balance < 0:
            self.balance = 0
        if not self.payment_date:
            self.payment_date = timezone.now().date()

        if self.balance <= 0 and self.total_fees > 0:
            self.payment_status = 'paid'
        elif self.amount_paid > 0:
            self.payment_status = 'partial'
        elif self.balance > 0:
            if self.payment_status != 'overdue':
                self.payment_status = 'pending'

        super().save(*args, **kwargs)

    def __str__(self):
        year_display = self.academic_year.name if self.academic_year else "N/A"
        return f"{self.student.full_name} - {year_display} - {self.get_payment_status_display()}"


class SchoolFeePayment(models.Model):
    """Individual payment transaction recorded against a school fee plan."""

    PAYMENT_METHOD_CHOICES = [
        ('bank', 'Bank Transfer'),
        ('cash', 'Cash'),
        ('mobile_money', 'Mobile Money'),
        ('other', 'Other'),
    ]

    school_fee = models.ForeignKey(
        SchoolFee,
        on_delete=models.CASCADE,
        related_name='payments',
    )
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField(default=timezone.now)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='bank')
    reference_number = models.CharField(max_length=100, blank=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='school_fee_payments_recorded',
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-payment_date', '-created_at']
        verbose_name = 'School Fee Payment'
        verbose_name_plural = 'School Fee Payments'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.school_fee.refresh_payment_summary()

    def delete(self, *args, **kwargs):
        school_fee = self.school_fee
        super().delete(*args, **kwargs)
        school_fee.refresh_payment_summary()

    def __str__(self):
        return f"{self.school_fee.student.full_name} - {self.amount_paid} on {self.payment_date}"
