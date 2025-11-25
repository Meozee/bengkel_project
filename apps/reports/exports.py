# apps/reports/exports.py

import io
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from django.template.loader import render_to_string
from weasyprint import HTML

def export_financial_report_to_excel(report_data):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Laporan Keuangan"

    bold_font = Font(bold=True)
    title_font = Font(bold=True, size=14)
    center_align = Alignment(horizontal='center', vertical='center')
    left_align = Alignment(horizontal='left', vertical='center')
    
    sheet.merge_cells('A1:C1')
    sheet['A1'] = "LAPORAN LABA RUGI"
    sheet['A1'].font = title_font
    sheet['A1'].alignment = center_align

    sheet.merge_cells('A2:C2')
    sheet['A2'] = f"Periode: {report_data['start_date'].strftime('%d %b %Y')} - {report_data['end_date'].strftime('%d %b %Y')}"
    sheet['A2'].alignment = center_align
    sheet['A2'].font = Font(italic=True)

    rows = [
        ("PENDAPATAN", "", True),
        ("   Total Pendapatan Transaksi", report_data['total_income'], False),
        ("", "", False),
        ("BEBAN & PENGELUARAN", "", True),
        ("   (-) Pembelian Stok (HPP)", report_data['total_purchases'], False),
        ("   (-) Biaya Operasional", report_data['total_operational'], False),
        ("   Total Pengeluaran", report_data['total_expenses'], True),
        ("", "", False),
        ("LABA BERSIH", report_data['net_profit'], True),
    ]

    current_row = 4
    for label, value, is_bold in rows:
        sheet.cell(row=current_row, column=1, value=label)
        if value != "":
            cell_b = sheet.cell(row=current_row, column=2, value=value)
            cell_b.number_format = '"Rp "#,##0.00'
        if is_bold:
            sheet.cell(row=current_row, column=1).font = bold_font
            sheet.cell(row=current_row, column=2).font = bold_font
        current_row += 1

    sheet.column_dimensions['A'].width = 40
    sheet.column_dimensions['B'].width = 25

    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return buffer

def export_inventory_report_to_pdf(items, generated_date):
    context = {'items': items, 'generated_date': generated_date}
    html_string = render_to_string('reports/inventory_report_pdf.html', context)
    html = HTML(string=html_string)
    pdf_buffer = html.write_pdf()
    return io.BytesIO(pdf_buffer)

def export_customer_report_to_excel(customers, start_date, end_date):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Laporan Pelanggan"
    bold_font = Font(bold=True)
    
    sheet['A1'] = "Laporan Pelanggan"
    sheet['A1'].font = Font(bold=True, size=14)
    sheet['A2'] = f"Periode: {start_date.strftime('%d %b %Y')} - {end_date.strftime('%d %b %Y')}"

    headers = ['Nama Pelanggan', 'No. Telepon', 'Total Kunjungan', 'Total Belanja', 'Kunjungan Terakhir']
    for col_num, header_title in enumerate(headers, 1):
        cell = sheet.cell(row=4, column=col_num, value=header_title)
        cell.font = bold_font

    for row_num, customer in enumerate(customers, 5):
        sheet.cell(row=row_num, column=1, value=customer.name)
        sheet.cell(row=row_num, column=2, value=customer.phone_number)
        sheet.cell(row=row_num, column=3, value=customer.total_visits)
        
        spending = sheet.cell(row=row_num, column=4, value=customer.total_spending)
        spending.number_format = '"Rp "#,##0'

        # PERBAIKAN TIMEZONE DISINI
        if customer.last_visit:
            # Hapus info timezone agar Excel tidak error
            naive_dt = customer.last_visit.replace(tzinfo=None)
            cell_date = sheet.cell(row=row_num, column=5, value=naive_dt)
            cell_date.number_format = 'dd-mmm-yyyy'
        else:
            sheet.cell(row=row_num, column=5, value="-")

    for i in range(1, 6):
        sheet.column_dimensions[get_column_letter(i)].width = 20

    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return buffer

def export_mechanic_report_to_excel(report_data):
    """Fungsi Baru: Export Excel Kinerja Mekanik"""
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Kinerja Mekanik"
    
    sheet['A1'] = f"Laporan Kinerja: {report_data['mechanic'].name}"
    sheet['A1'].font = Font(bold=True, size=14)
    sheet['A2'] = f"Periode: {report_data['start_date']} - {report_data['end_date']}"
    
    data = [
        ("Total Pekerjaan (Unit)", report_data['total_jobs']),
        ("Total Pendapatan (Omzet)", report_data['total_revenue']),
        ("Rata-rata Durasi", report_data['avg_duration_str']),
        ("Top Service", f"{report_data['top_service']} ({report_data['top_service_count']}x)"),
    ]
    
    row_idx = 4
    for label, val in data:
        sheet.cell(row=row_idx, column=1, value=label).font = Font(bold=True)
        sheet.cell(row=row_idx, column=2, value=val)
        if label == "Total Pendapatan (Omzet)":
             sheet.cell(row=row_idx, column=2).number_format = '"Rp "#,##0'
        row_idx += 1
        
    sheet.column_dimensions['A'].width = 25
    sheet.column_dimensions['B'].width = 30
    
    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return buffer