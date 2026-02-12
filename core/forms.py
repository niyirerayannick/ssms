from django import forms
from .models import School, Province, District, Sector, Cell, Village, Partner
from .utils import decode_id

class HashidModelChoiceField(forms.ModelChoiceField):
    """Custom ModelChoiceField that can handle both integer IDs and HashID strings."""
    def to_python(self, value):
        if value:
            decoded = decode_id(value)
            if decoded is not None:
                value = decoded
        return super().to_python(value)

class PartnerForm(forms.ModelForm):
    """Form for creating and editing partner information with Rwanda location."""
    
    province = HashidModelChoiceField(queryset=Province.objects.all(), required=False)
    district = HashidModelChoiceField(queryset=District.objects.none(), required=False)
    sector = HashidModelChoiceField(queryset=Sector.objects.none(), required=False)
    cell = HashidModelChoiceField(queryset=Cell.objects.none(), required=False)
    village = HashidModelChoiceField(queryset=Village.objects.none(), required=False)
    
    class Meta:
        model = Partner
        fields = [
            'name', 'description', 'contact_person', 'email', 'phone',
            'province', 'district', 'sector', 'cell', 'village'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'placeholder': 'Partner Name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'rows': 3,
                'placeholder': 'Brief description...'
            }),
            'contact_person': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'placeholder': 'Full name of contact person'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'placeholder': 'contact@partner.org'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'placeholder': 'e.g., +250788000000'
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
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Initial querysets for cascading
        province_id = decode_id(self.data.get('province')) or (self.instance.province_id if self.instance.pk else None)
        district_id = decode_id(self.data.get('district')) or (self.instance.district_id if self.instance.pk else None)
        sector_id = decode_id(self.data.get('sector')) or (self.instance.sector_id if self.instance.pk else None)
        cell_id = decode_id(self.data.get('cell')) or (self.instance.cell_id if self.instance.pk else None)

        if province_id:
            self.fields['district'].queryset = District.objects.filter(province_id=province_id)
        if district_id:
            self.fields['sector'].queryset = Sector.objects.filter(district_id=district_id)
        if sector_id:
            self.fields['cell'].queryset = Cell.objects.filter(sector_id=sector_id)
        if cell_id:
            self.fields['village'].queryset = Village.objects.filter(cell_id=cell_id)

class SchoolForm(forms.ModelForm):
    """Form for creating and editing school information."""
    
    province = HashidModelChoiceField(queryset=Province.objects.all(), required=False)
    district = HashidModelChoiceField(queryset=District.objects.none(), required=False)
    sector = HashidModelChoiceField(queryset=Sector.objects.none(), required=False)
    
    class Meta:
        model = School
        fields = [
            'name', 'province', 'district', 'sector',
            'headteacher_name', 'headteacher_mobile', 'headteacher_email',
            'bank_name', 'bank_account_name', 'bank_account_number',
            'fee_amount'
        ]
        labels = {
            'name': 'School Name *',
            'province': 'Province',
            'district': 'District',
            'sector': 'Sector',
            'headteacher_name': 'Headteacher Name',
            'headteacher_mobile': 'Headteacher Mobile Number',
            'headteacher_email': 'Headteacher Email',
            'bank_name': 'Bank Name',
            'bank_account_name': 'Account Holder Name',
            'bank_account_number': 'Account Number',
            'fee_amount': 'Standard Fee Amount (RWF)',
        }
        help_texts = {
            'name': 'Full name of the school',
            'headteacher_mobile': 'Contact number for the headteacher',
            'headteacher_email': 'Email address for correspondence',
            'bank_name': 'Name of the bank where account is held',
            'bank_account_name': 'Name on the bank account',
            'bank_account_number': 'Bank account number for fee payments',
            'fee_amount': 'Amount each student must pay per term/year',
        }
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'placeholder': 'Enter school name'
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
            'headteacher_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'placeholder': 'Full name of headteacher'
            }),
            'headteacher_mobile': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'placeholder': 'e.g., +250788123456',
                'type': 'tel'
            }),
            'headteacher_email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'placeholder': 'headteacher@school.com',
                'type': 'email'
            }),
            'bank_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'placeholder': 'e.g., BK, EQUITY, KCB'
            }),
            'bank_account_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'placeholder': 'Name on bank account'
            }),
            'bank_account_number': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'placeholder': 'Bank account number'
            }),
            'fee_amount': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'type': 'number',
                'step': '100',
                'min': '0',
                'placeholder': 'Amount in RWF'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Get initial/current values from POST data or instance
        province_id = decode_id(self.data.get('province')) or (self.instance.province_id if self.instance.pk else None)
        district_id = decode_id(self.data.get('district')) or (self.instance.district_id if self.instance.pk else None)
        
        # Set querysets based on selected values
        if province_id:
            self.fields['district'].queryset = District.objects.filter(province_id=province_id)
        
        if district_id:
            self.fields['sector'].queryset = Sector.objects.filter(district_id=district_id)
