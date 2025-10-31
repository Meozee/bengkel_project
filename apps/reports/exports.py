import io
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
from openpyxl.utils import get_column_letter
from django.template.loader import render_to_string
from weasyprint import HTML

def export_financial_report_to_excel(report_data):
    """
    Membuat file Excel dari data laporan keuangan.
    """
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Laporan Keuangan"

    bold_font = Font(bold=True)
    center_align = Alignment(horizontal='center', vertical='center')

    sheet.merge_cells('A1:B1')
    sheet['A1'] = "Laporan Keuangan"
    sheet['A1'].font = Font(bold=True, size=16)
    sheet['A1'].alignment = center_align

    sheet.merge_cells('A2:B2')
    period = f"Periode: {report_data['start_date'].strftime('%d %b %Y')} - {report_data['end_date'].strftime('%d %b %Y')}"
    sheet['A2'] = period
    sheet['A2'].font = Font(italic=True)
    sheet['A2'].alignment = center_align

    data_rows = [
        ("PENDAPATAN", ""),
        ("Total Pendapatan", report_data['total_income']),
        ("", ""),
        ("PENGELUARAN", ""),
        ("Total Pengeluaran", report_data['total_expenses']),
        ("", ""),
        ("LABA BERSIH", report_data['net_profit']),
    ]

    for i, row_data in enumerate(data_rows, start=4):
        sheet.cell(row=i, column=1, value=row_data[0])
        sheet.cell(row=i, column=2, value=row_data[1])
        if row_data[0] in ["PENDAPATAN", "PENGELUARAN", "LABA BERSIH"]:
            sheet.cell(row=i, column=1).font = bold_font
            sheet.cell(row=i, column=2).font = bold_font
        if isinstance(row_data[1], (int, float, type(report_data['net_profit']))):
             sheet.cell(row=i, column=2).number_format = '"Rp "#,##0.00'

    sheet.column_dimensions['A'].width = 25
    sheet.column_dimensions['B'].width = 25

    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return buffer

def export_inventory_report_to_pdf(items, generated_date):
    """
    Merender template HTML ke PDF menggunakan WeasyPrint.
    """
    context = {'items': items, 'generated_date': generated_date}
    html_string = render_to_string('reports/inventory_report_pdf.html', context)
    
    html = HTML(string=html_string)
    pdf_buffer = html.write_pdf()
    
    return io.BytesIO(pdf_buffer)

def export_customer_report_to_excel(customers, start_date, end_date):
    """
    Membuat file Excel dari data laporan pelanggan.
    """
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Laporan Pelanggan"

    bold_font = Font(bold=True)
    
    sheet['A1'] = "Laporan Pelanggan"
    sheet['A1'].font = Font(bold=True, size=16)
    sheet['A2'] = f"Periode: {start_date.strftime('%d %b %Y')} - {end_date.strftime('%d %b %Y')}"
    sheet['A2'].font = Font(italic=True)

    headers = ['Nama Pelanggan', 'No. Telepon', 'Total Kunjungan', 'Total Belanja', 'Kunjungan Terakhir']
    for col_num, header_title in enumerate(headers, 1):
        cell = sheet.cell(row=4, column=col_num, value=header_title)
        cell.font = bold_font

    for row_num, customer in enumerate(customers, 5):
        sheet.cell(row=row_num, column=1, value=customer.name)
        sheet.cell(row=row_num, column=2, value=customer.phone_number)
        sheet.cell(row=row_num, column=3, value=customer.total_visits)
        
        spending_cell = sheet.cell(row=row_num, column=4, value=customer.total_spending)
        spending_cell.number_format = '"Rp "#,##0'

        last_visit_cell = sheet.cell(row=row_num, column=5, value=customer.last_visit)
        if customer.last_visit:
            last_visit_cell.number_format = 'DD-MMM-YYYY'

    for col_num in range(1, len(headers) + 1):
        column_letter = get_column_letter(col_num)
        sheet.column_dimensions[column_letter].width = 20

    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return buffer