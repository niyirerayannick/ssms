from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse
from django.db.models import Sum, Count, Avg, Q
from students.models import Student, StudentMark, StudentMaterial
from finance.models import SchoolFee
from insurance.models import FamilyInsurance
from core.models import AcademicYear, Partner, District
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.pdfgen import canvas
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from datetime import datetime
import io
import os
from django.conf import settings


class NumberedCanvas(canvas.Canvas):
    """Custom canvas for adding page numbers and headers/footers"""
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.grey)
        self.drawRightString(
            letter[0] - 0.5*inch,
            0.5*inch,
            f"Page {self._pageNumber} of {page_count}"
        )
        # Add footer line
        self.setStrokeColor(colors.HexColor("#047857"))
        self.setLineWidth(1)
        self.line(0.75*inch, 0.65*inch, letter[0] - 0.75*inch, 0.65*inch)


def _resolve_logo_path():
    candidates = [
        os.path.join(settings.BASE_DIR, 'static', 'image', 'logo.jpg'),
        os.path.join(settings.BASE_DIR, 'static', 'image', 'logo.png'),
    ]
    for path in candidates:
        if path and os.path.exists(path):
            return path
    return None


def create_letterhead(elements, report_title, report_subtitle=None):
    """Create professional letterhead for reports"""
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#047857'),
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.grey,
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica'
    )
    
    meta_style = ParagraphStyle(
        'MetaInfo',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.grey,
        alignment=TA_RIGHT,
        spaceAfter=6
    )
    
    logo_path = _resolve_logo_path()
    if logo_path:
        logo = Image(logo_path, width=1.1 * inch, height=1.1 * inch)
        logo.hAlign = 'CENTER'
        elements.append(logo)
        elements.append(Spacer(1, 8))
    elements.append(Paragraph("Solidact Foundation", subtitle_style))
    elements.append(Spacer(1, 6))
    
    # Report title
    elements.append(Paragraph(report_title, title_style))
    if report_subtitle:
        elements.append(Paragraph(report_subtitle, subtitle_style))
    elements.append(Spacer(1, 6))
    
    # Report metadata
    current_date = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    elements.append(Paragraph(f"Generated on: {current_date}", meta_style))
    elements.append(Spacer(1, 20))


