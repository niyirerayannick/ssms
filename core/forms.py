from django import forms
from .models import School, Province, District, Sector


class SchoolForm(forms.ModelForm):
    """Form for creating and editing school information."""
    
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
        
        # Allow all location fields to be optional
        self.fields['province'].required = False
        self.fields['district'].required = False
        self.fields['sector'].required = False
        
        # Get initial/current values from POST data or instance
        province_id = None
        district_id = None
        
        # If this is a bound form (form submission with data)
        if self.is_bound:
            province_id = self.data.get('province')
            district_id = self.data.get('district')
        # If this is an existing instance being edited
        elif self.instance and self.instance.pk:
            province_id = self.instance.province_id
            district_id = self.instance.district_id
        
        # Set querysets based on selected values
        if province_id:
            self.fields['district'].queryset = District.objects.filter(province_id=province_id)
        else:
            self.fields['district'].queryset = District.objects.all()
        
        if district_id:
            self.fields['sector'].queryset = Sector.objects.filter(district_id=district_id)
        else:
            self.fields['sector'].queryset = Sector.objects.all()
