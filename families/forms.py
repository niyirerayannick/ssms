from django import forms
from .models import Family
from core.models import Province, District, Sector, Cell, Village
from core.forms import HashidModelChoiceField
from core.utils import decode_id

class FamilyForm(forms.ModelForm):
    """Form for creating and editing family information with Rwanda location."""
    
    province = HashidModelChoiceField(queryset=Province.objects.all(), required=False)
    district = HashidModelChoiceField(queryset=District.objects.none(), required=False)
    sector = HashidModelChoiceField(queryset=Sector.objects.none(), required=False)
    cell = HashidModelChoiceField(queryset=Cell.objects.none(), required=False)
    village = HashidModelChoiceField(queryset=Village.objects.none(), required=False)
    
    class Meta:
        model = Family
        fields = [
            'head_of_family', 'national_id', 'phone_number', 'alternative_phone',
            'father_name', 'mother_name', 'is_orphan', 'guardian_name', 'guardian_phone',
            'total_family_members',
            'province', 'district', 'sector', 'cell', 'village',
            'address_description', 'notes'
        ]
        widgets = {
            'head_of_family': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent'
            }),
            'national_id': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'placeholder': 'e.g., 1234567890123456'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent'
            }),
            'alternative_phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent'
            }),
            'father_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'placeholder': "Father's full name"
            }),
            'mother_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'placeholder': "Mother's full name"
            }),
            'guardian_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'placeholder': "Guardian's full name"
            }),
            'guardian_phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'placeholder': 'Guardian phone number'
            }),
            'is_orphan': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-emerald-600 focus:ring-emerald-500 border-gray-300 rounded'
            }),
            'total_family_members': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'min': '1',
                'placeholder': 'Total number of family members',
                'type': 'number'
            }),
            'province': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'id': 'id_province'
            }),
            'district': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'id': 'id_district'
            }),
            'sector': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'id': 'id_sector'
            }),
            'cell': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'id': 'id_cell'
            }),
            'village': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'id': 'id_village'
            }),
            'address_description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'rows': 3,
                'placeholder': 'Detailed address, landmarks, or directions...'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'rows': 4,
                'placeholder': 'Additional comments or notes...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Get initial/current values from POST data or instance
        province_id = self.data.get('province') or (self.instance.province_id if self.instance.pk else None)
        district_id = self.data.get('district') or (self.instance.district_id if self.instance.pk else None)
        sector_id = self.data.get('sector') or (self.instance.sector_id if self.instance.pk else None)
        cell_id = self.data.get('cell') or (self.instance.cell_id if self.instance.pk else None)
        
        # Decode IDs if they are HashIDs
        if isinstance(province_id, str) and ':' in province_id:
            province_id = decode_id(province_id)
        if isinstance(district_id, str) and ':' in district_id:
            district_id = decode_id(district_id)
        if isinstance(sector_id, str) and ':' in sector_id:
            sector_id = decode_id(sector_id)
        if isinstance(cell_id, str) and ':' in cell_id:
            cell_id = decode_id(cell_id)
        
        # Set querysets based on selected values
        if province_id:
            self.fields['district'].queryset = District.objects.filter(province_id=province_id)
        
        if district_id:
            self.fields['sector'].queryset = Sector.objects.filter(district_id=district_id)
        
        if sector_id:
            self.fields['cell'].queryset = Cell.objects.filter(sector_id=sector_id)
        
        if cell_id:
            self.fields['village'].queryset = Village.objects.filter(cell_id=cell_id)

    def clean(self):
        cleaned_data = super().clean()
        is_orphan = cleaned_data.get('is_orphan')
        guardian_name = cleaned_data.get('guardian_name')
        guardian_phone = cleaned_data.get('guardian_phone')

        if is_orphan:
            if not guardian_name:
                self.add_error('guardian_name', 'Guardian name is required if the student is orphan.')
            if not guardian_phone:
                self.add_error('guardian_phone', 'Guardian phone is required if the student is orphan.')

        return cleaned_data
