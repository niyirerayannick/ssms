from django import forms
from django.utils import timezone
from .models import SchoolFee, SchoolFeePayment
from insurance.models import FamilyInsurance
from core.models import School, AcademicYear, Partner
from core.academic_years import apply_default_academic_year_field


class FeeForm(forms.ModelForm):
    """Form for creating and editing school fee plans."""
    academic_year = forms.ModelChoiceField(
        queryset=AcademicYear.objects.none(),
        required=True,
        empty_label="Select academic year",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent'
        })
    )
    
    # Override school_name as a ChoiceField
    school_name = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent'
        })
    )
    
    class Meta:
        model = SchoolFee
        fields = [
            'student', 'academic_year', 'term', 'school_name', 'class_level',
            'bank_name', 'bank_account_name', 'bank_account_number',
            'total_fees', 'comments'
        ]
        widgets = {
            'student': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent'
            }),
            'term': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent'
            }),
            'class_level': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent'
            }),
            'total_fees': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'step': '0.01'
            }),
            'bank_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'placeholder': 'e.g. Bank of Kigali'
            }),
            'bank_account_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'placeholder': 'Account holder name'
            }),
            'bank_account_number': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'placeholder': 'Account number'
            }),
            'comments': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'rows': 3
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Populate school choices from the School model
        schools = School.objects.all().order_by('name')
        school_choices = [('', '--- Select School ---')] + [(school.name, school.name) for school in schools]
        self.fields['school_name'].choices = school_choices

        apply_default_academic_year_field(self, 'academic_year')
        
        # If editing and instance has a student with a school, pre-select it
        if self.instance and self.instance.pk:  # Check if it's an existing instance
            try:
                if self.instance.student and self.instance.student.school:
                    self.fields['school_name'].initial = self.instance.student.school.name
            except:
                pass  # Instance doesn't have a student yet (new record)

    def clean(self):
        cleaned_data = super().clean()
        student = cleaned_data.get('student')
        academic_year = cleaned_data.get('academic_year')
        term = cleaned_data.get('term')

        if student and academic_year and term:
            qs = SchoolFee.objects.filter(
                student=student,
                academic_year=academic_year,
                term=term,
            )
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)

            if qs.exists():
                term_label = dict(SchoolFee.TERM_CHOICES).get(term, term)
                raise forms.ValidationError(
                    f"{student.full_name} already has a fee record for {academic_year.name} - {term_label}."
                )

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if instance.student_id:
            school = instance.student.school
            if not instance.school_name:
                instance.school_name = school.name if school else instance.student.school_name
            if not instance.class_level:
                instance.class_level = instance.student.class_level
            if school:
                if not instance.bank_name:
                    instance.bank_name = school.bank_name or ''
                if not instance.bank_account_name:
                    instance.bank_account_name = school.bank_account_name or ''
                if not instance.bank_account_number:
                    instance.bank_account_number = school.bank_account_number or ''
        if commit:
            instance.save()
        return instance


class BulkFeeFilterForm(forms.Form):
    """Filter inputs required before loading bulk fee entries."""

    CATEGORY_CHOICES = [
        ('all', 'All Students'),
        ('primary', 'Primary Students'),
        ('secondary', 'Secondary Students'),
    ]

    academic_year = forms.ModelChoiceField(
        queryset=AcademicYear.objects.none(),
        required=True,
        empty_label="Select academic year",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent'
        })
    )
    school = forms.ModelChoiceField(
        queryset=School.objects.none(),
        required=False,
        empty_label="Select school",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent'
        })
    )
    partner = forms.ModelChoiceField(
        queryset=Partner.objects.none(),
        required=False,
        empty_label="Select partner (optional)",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent'
        })
    )
    term = forms.ChoiceField(
        choices=SchoolFee.TERM_CHOICES,
        required=True,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent'
        })
    )
    category = forms.ChoiceField(
        choices=CATEGORY_CHOICES,
        required=True,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent'
        })
    )
    payment_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        schools = School.objects.order_by('name')
        self.fields['school'].queryset = schools
        self.fields['partner'].queryset = Partner.objects.order_by('name')
        apply_default_academic_year_field(self, 'academic_year')

        if not self.data:
            self.fields['payment_date'].initial = timezone.now().date()

    def clean(self):
        cleaned = super().clean()
        partner = cleaned.get('partner')
        school = cleaned.get('school')
        if not partner and not school:
            raise forms.ValidationError('Select a school or choose a partner.')
        return cleaned


class BulkStudentFeeForm(forms.Form):
    """Single row within the bulk fee entry table."""

    student_id = forms.IntegerField(widget=forms.HiddenInput())
    total_fees = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm',
            'step': '0.01'
        })
    )
    amount_paid = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent text-sm',
            'step': '0.01'
        })
    )


class SchoolFeePaymentForm(forms.ModelForm):
    """Record an actual payment against a school fee plan."""

    academic_year = forms.ModelChoiceField(
        queryset=AcademicYear.objects.none(),
        required=True,
        empty_label="Select academic year",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent'
        })
    )
    term = forms.ChoiceField(
        choices=SchoolFee.TERM_CHOICES,
        required=True,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent'
        })
    )
    total_fees = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0,
        required=True,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent',
            'step': '0.01'
        })
    )

    class Meta:
        model = SchoolFeePayment
        fields = ['amount_paid', 'payment_date', 'payment_method', 'reference_number', 'notes']
        widgets = {
            'amount_paid': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent',
                'step': '0.01'
            }),
            'payment_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent'
            }),
            'payment_method': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent'
            }),
            'reference_number': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent',
                'placeholder': 'Bank slip or transaction reference'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent',
                'rows': 3
            }),
        }

    def __init__(self, *args, student=None, **kwargs):
        self.student = student
        super().__init__(*args, **kwargs)
        apply_default_academic_year_field(self, 'academic_year')
        if not self.initial.get('payment_date'):
            self.fields['payment_date'].initial = timezone.now().date()
        if student:
            self.fields['total_fees'].initial = student.school.fee_amount if student.school else 0
            self.fields['term'].initial = SchoolFee.TERM_CHOICES[0][0]

    def clean(self):
        cleaned_data = super().clean()
        amount_paid = cleaned_data.get('amount_paid')
        total_fees = cleaned_data.get('total_fees')
        if amount_paid is not None and total_fees is not None and amount_paid > total_fees and total_fees >= 0:
            self.add_error('amount_paid', 'Amount paid cannot be greater than the required amount for this term.')
        return cleaned_data


class FamilyInsuranceForm(forms.ModelForm):
    """Form for creating and editing family Mutuelle de Santé payments."""
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
