from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from core.models import School
from families.models import Family


class Student(models.Model):
    """Student model with connection to Family."""
    
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]
    
    ENROLLMENT_STATUS_CHOICES = [
        ('enrolled', 'Enrolled'),
        ('transferred', 'Transferred'),
        ('graduated', 'Graduated'),
        ('dropped_out', 'Dropped Out'),
    ]

    SPONSORSHIP_STATUS_CHOICES = [
        ('active', 'Active'),
        ('pending', 'Pending'),
        ('graduated', 'Graduated'),
    ]
    
    DISABILITY_CHOICES = [
        ('visual', 'Visual Impairment (Blind/Low Vision)'),
        ('hearing', 'Hearing Impairment (Deaf/Hard of Hearing)'),
        ('mobility', 'Mobility Impairment (Physical Disability)'),
        ('intellectual', 'Intellectual Disability'),
        ('autism', 'Autism Spectrum Disorder'),
        ('speech', 'Speech or Language Impairment'),
        ('learning', 'Specific Learning Disability'),
        ('emotional', 'Emotional or Behavioral Disability'),
        ('other', 'Other Disability'),
    ]
    
    # Family Connection
    family = models.ForeignKey(
        Family, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='students'
    )
    
    # Personal Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    date_of_birth = models.DateField(help_text="YYYY-MM-DD")
    
    # School Information
    school_name = models.CharField(max_length=200, blank=True)
    school = models.ForeignKey(School, on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
    class_level = models.CharField(max_length=50)
    
    # Status
    enrollment_status = models.CharField(
        max_length=20, 
        choices=ENROLLMENT_STATUS_CHOICES, 
        default='enrolled'
    )
    sponsorship_status = models.CharField(
        max_length=20,
        choices=SPONSORSHIP_STATUS_CHOICES,
        default='pending'
    )
    is_active = models.BooleanField(default=True)
    
    # Disability Information
    has_disability = models.BooleanField(
        default=False,
        help_text="Does the student have any disability?"
    )
    disability_types = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Comma-separated list of disabilities (e.g., visual, hearing, mobility)"
    )
    disability_description = models.TextField(
        blank=True,
        null=True,
        help_text="Detailed description of the disability and any special needs"
    )
    
    # Profile Picture
    profile_picture = models.ImageField(upload_to='students/profile/', blank=True, null=True)
    
    # Program Officer
    program_officer = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='assigned_students'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def full_name(self):
        """Return full name."""
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def age(self):
        """Calculate age from date of birth."""
        from datetime import date
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return None
    
    @property
    def location_display(self):
        """Display location from family."""
        if self.family:
            return self.family.location_display
        return "Not specified"
    
    @property
    def mutuelle_status(self):
        """Get Mutuelle status from family."""
        if self.family:
            latest_insurance = self.family.insurance_records.first()
            if latest_insurance:
                return latest_insurance.coverage_status
        return None
    
    @property
    def disability_display(self):
        """Display formatted disability information."""
        if not self.has_disability:
            return "No disability reported"
        
        if not self.disability_types:
            return "Disability reported but no types specified"
        
        # Convert comma-separated codes to display names
        disability_dict = dict(self.DISABILITY_CHOICES)
        types = [t.strip() for t in self.disability_types.split(',')]
        display_names = [disability_dict.get(t, t) for t in types]
        return ", ".join(display_names)

    def __str__(self):
        return self.full_name


class StudentPhoto(models.Model):
    """Model for storing multiple photos per student."""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='students/photos/')
    captured_via_camera = models.BooleanField(default=False, help_text="Was this photo captured using device camera?")
    caption = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Photo of {self.student.full_name} ({'Camera' if self.captured_via_camera else 'Upload'})"


class StudentMark(models.Model):
    """Model for storing student academic marks/records."""
    
    TERM_CHOICES = [
        ('Term 1', 'Term 1'),
        ('Term 2', 'Term 2'),
        ('Term 3', 'Term 3'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='academic_records')
    subject = models.CharField(max_length=100)
    term = models.CharField(max_length=20, choices=TERM_CHOICES)
    academic_year = models.CharField(max_length=20, default='2024')
    marks = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Marks out of 100"
    )
    teacher_remark = models.TextField(blank=True, help_text="Teacher's comments or remarks")
    report_card_image = models.ImageField(upload_to='students/reports/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-academic_year', 'term', 'subject']
        unique_together = ['student', 'subject', 'term', 'academic_year']

    def __str__(self):
        return f"{self.student.full_name} - {self.subject} - {self.term} ({self.academic_year}) - {self.marks}%"
