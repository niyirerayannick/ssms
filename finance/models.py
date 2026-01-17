from django.db import models
from students.models import Student


class SchoolFee(models.Model):
    """School fees model for tracking fee payments."""
    
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
    academic_year = models.CharField(max_length=20, default='2024')
    school_name = models.CharField(max_length=200, blank=True, help_text="School name for this fee record")
    class_level = models.CharField(max_length=50, blank=True)
    total_fees = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_dates = models.TextField(blank=True, help_text="Dates of payments (comma-separated)")
    comments = models.TextField(blank=True, help_text="Additional comments or notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'School Fees'
        ordering = ['-academic_year', '-created_at']
        permissions = [
            ('manage_fees', 'Can manage fees'),
        ]

    def save(self, *args, **kwargs):
        """Auto-calculate balance and update payment status."""
        self.balance = self.total_fees - self.amount_paid
        
        # Auto-update payment status based on balance
        if self.balance <= 0:
            self.payment_status = 'paid'
        elif self.amount_paid > 0:
            self.payment_status = 'partial'
        elif self.balance > 0:
            # You can add logic here to determine if overdue based on dates
            if self.payment_status != 'overdue':
                self.payment_status = 'pending'
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.full_name} - {self.academic_year} - {self.get_payment_status_display()}"
