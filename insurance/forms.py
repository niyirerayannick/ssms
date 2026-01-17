from django import forms
from .models import HealthInsurance


class InsuranceForm(forms.ModelForm):
    """Form for creating and editing health insurance."""
    
    class Meta:
        model = HealthInsurance
        fields = ['student', 'required_amount', 'amount_paid', 'coverage_status']
        widgets = {
            'student': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'required_amount': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'step': '0.01'
            }),
            'amount_paid': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'step': '0.01'
            }),
            'coverage_status': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
        }

