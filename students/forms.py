from django import forms
from .models import Student, StudentPhoto, StudentMark
from core.models import School
from families.models import Family
from django.contrib.auth.models import User


class StudentForm(forms.ModelForm):
    """Form for creating and editing students."""

    has_disability = forms.TypedChoiceField(
        choices=[('false', 'No'), ('true', 'Yes')],
        coerce=lambda value: value == 'true',
        empty_value=False,
        required=True,
        label='Does student have any disability?',
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
            'school', 'school_name', 'class_level', 'enrollment_status', 'sponsorship_status',
            'has_disability', 'disability_types', 'disability_description',
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
            'enrollment_status': 'Enrollment Status',
            'sponsorship_status': 'Sponsorship Status',
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
            'enrollment_status': 'Current enrollment status of the student',
            'sponsorship_status': 'Current sponsorship status',
            'has_disability': 'Check if student has any disability',
            'disability_types': 'Select one or more disability types',
            'disability_description': 'Describe the disability and any special accommodations needed',
            'is_active': 'Check if student is currently active',
        }
        widgets = {
            'family': forms.Select(attrs={
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
            'enrollment_status': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent'
            }),
            'sponsorship_status': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent'
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
            'academic_year': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'placeholder': 'e.g., 2024'
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
