from django import forms
from .models import Student, StudentPhoto, StudentMark, StudentMaterial
from core.models import School, AcademicYear
from families.models import Family
from django.contrib.auth.models import User


class StudentForm(forms.ModelForm):
    """Form for creating and editing students."""

    SPONSORSHIP_YEAR_CHOICES = [('', 'Select year...')] + [
        (str(year), str(year)) for year in range(2020, 2031)
    ]

    has_disability = forms.TypedChoiceField(
        choices=[('false', 'No'), ('true', 'Yes')],
        coerce=lambda value: value == 'true',
        empty_value=False,
        required=True,
        label='Does student have any disability?',
    )
    sponsorship_start_year = forms.TypedChoiceField(
        choices=SPONSORSHIP_YEAR_CHOICES,
        required=False,
        coerce=lambda value: int(value) if value else None,
        empty_value=None,
        label='Sponsorship Start Year',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg bg-white/90 shadow-sm focus:ring-2 focus:ring-emerald-500 focus:border-transparent'
        })
    )
    disability_types = forms.ChoiceField(
        choices=[('', 'Select disability type...')] + list(Student.DISABILITY_CHOICES),
        required=False,
        label='Types of Disabilities',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.disability_types:
            self.fields['disability_types'].initial = self.instance.disability_types.strip()
    
    class Meta:
        model = Student
        fields = [
            'family', 'first_name', 'last_name', 'gender', 'date_of_birth',
            'school', 'school_name', 'class_level', 'school_level', 'boarding_status',
            'partner',
            'enrollment_status', 'sponsorship_status',
            'sponsorship_start_year', 'sponsorship_reason', 'has_disability', 'disability_types', 'disability_description',
            'is_active', 'profile_picture', 'program_officer'
        ]
        labels = {
            'family': 'Family *',
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'gender': 'Gender',
            'date_of_birth': 'Date of Birth',
            'school': 'School',
            'school_name': 'Or Enter School Name',
            'class_level': 'Class Level',
            'school_level': 'School Level',
            'boarding_status': 'Boarding Status',
            'partner': 'Partner Organization',
            'enrollment_status': 'Enrollment Status',
            'sponsorship_status': 'Sponsorship Status',
            'sponsorship_start_year': 'Sponsorship Start Year',
            'sponsorship_reason': 'Reason for Support',
            'has_disability': 'Does student have any disability?',
            'disability_types': 'Types of Disabilities',
            'disability_description': 'Disability Description & Special Needs',
            'is_active': 'Active Student',
            'profile_picture': 'Profile Picture',
            'program_officer': 'Assigned Program Officer',
        }
        help_texts = {
            'family': 'Select existing family or create a new one using the link below',
            'school': 'Select from existing schools or create a new one using the link below',
            'school_name': 'Alternative: if school is not in database, enter name here',
            'class_level': 'e.g., P1, P6, S1, S3',
            'school_level': 'Select the school level',
            'boarding_status': 'Select boarding or non-boarding',
            'partner': 'Select partner organization if applicable',
            'enrollment_status': 'Current enrollment status of the student',
            'sponsorship_status': 'Current sponsorship status',
            'sponsorship_start_year': 'Select the year the sponsorship started',
            'sponsorship_reason': 'Why Solidact is supporting this student',
            'has_disability': 'Check if student has any disability',
            'disability_types': 'Select one or more disability types',
            'disability_description': 'Describe the disability and any special accommodations needed',
            'is_active': 'Check if student is currently active',
        }
        widgets = {
            'family': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent'
            }),
            'partner': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'placeholder': 'Enter first name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'placeholder': 'Enter last name'
            }),
            'gender': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent'
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'type': 'date'
            }),
            'school': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent'
            }),
            'school_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'placeholder': 'Or enter school name manually'
            }),
            'class_level': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'placeholder': 'e.g., P1, P6, S1, S3'
            }),
            'school_level': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent'
            }),
            'boarding_status': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent'
            }),
            'enrollment_status': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent'
            }),
            'sponsorship_status': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent'
            }),
            'sponsorship_reason': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'rows': 3,
                'placeholder': 'Explain why Solidact should support this student...'
            }),
            'has_disability': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent'
            }),
            'disability_types': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg bg-white/90 shadow-sm focus:ring-2 focus:ring-emerald-500 focus:border-transparent'
            }),
            'disability_description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'rows': 4,
                'placeholder': 'Describe the disability and any special accommodations needed'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-emerald-600 border-gray-300 rounded focus:ring-emerald-500'
            }),
            'profile_picture': forms.FileInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'accept': 'image/*'
            }),
            'program_officer': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        has_disability = cleaned_data.get('has_disability')
        disability_types = cleaned_data.get('disability_types') or ''
        disability_description = cleaned_data.get('disability_description', '')

        if has_disability:
            if not disability_types:
                self.add_error('disability_types', 'Select a disability type.')
        else:
            cleaned_data['disability_types'] = ''
            cleaned_data['disability_description'] = ''

        return cleaned_data

    def clean_disability_types(self):
        value = self.cleaned_data.get('disability_types') or ''
        return value


