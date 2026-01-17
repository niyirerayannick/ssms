from django.shortcuts import render
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse
from django.db.models import Sum
from students.models import Student
from finance.models import SchoolFee
from insurance.models import HealthInsurance
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
import io


@login_required
@permission_required('students.view_student', raise_exception=True)
def students_pdf(request):
    """Export students list as PDF."""
    students = Student.objects.select_related('school', 'program_officer').all()
    
    # Create PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title = Paragraph("Students List - SIMS", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 12))
    
    # Table data
    data = [['Name', 'Gender', 'Age', 'School', 'District', 'Status']]
    for student in students:
        data.append([
            student.full_name,
            student.get_gender_display(),
            str(student.age),
            student.school.name if student.school else 'N/A',
            student.district,
            student.get_sponsorship_status_display(),
        ])
    
    # Create table
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    elements.append(table)
    doc.build(elements)
    
    buffer.seek(0)
    response = HttpResponse(buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="students_list.pdf"'
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
            float(fee.required_fees),
            float(fee.amount_paid),
            float(fee.balance),
            fee.get_status_display(),
        ])
        total_required += float(fee.required_fees)
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
    insurance_records = HealthInsurance.objects.select_related('student').all()
    
    # Create PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title = Paragraph("Insurance Coverage Report - SIMS", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 12))
    
    # Summary
    covered = insurance_records.filter(coverage_status='covered').count()
    not_covered = insurance_records.filter(coverage_status='not covered').count()
    summary = Paragraph(
        f"Covered: {covered} | Not Covered: {not_covered} | Total: {insurance_records.count()}",
        styles['Normal']
    )
    elements.append(summary)
    elements.append(Spacer(1, 12))
    
    # Table data
    data = [['Student Name', 'Required Amount', 'Amount Paid', 'Coverage Status']]
    for insurance in insurance_records:
        data.append([
            insurance.student.full_name,
            f"${insurance.required_amount:.2f}",
            f"${insurance.amount_paid:.2f}",
            insurance.get_coverage_status_display(),
        ])
    
    # Create table
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    elements.append(table)
    doc.build(elements)
    
    buffer.seek(0)
    response = HttpResponse(buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="insurance_coverage.pdf"'
    return response


@login_required
def reports_index(request):
    """Reports index page."""
    return render(request, 'reports/index.html')

