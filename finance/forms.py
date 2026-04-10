from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from core.academic_years import apply_default_academic_year_field
from core.models import AcademicYear, District, Partner, School
from insurance.models import FamilyInsurance
from students.models import StudentEnrollmentHistory

from .models import SchoolFee, SchoolFeePayment
from .services import get_or_create_fee_enrollment


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

    class Meta:
        model = SchoolFee
        fields = ['student', 'academic_year', 'term', 'total_fees', 'comments']
        widgets = {
            'student': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent'
            }),
            'term': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent'
            }),
            'total_fees': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'step': '0.01'
            }),
            'comments': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent',
                'rows': 3
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_default_academic_year_field(self, 'academic_year')

    def clean(self):
        cleaned_data = super().clean()
        student = cleaned_data.get('student')
        academic_year = cleaned_data.get('academic_year')
        term = cleaned_data.get('term')
        total_fees = cleaned_data.get('total_fees')

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

            history = StudentEnrollmentHistory.objects.filter(
                student=student,
                academic_year=academic_year,
            ).first()
            if not history:
                raise forms.ValidationError(
                    'This student has no enrollment history for the selected academic year.'
                )

        if total_fees is not None and total_fees < 0:
            self.add_error('total_fees', 'Total fees cannot be negative.')

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if instance.student_id and instance.academic_year_id:
            history = get_or_create_fee_enrollment(instance.student, instance.academic_year)
            if history:
                instance.enrollment_history = history
                instance.sync_from_enrollment_history(history, overwrite=True)
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
    district = forms.ModelChoiceField(
        queryset=District.objects.none(),
        required=False,
        empty_label="Select district",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent'
        })
    )
    partner = forms.ModelChoiceField(
        queryset=Partner.objects.none(),
        required=False,
        empty_label="Select partner",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent'
        })
    )
    school = forms.ModelChoiceField(
        queryset=School.objects.none(),
        required=False,
        empty_label="All schools",
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
        self.fields['district'].queryset = District.objects.order_by('name')
        self.fields['partner'].queryset = Partner.objects.order_by('name')
        self.fields['school'].queryset = School.objects.order_by('name')
        apply_default_academic_year_field(self, 'academic_year')

        if not self.data:
            self.fields['payment_date'].initial = timezone.now().date()

    def clean(self):
        cleaned = super().clean()
        district = cleaned.get('district')
        partner = cleaned.get('partner')
        school = cleaned.get('school')

        if not district and not partner and not school:
            raise forms.ValidationError('Select a district, school, or partner.')
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
            self.fields['term'].initial = SchoolFee.TERM_CHOICES[0][0]

    def clean(self):
        cleaned_data = super().clean()
        amount_paid = cleaned_data.get('amount_paid')
        total_fees = cleaned_data.get('total_fees')
        academic_year = cleaned_data.get('academic_year')
        term = cleaned_data.get('term')

        if amount_paid is not None and amount_paid <= 0:
            self.add_error('amount_paid', 'Amount paid must be greater than zero.')
        if amount_paid is not None and total_fees is not None and amount_paid > total_fees and total_fees >= 0:
            self.add_error('amount_paid', 'Amount paid cannot be greater than the required amount for this term.')

        if self.student and academic_year and term:
            history = StudentEnrollmentHistory.objects.filter(
                student=self.student,
                academic_year=academic_year,
            ).first()
            if not history:
                raise ValidationError('This student has no enrollment history for the selected academic year.')

            existing_fee = SchoolFee.objects.filter(
                student=self.student,
                academic_year=academic_year,
                term=term,
            ).first()
            if existing_fee and amount_paid is not None and amount_paid > existing_fee.balance:
                self.add_error(
                    'amount_paid',
                    f'Amount paid cannot exceed the remaining balance of {existing_fee.balance}.'
                )

        reference_number = cleaned_data.get('reference_number')
        if reference_number:
            cleaned_data['reference_number'] = reference_number.strip()
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


class SchoolFeeDisbursementMarkPaidForm(forms.Form):
    """Capture payout metadata when finance confirms payment."""

    payment_date = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-4 py-2.5 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-sm'
        })
    )
    payment_reference = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2.5 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-sm',
            'placeholder': 'Bank payment reference'
        })
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2.5 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-sm',
            'rows': 2,
            'placeholder': 'Optional finance note'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.data:
            self.fields['payment_date'].initial = timezone.now().date()


class SchoolFeeReconciliationForm(forms.Form):
    """Explicit scope for finance reconciliation."""

    TERM_SCOPE_CHOICES = [('all', 'All Terms')] + list(SchoolFee.TERM_CHOICES)

    academic_year = forms.ModelChoiceField(
        queryset=AcademicYear.objects.none(),
        required=True,
        empty_label="Select academic year",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2.5 border border-slate-200 rounded-xl focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500 text-sm'
        })
    )
    term = forms.ChoiceField(
        choices=TERM_SCOPE_CHOICES,
        required=True,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2.5 border border-slate-200 rounded-xl focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500 text-sm'
        })
    )
    school = forms.ModelChoiceField(
        queryset=School.objects.none(),
        required=False,
        empty_label="All schools",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2.5 border border-slate-200 rounded-xl focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500 text-sm'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['school'].queryset = School.objects.order_by('name')
        apply_default_academic_year_field(self, 'academic_year')
        if not self.data:
            self.fields['term'].initial = 'all'