@login_required
@permission_required('students.view_student', raise_exception=True)
def students_pdf(request):
    """Export students list as PDF."""
    students = Student.objects.select_related('school', 'program_officer').all()
    
    # Create PDF with custom canvas for page numbers
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=1*inch
    )
    elements = []
    
    # Add letterhead
    create_letterhead(
        elements,
        "Students List Report",
        f"Total Students: {students.count()}"
    )
    
    # Table data with better styling
    data = [['Full Name', 'Gender', 'Age', 'School', 'Location', 'Status']]
    for student in students:
        data.append([
            student.full_name,
            student.get_gender_display(),
            str(student.age),
            student.school.name if student.school else 'N/A',
            student.family_district_name,
            student.get_sponsorship_status_display(),
        ])
    
    # Create table with improved styling
    table = Table(data, colWidths=[1.8*inch, 0.7*inch, 0.5*inch, 1.5*inch, 1.5*inch, 1*inch])
    table.setStyle(TableStyle([
        # Header styling
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#047857')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        
        # Data rows styling
        ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 1), (2, -1), 'CENTER'),  # Gender and Age centered
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        
        # Alternating row colors
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0fdf4')]),
        
        # Grid
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#047857')),
    ]))
    
    elements.append(table)
    
    # Build PDF with custom canvas for page numbers
    doc.build(elements, canvasmaker=NumberedCanvas)
    
    buffer.seek(0)
    response = HttpResponse(buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="students_list_report.pdf"'
    return response


@login_required
@permission_required('students.view_student', raise_exception=True)
def sponsored_students_report(request):
    """Detailed report for sponsored (active) students."""
    students = (
        Student.objects.select_related('family', 'school', 'program_officer')
        .filter(sponsorship_status='active')
        .order_by('last_name', 'first_name')
    )
    total = students.count()
    boys = students.filter(gender='M').count()
    girls = students.filter(gender='F').count()
    with_disability = students.filter(has_disability=True).count()
    without_disability = students.filter(has_disability=False).count()

    context = {
        'students': students,
        'total': total,
        'boys': boys,
        'girls': girls,
        'with_disability': with_disability,
        'without_disability': without_disability,
    }
    return render(request, 'reports/sponsored_students.html', context)


@login_required
@permission_required('finance.view_schoolfee', raise_exception=True)
def fees_pdf(request):
    """Export school fees summary as PDF."""
    fees = SchoolFee.objects.select_related('student', 'student__school').all()
    
    # Calculate summary statistics
    total_required = sum(float(fee.total_fees) for fee in fees)
    total_paid = sum(float(fee.amount_paid) for fee in fees)
    total_balance = sum(float(fee.balance) for fee in fees)
    
    paid_count = fees.filter(payment_status='paid').count()
    partial_count = fees.filter(payment_status='partial').count()
    pending_count = fees.filter(payment_status='pending').count()
    
    # Create PDF with custom canvas
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=1*inch
    )
    elements = []
    
    # Add letterhead
    create_letterhead(
        elements,
        "School Fees Summary Report",
        f"Total Fee Records: {fees.count()}"
    )
    
    # Summary statistics box
    styles = getSampleStyleSheet()
    summary_style = ParagraphStyle(
        'SummaryBox',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#047857'),
        alignment=TA_CENTER
    )
    
    summary_data = [[
        Paragraph(f"<b>Paid:</b> {paid_count}", summary_style),
        Paragraph(f"<b>Partial:</b> {partial_count}", summary_style),
        Paragraph(f"<b>Pending:</b> {pending_count}", summary_style),
    ]]
    
    summary_table = Table(summary_data, colWidths=[2.4*inch, 2.4*inch, 2.4*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0fdf4')),
        ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#047857')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 20))
    
    # Table data
    data = [['Student Name', 'Term', 'School', 'Required (RWF)', 'Paid (RWF)', 'Balance (RWF)', 'Status']]
    for fee in fees:
        data.append([
            fee.student.full_name,
            f"Term {fee.term}",
            fee.student.school.name if fee.student.school else 'N/A',
            f"{fee.total_fees:,.0f}",
            f"{fee.amount_paid:,.0f}",
            f"{fee.balance:,.0f}",
            fee.get_payment_status_display(),
        ])
    
    # Add totals row
    data.append([
        'TOTAL',
        '',
        '',
        f"{total_required:,.0f}",
        f"{total_paid:,.0f}",
        f"{total_balance:,.0f}",
        ''
    ])
    
    # Create table with improved styling
    table = Table(data, colWidths=[1.5*inch, 0.6*inch, 1.2*inch, 1*inch, 1*inch, 1*inch, 0.9*inch])
    table.setStyle(TableStyle([
        # Header styling
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#047857')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        
        # Data rows styling
        ('ALIGN', (0, 1), (2, -2), 'LEFT'),  # Name, term, school left aligned
        ('ALIGN', (3, 1), (-1, -2), 'CENTER'),  # Numbers and status centered
        ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -2), 7),
        ('TOPPADDING', (0, 1), (-1, -2), 5),
        ('BOTTOMPADDING', (0, 1), (-1, -2), 5),
        
        # Totals row styling
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#d1fae5')),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#047857')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 8),
        ('ALIGN', (0, -1), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, -1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, -1), (-1, -1), 8),
        
        # Alternating row colors
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f0fdf4')]),
        
        # Grid
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#047857')),
    ]))
    
    elements.append(table)
    
    # Build PDF with custom canvas
    doc.build(elements, canvasmaker=NumberedCanvas)
    
    buffer.seek(0)
    response = HttpResponse(buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="school_fees_report.pdf"'
    return response


@login_required
@permission_required('finance.manage_fees', raise_exception=True)
def fees_excel(request):
    """Export fees summary as Excel."""
    fees = SchoolFee.objects.select_related('student').all()
    
    # Create workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Fees Summary"
    
    # Header row
    headers = ['Student Name', 'Term', 'Required Fees', 'Amount Paid', 'Balance', 'Status']
    ws.append(headers)
    
    # Style header
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")
    
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center')
    
    # Data rows
    total_required = 0
    total_paid = 0
    total_balance = 0
    
    for fee in fees:
        ws.append([
            fee.student.full_name,
            fee.term,
            float(fee.total_fees),
            float(fee.amount_paid),
            float(fee.balance),
            fee.get_payment_status_display(),
        ])
        total_required += float(fee.total_fees)
        total_paid += float(fee.amount_paid)
        total_balance += float(fee.balance)
    
    # Summary row
    ws.append([])
    ws.append(['TOTAL', '', total_required, total_paid, total_balance, ''])
    
    # Auto-adjust column widths
    for column in ws.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column_letter].width = adjusted_width
    
    # Save to response
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="fees_summary.xlsx"'
    wb.save(response)
    return response