class StudentPhotoForm(forms.ModelForm):
    """Form for uploading student photos."""
    
    class Meta:
        model = StudentPhoto
        fields = ['image', 'captured_via_camera', 'caption']
        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'accept': 'image/*',
                'capture': 'environment'
            }),
            'captured_via_camera': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-emerald-600 border-gray-300 rounded focus:ring-emerald-500'
            }),
            'caption': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'placeholder': 'Optional caption...'
            }),
        }


class StudentMarkForm(forms.ModelForm):
    """Form for adding academic marks."""
    academic_year = forms.ModelChoiceField(
        queryset=AcademicYear.objects.none(),
        required=True,
        empty_label="Select academic year",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent'
        })
    )
    
    class Meta:
        model = StudentMark
        fields = ['subject', 'term', 'academic_year', 'marks', 'teacher_remark', 'report_card_image']
        widgets = {
            'subject': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent'
            }),
            'term': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent'
            }),
            'marks': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'step': '0.01',
                'min': '0',
                'max': '100'
            }),
            'teacher_remark': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'rows': 3,
                'placeholder': "Teacher's comments or remarks..."
            }),
            'report_card_image': forms.FileInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'accept': 'image/*'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        years = AcademicYear.objects.order_by('-name')
        self.fields['academic_year'].queryset = years
        active_year = years.filter(is_active=True).first()
        if active_year and not self.instance.pk:
            self.fields['academic_year'].initial = active_year


class StudentMaterialForm(forms.ModelForm):
    """Form for recording school materials for sponsored students."""
    academic_year = forms.ModelChoiceField(
        queryset=AcademicYear.objects.none(),
        required=True,
        empty_label="Select academic year",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent'
        })
    )

    class Meta:
        model = StudentMaterial
        fields = [
            'student',
            'academic_year',
            'books_received',
            'bag_received',
            'shoes_received',
            'uniforms_received',
            'received_date',
            'special_request',
            'notes',
        ]
        widgets = {
            'student': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent'
            }),
            'books_received': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-emerald-600 focus:ring-emerald-500 border-gray-300 rounded'
            }),
            'bag_received': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-emerald-600 focus:ring-emerald-500 border-gray-300 rounded'
            }),
            'shoes_received': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-emerald-600 focus:ring-emerald-500 border-gray-300 rounded'
            }),
            'uniforms_received': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-emerald-600 focus:ring-emerald-500 border-gray-300 rounded'
            }),
            'received_date': forms.DateInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'type': 'date'
            }),
            'special_request': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'rows': 3,
                'placeholder': 'Special needs or requests...'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'rows': 3,
                'placeholder': 'Additional notes...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['student'].queryset = Student.objects.filter(sponsorship_status='active').order_by('first_name', 'last_name')
        years = AcademicYear.objects.order_by('-name')
        self.fields['academic_year'].queryset = years
        active_year = years.filter(is_active=True).first()
        if active_year and not self.instance.pk:
            self.fields['academic_year'].initial = active_year
