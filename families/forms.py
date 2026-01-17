from django import forms
from .models import Family
from core.models import Province, District, Sector, Cell, Village


class FamilyForm(forms.ModelForm):
    """Form for creating and editing family information with Rwanda location."""
    
    class Meta:
        model = Family
        fields = [
            'head_of_family', 'phone_number', 'alternative_phone',
            'province', 'district', 'sector', 'cell', 'village',
            'address_description', 'notes'
        ]
        widgets = {
            'head_of_family': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'alternative_phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'province': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'id': 'id_province'
            }),
            'district': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'id': 'id_district'
            }),
            'sector': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'id': 'id_sector'
            }),
            'cell': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'id': 'id_cell'
            }),
            'village': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'id': 'id_village'
            }),
            'address_description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'rows': 3,
                'placeholder': 'Detailed address, landmarks, or directions...'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'rows': 4,
                'placeholder': 'Additional comments or notes...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize dependent dropdowns as empty
        self.fields['district'].queryset = District.objects.none()
        self.fields['sector'].queryset = Sector.objects.none()
        self.fields['cell'].queryset = Cell.objects.none()
        self.fields['village'].queryset = Village.objects.none()
        
        # If editing existing instance, populate dependent fields
        if self.instance and self.instance.pk:
            if self.instance.province:
                self.fields['district'].queryset = District.objects.filter(province=self.instance.province)
            if self.instance.district:
                self.fields['sector'].queryset = Sector.objects.filter(district=self.instance.district)
            if self.instance.sector:
                self.fields['cell'].queryset = Cell.objects.filter(sector=self.instance.sector)
            if self.instance.cell:
                self.fields['village'].queryset = Village.objects.filter(cell=self.instance.cell)
