from django.shortcuts import render
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse
from django.db.models import Sum
from students.models import Student
from finance.models import SchoolFee
from insurance.models import FamilyInsurance
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
            insurance.insurance_year,
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
    return render(request, 'reports/index.html')

