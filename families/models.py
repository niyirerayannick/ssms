from django.db import models
from django.utils.text import gettext_lazy as _
from django.core.validators import MinValueValidator
from core.models import Province, District, Sector, Cell, Village
import uuid


class Family(models.Model):
    """Family model with Rwanda location structure."""

    PAYMENT_ABILITY_ABLE = 'able_to_pay'
    PAYMENT_ABILITY_UNABLE = 'unable_to_pay'
    PAYMENT_ABILITY_CHOICES = [
        (PAYMENT_ABILITY_ABLE, 'Able to Pay'),
        (PAYMENT_ABILITY_UNABLE, 'Unable to Pay'),
    ]

    MUTUELLE_SUPPORT_STATUS_SUPPORTED = 'supported'
    MUTUELLE_SUPPORT_STATUS_NOT_SUPPORTED = 'not_supported'
    MUTUELLE_SUPPORT_STATUS_CHOICES = [
        (MUTUELLE_SUPPORT_STATUS_SUPPORTED, 'Supported'),
        (MUTUELLE_SUPPORT_STATUS_NOT_SUPPORTED, 'Not Supported'),
    ]
    
    # Auto-generated Family Code
    family_code = models.CharField(max_length=50, unique=True, editable=False, blank=True)
    
    # Head of Family Information
    head_of_family = models.CharField(max_length=200, help_text="Full Name")
    national_id = models.CharField(max_length=50, unique=True, help_text="National ID (e.g., ID Card Number)")
    phone_number = models.CharField(max_length=20)
    alternative_phone = models.CharField(max_length=20, blank=True, null=True)

    # Parents / Guardian Information
    father_name = models.CharField(max_length=200, blank=True, help_text="Father's full name")
    mother_name = models.CharField(max_length=200, blank=True, help_text="Mother's full name")
    is_orphan = models.BooleanField(default=False)
    guardian_name = models.CharField(max_length=200, blank=True, help_text="Guardian full name (if orphan)")
    guardian_phone = models.CharField(max_length=20, blank=True, help_text="Guardian phone number")
    
    # Rwanda Location Structure (Province → District → Sector → Cell → Village)
    province = models.ForeignKey(Province, on_delete=models.SET_NULL, null=True, related_name='families')
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True, related_name='families')
    sector = models.ForeignKey(Sector, on_delete=models.SET_NULL, null=True, blank=True, related_name='families')
    cell = models.ForeignKey(Cell, on_delete=models.SET_NULL, null=True, blank=True, related_name='families')
    village = models.ForeignKey(Village, on_delete=models.SET_NULL, null=True, blank=True, related_name='families')
    
    # Family Members
    total_family_members = models.IntegerField(
        default=1, 
        help_text="Total number of family members",
        validators=[MinValueValidator(1)]
    )
    payment_ability = models.CharField(
        max_length=20,
        choices=PAYMENT_ABILITY_CHOICES,
        default=PAYMENT_ABILITY_ABLE,
        db_index=True,
        help_text="Whether the family can pay Mutuelle de Sante by themselves.",
    )
    mutuelle_support_status = models.CharField(
        max_length=20,
        choices=MUTUELLE_SUPPORT_STATUS_CHOICES,
        default=MUTUELLE_SUPPORT_STATUS_NOT_SUPPORTED,
        db_index=True,
        help_text="Whether the organization supports this family's Mutuelle de Sante.",
    )
    
    # Additional Information
    address_description = models.TextField(blank=True, null=True, help_text="Detailed address or landmarks")
    notes = models.TextField(blank=True, help_text="Additional comments or notes")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Families'
        ordering = ['head_of_family']

    def clean(self):
        """Enforce Mutuelle support business rules."""
        from django.core.exceptions import ValidationError

        if (
            self.payment_ability == self.PAYMENT_ABILITY_ABLE
            and self.mutuelle_support_status == self.MUTUELLE_SUPPORT_STATUS_SUPPORTED
        ):
            raise ValidationError({
                'mutuelle_support_status': _(
                    'Only families marked as unable to pay are eligible for Mutuelle support.'
                )
            })

    def save(self, *args, **kwargs):
        """Auto-generate family code if not provided."""
        if not self.family_code:
            # Generate format: FAM-YYYY-XXXX
            year = self.created_at.year if self.created_at else 2024
            unique_id = str(uuid.uuid4())[:8].upper()
            self.family_code = f"FAM-{year}-{unique_id}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.family_code} - {self.head_of_family}"
    
    @property
    def location_display(self):
        """Display full location path."""
        parts = []
        if self.province:
            parts.append(self.province.name)
        if self.district:
            parts.append(self.district.name)
        if self.sector:
            parts.append(self.sector.name)
        if self.cell:
            parts.append(self.cell.name)
        if self.village:
            parts.append(self.village.name)
        return " → ".join(parts) if parts else "Not specified"
    
    @property
    def total_contribution(self):
        """Calculate total family contribution: total_members * 3000."""
        return self.total_family_members * 3000
    
    @property
    def total_students(self):
        """Get count of students in this family."""
        from students.models import Student
        linked_ids = set(self.family_students.values_list('student_id', flat=True))
        direct_ids = set(Student.objects.filter(family=self).values_list('id', flat=True))
        return len(linked_ids | direct_ids)

    @property
    def is_eligible_for_mutuelle_support(self):
        """Return whether the family can receive Mutuelle support."""
        return self.payment_ability == self.PAYMENT_ABILITY_UNABLE

    @property
    def is_mutuelle_supported(self):
        """Return whether the family is currently supported."""
        return self.mutuelle_support_status == self.MUTUELLE_SUPPORT_STATUS_SUPPORTED

    @property
    def payment_ability_badge_classes(self):
        """Badge styles for payment ability display."""
        if self.payment_ability == self.PAYMENT_ABILITY_UNABLE:
            return 'bg-amber-100 text-amber-700'
        return 'bg-emerald-100 text-emerald-700'

    @property
    def mutuelle_support_badge_classes(self):
        """Badge styles for support status display."""
        if self.mutuelle_support_status == self.MUTUELLE_SUPPORT_STATUS_SUPPORTED:
            return 'bg-blue-100 text-blue-700'
        return 'bg-slate-100 text-slate-700'
    
    @property
    def students(self):
        """Get all students in this family."""
        return self.family_students.all()


class FamilyStudent(models.Model):
    """Junction model linking Family to Student."""
    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name='family_students')
    student = models.OneToOneField(
        'students.Student', 
        on_delete=models.CASCADE, 
        related_name='family_member'
    )
    relationship = models.CharField(max_length=50, default='Child', help_text="e.g., Child, Sibling, etc.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['family', 'student']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student.full_name} in {self.family.head_of_family}'s family ({self.family.family_code})"
