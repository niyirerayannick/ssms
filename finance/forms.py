from django import forms
from .models import SchoolFee
from insurance.models import FamilyInsurance
from core.models import School


class FeeForm(forms.ModelForm):
    """Form for creating and editing school fees."""
    
    # Override school_name as a ChoiceField
    school_name = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
        })
    )
    
    class Meta:
        model = SchoolFee
        fields = [
            'student', 'academic_year', 'term', 'school_name', 'class_level',
            'total_fees', 'amount_paid', 'payment_status', 'payment_dates', 'comments'
        ]
        widgets = {
            'student': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'academic_year': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'e.g., 2024'
            }),
            'term': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'class_level': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'total_fees': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'step': '0.01'
            }),
            'amount_paid': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'step': '0.01'
            }),
            'payment_status': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'payment_dates': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'rows': 2,
                'placeholder': 'Dates of payments (comma-separated)'
            }),
            'comments': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'rows': 3
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Populate school choices from the School model
        schools = School.objects.all().order_by('name')
        school_choices = [('', '--- Select School ---')] + [(school.name, school.name) for school in schools]
        self.fields['school_name'].choices = school_choices
        
        # If editing and instance has a student with a school, pre-select it
        if self.instance and self.instance.pk:  # Check if it's an existing instance
            try:
                if self.instance.student and self.instance.student.school:
                    self.fields['school_name'].initial = self.instance.student.school.name
            except:
                pass  # Instance doesn't have a student yet (new record)


class FamilyInsuranceForm(forms.ModelForm):
    """Form for creating and editing family Mutuelle de Santé payments."""
    
    class Meta:
        model = FamilyInsurance
        fields = [
            'family', 'insurance_year', 'required_amount', 'amount_paid',
            'coverage_status', 'payment_dates', 'remarks'
        ]
        widgets = {
            'family': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent'
            }),
            'insurance_year': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent',
                'placeholder': 'e.g., 2024'
            }),
            'required_amount': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent',
                'step': '0.01'
            }),
            'amount_paid': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent',
                'step': '0.01'
            }),
            'coverage_status': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent'
            }),
            'payment_dates': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent',
                'rows': 2,
                'placeholder': 'Dates of payments (comma-separated)'
            }),
            'remarks': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent',
                'rows': 3,
                'placeholder': 'Additional remarks or notes'
            }),
        }
