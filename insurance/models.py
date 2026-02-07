from django.db import models
from families.models import Family
from core.models import AcademicYear


class FamilyInsurance(models.Model):
    """Mutuelle de Santé model - Insurance at Family level."""
    
    COVERAGE_STATUS_CHOICES = [
        ('covered', 'Covered'),
        ('partially_covered', 'Partially Covered'),
        ('not_covered', 'Not Covered'),
    ]
    
    family = models.ForeignKey(
        Family, 
        on_delete=models.CASCADE, 
        related_name='insurance_records'
    )
    insurance_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='insurance_records'
    )
    required_amount = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    coverage_status = models.CharField(
        max_length=20, 
        choices=COVERAGE_STATUS_CHOICES, 
        default='not_covered'
    )
    payment_dates = models.TextField(blank=True, help_text="Dates of payments (comma-separated)")
    remarks = models.TextField(blank=True, help_text="Additional remarks or notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-insurance_year__name', '-created_at']
        unique_together = ['family', 'insurance_year']
        permissions = [
            ('manage_insurance', 'Can manage insurance'),
        ]

    def save(self, *args, **kwargs):
        """Auto-calculate balance and update coverage status."""
        self.balance = self.required_amount - self.amount_paid
        
        # Auto-update coverage status based on payment
        if self.amount_paid >= self.required_amount:
            self.coverage_status = 'covered'
        elif self.amount_paid > 0:
            self.coverage_status = 'partially_covered'
        else:
            self.coverage_status = 'not_covered'
        
        super().save(*args, **kwargs)

    def __str__(self):
        year_display = self.insurance_year.name if self.insurance_year else "N/A"
        return f"{self.family.family_code} - {year_display} - {self.get_coverage_status_display()}"


# Legacy model - kept for backward compatibility
class HealthInsurance(models.Model):
    """Legacy health insurance model - DEPRECATED."""
    
    COVERAGE_STATUS_CHOICES = [
        ('covered', 'Covered'),
        ('not covered', 'Not Covered'),
    ]
    
    student = models.ForeignKey(
        'students.Student', 
        on_delete=models.CASCADE, 
        related_name='legacy_insurance'
    )
    required_amount = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    coverage_status = models.CharField(
        max_length=20, 
        choices=COVERAGE_STATUS_CHOICES, 
        default='not covered'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Legacy Health Insurance"
        verbose_name_plural = "Legacy Health Insurance Records"

    def __str__(self):
        return f"{self.student.full_name} - {self.coverage_status} (LEGACY)"
