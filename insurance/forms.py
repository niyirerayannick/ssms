from django import forms
from .models import FamilyInsurance
from core.models import AcademicYear
from core.academic_years import apply_default_academic_year_field


class InsuranceForm(forms.ModelForm):
    """Form for creating and editing health insurance."""
    insurance_year = forms.ModelChoiceField(
        queryset=AcademicYear.objects.none(),
        required=True,
        empty_label="Select academic year",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent'
        })
    )
    
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_default_academic_year_field(self, 'insurance_year')