@login_required
@permission_required('insurance.manage_insurance', raise_exception=True)
def insurance_pdf(request):
    """Export insurance coverage as PDF."""
    insurance_records = FamilyInsurance.objects.select_related('family').all()
    
    # Calculate summary statistics
    covered = insurance_records.filter(coverage_status='covered').count()
    partially_covered = insurance_records.filter(coverage_status='partially_covered').count()
    not_covered = insurance_records.filter(coverage_status='not_covered').count()
    total_required = sum(float(i.required_amount) for i in insurance_records)
    total_paid = sum(float(i.amount_paid) for i in insurance_records)
    
    # Create PDF with custom canvas
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=1*inch
    )
    elements = []
    
    # Add letterhead
    create_letterhead(
        elements,
        "Mutuelle de Santé Coverage Report",
        f"Total Families: {insurance_records.count()}"
    )
    
    # Summary statistics box
    styles = getSampleStyleSheet()
    summary_style = ParagraphStyle(
        'SummaryBox',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#047857'),
        alignment=TA_CENTER
    )
    
    summary_data = [[
        Paragraph(f"<b>Covered:</b> {covered}", summary_style),
        Paragraph(f"<b>Partially:</b> {partially_covered}", summary_style),
        Paragraph(f"<b>Not Covered:</b> {not_covered}", summary_style),
    ]]
    
    summary_table = Table(summary_data, colWidths=[2.4*inch, 2.4*inch, 2.4*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0fdf4')),
        ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#047857')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 20))
    
    # Table data
    data = [['Family Head', 'Year', 'Required (RWF)', 'Paid (RWF)', 'Balance (RWF)', 'Status']]
    for insurance in insurance_records:
        balance = float(insurance.required_amount) - float(insurance.amount_paid)
        data.append([
            insurance.family.head_of_family,
            insurance.insurance_year.name if insurance.insurance_year else '',
            f"{insurance.required_amount:,.0f}",
            f"{insurance.amount_paid:,.0f}",
            f"{balance:,.0f}",
            insurance.get_coverage_status_display(),
        ])
    
    # Add totals row
    total_balance = total_required - total_paid
    data.append([
        'TOTAL',
        '',
        f"{total_required:,.0f}",
        f"{total_paid:,.0f}",
        f"{total_balance:,.0f}",
        ''
    ])
    
    # Create table with improved styling
    table = Table(data, colWidths=[1.8*inch, 0.7*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1.1*inch])
    table.setStyle(TableStyle([
        # Header styling
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#047857')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        
        # Data rows styling
        ('ALIGN', (0, 1), (0, -2), 'LEFT'),  # Family name left aligned
        ('ALIGN', (1, 1), (-1, -2), 'CENTER'),  # Numbers and status centered
        ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -2), 8),
        ('TOPPADDING', (0, 1), (-1, -2), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -2), 6),
        
        # Totals row styling
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#d1fae5')),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#047857')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 9),
        ('ALIGN', (0, -1), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, -1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, -1), (-1, -1), 8),
        
        # Alternating row colors
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f0fdf4')]),
        
        # Grid
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#047857')),
    ]))
    
    elements.append(table)
    
    # Build PDF with custom canvas
    doc.build(elements, canvasmaker=NumberedCanvas)
    
    buffer.seek(0)
    response = HttpResponse(buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="mutuelle_coverage_report.pdf"'
    return response


@login_required
def reports_index(request):
    """Reports index page."""
    boarding_count = Student.objects.filter(boarding_status='boarding').count()
    non_boarding_count = Student.objects.filter(boarding_status='non_boarding').count()
    nursery_count = Student.objects.filter(school_level='nursery').count()
    primary_count = Student.objects.filter(school_level='primary').count()
    secondary_count = Student.objects.filter(school_level='secondary').count()
    tvet_count = Student.objects.filter(school_level='tvet').count()
    
    # Get all academic years for filter dropdown
    academic_years = AcademicYear.objects.all().order_by('-name')

    context = {
        'boarding_count': boarding_count,
        'non_boarding_count': non_boarding_count,
        'nursery_count': nursery_count,
        'primary_count': primary_count,
        'secondary_count': secondary_count,
        'tvet_count': tvet_count,
        'academic_years': academic_years,
    }
    return render(request, 'reports/index.html', context)


@login_required
@permission_required('finance.view_schoolfee', raise_exception=True)
def financial_report_pdf(request):
    """Generate comprehensive financial report PDF."""
    year_id = request.GET.get('year')
    
    # Base querysets
    fees_qs = SchoolFee.objects.all()
    insurance_qs = FamilyInsurance.objects.all()
    
    subtitle = "All Years"
    
    if year_id:
        academic_year = get_object_or_404(AcademicYear, id=year_id)
        fees_qs = fees_qs.filter(academic_year=academic_year)
        insurance_qs = insurance_qs.filter(insurance_year=academic_year)
        subtitle = f"Academic Year: {academic_year.name}"
    
    # Calculate Fees Totals
    fees_total_req = fees_qs.aggregate(Sum('total_fees'))['total_fees__sum'] or 0
    fees_total_paid = fees_qs.aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
    fees_total_bal = fees_qs.aggregate(Sum('balance'))['balance__sum'] or 0
    
    # Calculate Insurance Totals
    insurance_total_req = insurance_qs.aggregate(Sum('required_amount'))['required_amount__sum'] or 0
    insurance_total_paid = insurance_qs.aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
    # Insurance balance is calculated differently in model save, but we can sum it up or calc here
    # Since FamilyInsurance has 'balance' field:
    insurance_total_bal = insurance_qs.aggregate(Sum('balance'))['balance__sum'] or 0
    
    # Grand Totals
    grand_total_req = fees_total_req + insurance_total_req
    grand_total_paid = fees_total_paid + insurance_total_paid
    grand_total_bal = fees_total_bal + insurance_total_bal
    
    # Create PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=1*inch
    )
    elements = []
    
    # Letterhead
    create_letterhead(elements, "Comprehensive Financial Report", subtitle)
    
    styles = getSampleStyleSheet()
    h2_style = ParagraphStyle(
        'Heading2Custom',
        parent=styles['Heading2'],
        textColor=colors.HexColor('#047857'),
        spaceBefore=12,
        spaceAfter=6
    )
    
    # 1. Executive Summary Table
    elements.append(Paragraph("Executive Summary", h2_style))
    
    summary_data = [
        ['Category', 'Required Amount (RWF)', 'Paid Amount (RWF)', 'Outstanding Balance (RWF)', 'Collection Rate'],
        ['School Fees', f"{fees_total_req:,.0f}", f"{fees_total_paid:,.0f}", f"{fees_total_bal:,.0f}", 
         f"{(fees_total_paid/fees_total_req*100 if fees_total_req else 0):.1f}%"],
        ['Insurance', f"{insurance_total_req:,.0f}", f"{insurance_total_paid:,.0f}", f"{insurance_total_bal:,.0f}",
         f"{(insurance_total_paid/insurance_total_req*100 if insurance_total_req else 0):.1f}%"],
        ['TOTAL', f"{grand_total_req:,.0f}", f"{grand_total_paid:,.0f}", f"{grand_total_bal:,.0f}",
         f"{(grand_total_paid/grand_total_req*100 if grand_total_req else 0):.1f}%"]
    ]
    
    summary_table = Table(summary_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1.5*inch, 1*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#047857')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),  # Numbers right aligned
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        
        # Total Row
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#d1fae5')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#047857')),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 20))
    
    # 2. Detailed Breakdown by Term (for Fees) if available
    # Only if specific year is selected or generally useful
    if fees_qs.exists():
        elements.append(Paragraph("School Fees Breakdown by Term", h2_style))
        term_stats = []
        for term_code, term_name in SchoolFee.TERM_CHOICES:
            term_fees = fees_qs.filter(term=term_code)
            t_req = term_fees.aggregate(Sum('total_fees'))['total_fees__sum'] or 0
            t_paid = term_fees.aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
            t_bal = term_fees.aggregate(Sum('balance'))['balance__sum'] or 0
            term_stats.append([term_name, t_req, t_paid, t_bal])
            
        term_data = [['Term', 'Required', 'Paid', 'Balance']]
        for t in term_stats:
            term_data.append([
                t[0],
                f"{t[1]:,.0f}",
                f"{t[2]:,.0f}",
                f"{t[3]:,.0f}"
            ])
            
        term_table = Table(term_data, colWidths=[2*inch, 1.8*inch, 1.8*inch, 1.8*inch])
        term_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#065f46')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(term_table)
        elements.append(Spacer(1, 20))

    # 3. Insurance Status Breakdown
    if insurance_qs.exists():
        elements.append(Paragraph("Insurance Coverage Status", h2_style))
        covered = insurance_qs.filter(coverage_status='covered').count()
        partial = insurance_qs.filter(coverage_status='partially_covered').count()
        not_covered = insurance_qs.filter(coverage_status='not_covered').count()
        
        ins_data = [
            ['Status', 'Count', 'Percentage'],
            ['Covered', str(covered), f"{(covered/insurance_qs.count()*100):.1f}%"],
            ['Partially Covered', str(partial), f"{(partial/insurance_qs.count()*100):.1f}%"],
            ['Not Covered', str(not_covered), f"{(not_covered/insurance_qs.count()*100):.1f}%"],
        ]
        
        ins_table = Table(ins_data, colWidths=[3*inch, 2*inch, 2*inch])
        ins_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#065f46')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(ins_table)

    # Build PDF
    doc.build(elements, canvasmaker=NumberedCanvas)
    
    buffer.seek(0)
    response = HttpResponse(buffer.read(), content_type='application/pdf')
    filename = f"financial_report_{year_id if year_id else 'all_time'}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
@permission_required(('finance.view_schoolfee', 'insurance.view_familyinsurance', 'students.view_student'), raise_exception=True)
def analysis_dashboard(request):
    """
    Dashboard view for statistical analysis and visualizations with filters.
    """
    # Get Filter Parameters
    year_id = request.GET.get('year')
    term_val = request.GET.get('term')
    district_id = request.GET.get('district')
    partner_id = request.GET.get('partner')
    level_val = request.GET.get('level')

    # Base QuerySets
    students_qs = Student.objects.all()
    marks_qs = StudentMark.objects.all()
    materials_qs = StudentMaterial.objects.all()
    fees_qs = SchoolFee.objects.all()

    # Apply Student Filters (Level, Partner, District)
    if level_val:
        students_qs = students_qs.filter(school_level=level_val)
    if partner_id:
        students_qs = students_qs.filter(partner_id=partner_id)
    if district_id:
        students_qs = students_qs.filter(family__district_id=district_id)

    # Filter related data by filtered students
    # We apply this even if no student filters are set, to ensure consistency 
    # (though if no student filters, students_qs is all, so it's a no-op efficiently handled by DB usually)
    if level_val or partner_id or district_id:
        marks_qs = marks_qs.filter(student__in=students_qs)
        materials_qs = materials_qs.filter(student__in=students_qs)
        fees_qs = fees_qs.filter(student__in=students_qs)

    # Apply Year Filter
    if year_id:
        marks_qs = marks_qs.filter(academic_year_id=year_id)
        materials_qs = materials_qs.filter(academic_year_id=year_id)
        fees_qs = fees_qs.filter(academic_year_id=year_id)

    # Apply Term Filter
    if term_val:
        # StudentMark uses 'Term X' format
        marks_qs = marks_qs.filter(term=f"Term {term_val}")
        # SchoolFee uses 'X' format
        fees_qs = fees_qs.filter(term=term_val)
        # StudentMaterial is annual, so term filter doesn't apply directly

    # Student Analysis
    total_students = students_qs.count()
    
    # Gender Distribution
    gender_map = dict(Student.GENDER_CHOICES)
    gender_data = students_qs.values('gender').annotate(count=Count('id'))
    gender_labels = [gender_map.get(item['gender'], item['gender']) for item in gender_data]
    gender_counts = [item['count'] for item in gender_data]
    
    # School Level Distribution
    level_map = dict(Student.SCHOOL_LEVEL_CHOICES)
    level_data = students_qs.values('school_level').annotate(count=Count('id'))
    level_labels = [level_map.get(item['school_level'], item['school_level']) for item in level_data]
    level_counts = [item['count'] for item in level_data]

    # Finance Analysis
    total_fees_expected = fees_qs.aggregate(total=Sum('total_fees'))['total'] or 0
    total_fees_paid = fees_qs.aggregate(total=Sum('amount_paid'))['total'] or 0
    total_balance = fees_qs.aggregate(total=Sum('balance'))['total'] or 0
    
    # Payment Status Distribution
    status_map = dict(SchoolFee.PAYMENT_STATUS_CHOICES)
    payment_status_data = fees_qs.values('payment_status').annotate(count=Count('id'))
    status_labels = [status_map.get(item['payment_status'], item['payment_status']) for item in payment_status_data]
    status_counts = [item['count'] for item in payment_status_data]

    # Performance Analysis
    avg_marks = marks_qs.aggregate(avg=Avg('marks'))['avg'] or 0
    total_marks_count = marks_qs.count()
    passed_count = marks_qs.filter(marks__gte=50).count()
    pass_rate = (passed_count / total_marks_count * 100) if total_marks_count > 0 else 0

    # Materials Analysis
    # If term filter is active, materials might show annual data still, which is fine, 
    # or we could clear it. For now, we show annual data filtered by year/student.
    total_materials_records = materials_qs.count()
    
    materials_stats = {
        'books': materials_qs.filter(books_received=True).count(),
        'bags': materials_qs.filter(bag_received=True).count(),
        'shoes': materials_qs.filter(shoes_received=True).count(),
        'uniforms': materials_qs.filter(uniforms_received=True).count(),
    }
    materials_labels = ['Books', 'Bags', 'Shoes', 'Uniforms']
    materials_counts = [materials_stats['books'], materials_stats['bags'], materials_stats['shoes'], materials_stats['uniforms']]

    # Partner Analysis
    partner_data = students_qs.values('partner__name').annotate(count=Count('id')).order_by('-count')
    partner_labels = [item['partner__name'] or 'No Partner' for item in partner_data]
    partner_counts = [item['count'] for item in partner_data]

    # Context for Filters
    academic_years = AcademicYear.objects.all().order_by('-name')
    districts = District.objects.all().order_by('name')
    partners = Partner.objects.all().order_by('name')
    school_levels = Student.SCHOOL_LEVEL_CHOICES
    terms = [('1', 'Term 1'), ('2', 'Term 2'), ('3', 'Term 3')]

    context = {
        'page_title': 'Analysis Dashboard',
        'total_students': total_students,
        'gender_labels': gender_labels,
        'gender_counts': gender_counts,
        'level_labels': level_labels,
        'level_counts': level_counts,
        'total_fees_expected': float(total_fees_expected),
        'total_fees_paid': float(total_fees_paid),
        'total_balance': float(total_balance),
        'status_labels': status_labels,
        'status_counts': status_counts,
        # New Stats
        'avg_marks': round(float(avg_marks), 1),
        'pass_rate': round(float(pass_rate), 1),
        'materials_labels': materials_labels,
        'materials_counts': materials_counts,
        'partner_labels': partner_labels,
        'partner_counts': partner_counts,
        # Filters
        'academic_years': academic_years,
        'districts': districts,
        'partners': partners,
        'school_levels': school_levels,
        'terms': terms,
        'selected_year': int(year_id) if year_id else None,
        'selected_term': term_val,
        'selected_district': int(district_id) if district_id else None,
        'selected_partner': int(partner_id) if partner_id else None,
        'selected_level': level_val,
    }
    return render(request, 'reports/analysis.html', context)

