from django import forms
from .models import Family
from core.models import Province, District, Sector, Cell, Village


class FamilyForm(forms.ModelForm):
    """Form for creating and editing family information with Rwanda location."""
    
    class Meta:
        model = Family
        fields = [
            'head_of_family', 'national_id', 'phone_number', 'alternative_phone',
            'total_family_members',
            'province', 'district', 'sector', 'cell', 'village',
            'address_description', 'notes'
        ]
        widgets = {
            'head_of_family': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'national_id': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'e.g., 1234567890123456'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'alternative_phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'total_family_members': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'min': '1',
                'placeholder': 'Total number of family members',
                'type': 'number'
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
        
        # Allow all location fields to be optional
        self.fields['province'].required = False
        self.fields['district'].required = False
        self.fields['sector'].required = False
        self.fields['cell'].required = False
        self.fields['village'].required = False
        
        # Get initial/current values from POST data or instance
        province_id = None
        district_id = None
        sector_id = None
        cell_id = None
        
        # If this is a bound form (form submission with data)
        if self.is_bound:
            province_id = self.data.get('province')
            district_id = self.data.get('district')
            sector_id = self.data.get('sector')
            cell_id = self.data.get('cell')
        # If this is an existing instance being edited
        elif self.instance and self.instance.pk:
            province_id = self.instance.province_id
            district_id = self.instance.district_id
            sector_id = self.instance.sector_id
            cell_id = self.instance.cell_id
        
        # Set querysets based on selected values
        if province_id:
            self.fields['district'].queryset = District.objects.filter(province_id=province_id)
        else:
            self.fields['district'].queryset = District.objects.all()
        
        if district_id:
            self.fields['sector'].queryset = Sector.objects.filter(district_id=district_id)
        else:
            self.fields['sector'].queryset = Sector.objects.all()
        
        if sector_id:
            self.fields['cell'].queryset = Cell.objects.filter(sector_id=sector_id)
        else:
            self.fields['cell'].queryset = Cell.objects.all()
        
        if cell_id:
            self.fields['village'].queryset = Village.objects.filter(cell_id=cell_id)
        else:
            self.fields['village'].queryset = Village.objects.all()
