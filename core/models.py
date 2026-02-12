from django.db import models
from django.contrib.auth.models import User


class Province(models.Model):
    """Rwanda Province model."""
    name = models.CharField(max_length=200, unique=True)
    code = models.CharField(max_length=10, unique=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class District(models.Model):
    """Rwanda District model."""
    name = models.CharField(max_length=200)
    province = models.ForeignKey(Province, on_delete=models.CASCADE, related_name='districts', null=True, blank=True)
    code = models.CharField(max_length=10, unique=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        unique_together = ['name', 'province']

    def __str__(self):
        return f"{self.name} - {self.province.name}"


class Sector(models.Model):
    """Rwanda Sector model."""
    name = models.CharField(max_length=200)
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name='sectors')
    code = models.CharField(max_length=10, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        unique_together = ['name', 'district']

    def __str__(self):
        return f"{self.name} - {self.district.name}"


class Cell(models.Model):
    """Rwanda Cell model."""
    name = models.CharField(max_length=200)
    sector = models.ForeignKey(Sector, on_delete=models.CASCADE, related_name='cells')
    code = models.CharField(max_length=10, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        unique_together = ['name', 'sector']

    def __str__(self):
        return f"{self.name} - {self.sector.name}"


class Village(models.Model):
    """Rwanda Village model."""
    name = models.CharField(max_length=200)
    cell = models.ForeignKey(Cell, on_delete=models.CASCADE, related_name='villages')
    code = models.CharField(max_length=10, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        unique_together = ['name', 'cell']

    def __str__(self):
        return f"{self.name} - {self.cell.name}"


class AcademicYear(models.Model):
    """Academic year options (admin-managed)."""
    name = models.CharField(max_length=20, unique=True)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-name']

    def __str__(self):
        return self.name


class School(models.Model):
    """School model for storing school information."""
    name = models.CharField(max_length=200)
    province = models.ForeignKey(Province, on_delete=models.SET_NULL, null=True, blank=True, related_name='schools')
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True, related_name='schools')
    sector = models.ForeignKey(Sector, on_delete=models.SET_NULL, null=True, blank=True, related_name='schools')
    
    # Headteacher Information
    headteacher_name = models.CharField(max_length=200, blank=True, null=True, help_text="Full name of school headteacher")
    headteacher_mobile = models.CharField(max_length=20, blank=True, null=True, help_text="Mobile phone number")
    headteacher_email = models.EmailField(blank=True, null=True, help_text="Email address")
    
    # Bank Account Information
    bank_name = models.CharField(max_length=200, blank=True, null=True, help_text="Name of the bank")
    bank_account_name = models.CharField(max_length=200, blank=True, null=True, help_text="Account holder name")
    bank_account_number = models.CharField(max_length=50, blank=True, null=True, help_text="Bank account number")
    
    # Fee Information
    fee_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Standard fee amount per student")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.district.name if self.district else 'N/A'}"


class Partner(models.Model):
    """Partner model for student sourcing organizations."""
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    contact_person = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    
    # Rwanda Location Structure
    province = models.ForeignKey('core.Province', on_delete=models.SET_NULL, null=True, blank=True, related_name='partners')
    district = models.ForeignKey('core.District', on_delete=models.SET_NULL, null=True, blank=True, related_name='partners')
    sector = models.ForeignKey('core.Sector', on_delete=models.SET_NULL, null=True, blank=True, related_name='partners')
    cell = models.ForeignKey('core.Cell', on_delete=models.SET_NULL, null=True, blank=True, related_name='partners')
    village = models.ForeignKey('core.Village', on_delete=models.SET_NULL, null=True, blank=True, related_name='partners')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

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


class Notification(models.Model):
    """Persistent notifications for users."""

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_notifications'
    )
    verb = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    link = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.recipient.username} - {self.verb}"
