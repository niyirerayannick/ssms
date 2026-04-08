from django import forms

from core.models import AcademicYear, District, School, Sector
from families.models import Family
from finance.models import SchoolFee
from insurance.models import FamilyInsurance
from students.models import Student

from .services import get_available_reports_for_user, get_report_definition


class SendReportForm(forms.Form):
    REPORT_FORMAT_CHOICES = [
        ("pdf", "PDF"),
        ("excel", "Excel"),
    ]

    report_key = forms.ChoiceField(
        choices=[],
        widget=forms.Select(attrs={
            "class": "w-full px-4 py-2.5 border border-slate-200 rounded-xl focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all outline-none text-sm",
        }),
    )
    export_format = forms.ChoiceField(
        choices=REPORT_FORMAT_CHOICES,
        widget=forms.Select(attrs={
            "class": "w-full px-4 py-2.5 border border-slate-200 rounded-xl focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all outline-none text-sm",
        }),
    )
    academic_year = forms.ModelChoiceField(
        queryset=AcademicYear.objects.order_by("-name"),
        required=False,
        empty_label="All Academic Years",
        widget=forms.Select(attrs={"class": "report-filter-field w-full px-4 py-2.5 border border-slate-200 rounded-xl text-sm", "data-filter-name": "academic_year"}),
    )
    district = forms.ModelChoiceField(
        queryset=District.objects.order_by("name"),
        required=False,
        empty_label="All Districts",
        widget=forms.Select(attrs={"class": "report-filter-field w-full px-4 py-2.5 border border-slate-200 rounded-xl text-sm", "data-filter-name": "district"}),
    )
    sector = forms.ModelChoiceField(
        queryset=Sector.objects.select_related("district").order_by("name"),
        required=False,
        empty_label="All Sectors",
        widget=forms.Select(attrs={"class": "report-filter-field w-full px-4 py-2.5 border border-slate-200 rounded-xl text-sm", "data-filter-name": "sector"}),
    )
    school = forms.ModelChoiceField(
        queryset=School.objects.select_related("district").order_by("name"),
        required=False,
        empty_label="All Schools",
        widget=forms.Select(attrs={"class": "report-filter-field w-full px-4 py-2.5 border border-slate-200 rounded-xl text-sm", "data-filter-name": "school"}),
    )
    gender = forms.ChoiceField(
        choices=[("", "All Genders"), *Student.GENDER_CHOICES],
        required=False,
        widget=forms.Select(attrs={"class": "report-filter-field w-full px-4 py-2.5 border border-slate-200 rounded-xl text-sm", "data-filter-name": "gender"}),
    )
    school_level = forms.ChoiceField(
        choices=[("", "All Levels"), *Student.SCHOOL_LEVEL_CHOICES],
        required=False,
        widget=forms.Select(attrs={"class": "report-filter-field w-full px-4 py-2.5 border border-slate-200 rounded-xl text-sm", "data-filter-name": "school_level"}),
    )
    sponsorship_status = forms.ChoiceField(
        choices=[("", "All Sponsorship Statuses"), *Student.SPONSORSHIP_STATUS_CHOICES],
        required=False,
        widget=forms.Select(attrs={"class": "report-filter-field w-full px-4 py-2.5 border border-slate-200 rounded-xl text-sm", "data-filter-name": "sponsorship_status"}),
    )
    enrollment_status = forms.ChoiceField(
        choices=[("", "All Academic Statuses"), *Student.ENROLLMENT_STATUS_CHOICES],
        required=False,
        widget=forms.Select(attrs={"class": "report-filter-field w-full px-4 py-2.5 border border-slate-200 rounded-xl text-sm", "data-filter-name": "enrollment_status"}),
    )
    payment_ability = forms.ChoiceField(
        choices=[("", "All Payment Abilities"), *Family.PAYMENT_ABILITY_CHOICES],
        required=False,
        widget=forms.Select(attrs={"class": "report-filter-field w-full px-4 py-2.5 border border-slate-200 rounded-xl text-sm", "data-filter-name": "payment_ability"}),
    )
    mutuelle_support_status = forms.ChoiceField(
        choices=[("", "All Mutuelle Support Statuses"), *Family.MUTUELLE_SUPPORT_STATUS_CHOICES],
        required=False,
        widget=forms.Select(attrs={"class": "report-filter-field w-full px-4 py-2.5 border border-slate-200 rounded-xl text-sm", "data-filter-name": "mutuelle_support_status"}),
    )
    payment_status = forms.ChoiceField(
        choices=[("", "All School Fees Statuses"), *SchoolFee.PAYMENT_STATUS_CHOICES],
        required=False,
        widget=forms.Select(attrs={"class": "report-filter-field w-full px-4 py-2.5 border border-slate-200 rounded-xl text-sm", "data-filter-name": "payment_status"}),
    )
    coverage_status = forms.ChoiceField(
        choices=[("", "All Coverage Statuses"), *FamilyInsurance.COVERAGE_STATUS_CHOICES],
        required=False,
        widget=forms.Select(attrs={"class": "report-filter-field w-full px-4 py-2.5 border border-slate-200 rounded-xl text-sm", "data-filter-name": "coverage_status"}),
    )
    age_from = forms.IntegerField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={"class": "report-filter-field w-full px-4 py-2.5 border border-slate-200 rounded-xl text-sm", "data-filter-name": "age_from", "placeholder": "Minimum age"}),
    )
    age_to = forms.IntegerField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={"class": "report-filter-field w-full px-4 py-2.5 border border-slate-200 rounded-xl text-sm", "data-filter-name": "age_to", "placeholder": "Maximum age"}),
    )
    recipients = forms.CharField(
        widget=forms.Textarea(attrs={
            "class": "w-full px-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all outline-none text-sm",
            "rows": 3,
            "placeholder": "name@example.com, second@example.com",
        }),
        help_text="Separate multiple email addresses with commas, semicolons, or new lines.",
    )
    subject = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "class": "w-full px-4 py-2.5 border border-slate-200 rounded-xl focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all outline-none text-sm",
            "placeholder": "Optional email subject",
        }),
    )
    message = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            "class": "w-full px-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all outline-none text-sm",
            "rows": 4,
            "placeholder": "Optional email message",
        }),
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        self.fields["report_key"].choices = [
            (report.key, report.label) for report in get_available_reports_for_user(self.user)
        ]

    def clean_recipients(self):
        raw_value = self.cleaned_data["recipients"]
        candidates = [part.strip() for chunk in raw_value.replace(";", ",").splitlines() for part in chunk.split(",")]
        emails = [email for email in candidates if email]
        if not emails:
            raise forms.ValidationError("Enter at least one recipient email address.")
        validator = forms.EmailField().clean
        validated = []
        for email in emails:
            validated.append(validator(email))
        return list(dict.fromkeys(validated))

    def clean(self):
        cleaned_data = super().clean()
        report_key = cleaned_data.get("report_key")
        if not report_key:
            return cleaned_data
        report = get_report_definition(report_key)
        if not report or not self.user.has_perm(report.permission):
            self.add_error("report_key", "You do not have permission to send this report.")
            return cleaned_data

        export_format = cleaned_data.get("export_format")
        if export_format and export_format not in report.formats:
            self.add_error("export_format", "This format is not available for the selected report.")
        return cleaned_data
