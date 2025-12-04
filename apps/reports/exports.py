# apps/reports/exports.py

import io
from datetime import datetime  # <--- TAMBAHKAN INI
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from django.template.loader import render_to_string
from weasyprint import HTML

def export_financial_report_to_excel(report_data):
    """
    Membuat file Excel Laporan Keuangan (Update: Ada rincian Operasional).
    """
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Laporan Keuangan"

    # Styles
    bold_font = Font(bold=True)
    title_font = Font(bold=True, size=14)
    center_align = Alignment(horizontal='center', vertical='center')
    left_align = Alignment(horizontal='left', vertical='center')
    
    # Header Judul
    sheet.merge_cells('A1:C1')
    sheet['A1'] = "LAPORAN LABA RUGI (INCOME STATEMENT)"
    sheet['A1'].font = title_font
    sheet['A1'].alignment = center_align

    # Header Periode
    sheet.merge_cells('A2:C2')
    start = report_data['start_date'].strftime('%d %b %Y')
    end = report_data['end_date'].strftime('%d %b %Y')
    sheet['A2'] = f"Periode: {start} - {end}"
    sheet['A2'].alignment = center_align
    sheet['A2'].font = Font(italic=True)

    # Struktur Data Baris [Label, Nilai, Format(Bold/Normal)]
    rows = [
        ("PENDAPATAN (REVENUE)", "", True),
        ("   Total Pendapatan Transaksi", report_data['total_income'], False),
        ("", "", False), # Spasi kosong
        
        ("BEBAN POKOK & OPERASIONAL", "", True),
        ("   (-) Pembelian Stok (HPP)", report_data['total_purchases'], False),
        ("   (-) Biaya Operasional (Gaji/Listrik/dll)", report_data['total_operational'], False),
        ("   Total Pengeluaran", report_data['total_expenses'], True),
        ("", "", False), # Spasi kosong
        
        ("LABA BERSIH (NET PROFIT)", report_data['net_profit'], True),
    ]

    current_row = 4
    for label, value, is_bold in rows:
        # Kolom A (Label)
        cell_a = sheet.cell(row=current_row, column=1, value=label)
        cell_a.alignment = left_align
        
        # Kolom B (Nilai)
        if value != "":
            cell_b = sheet.cell(row=current_row, column=2, value=value)
            cell_b.number_format = '"Rp "#,##0.00' # Format Rupiah di Excel
        else:
            sheet.cell(row=current_row, column=2, value="")

        # Styling Bold jika diperlukan
        if is_bold:
            sheet.cell(row=current_row, column=1).font = bold_font
            sheet.cell(row=current_row, column=2).font = bold_font
            # Tambahkan border bottom tipis untuk pemisah section
            if value == "": 
                sheet.cell(row=current_row, column=1).border = Border(bottom=Side(style='thin'))
                sheet.cell(row=current_row, column=2).border = Border(bottom=Side(style='thin'))

        current_row += 1

    # Auto width columns
    sheet.column_dimensions['A'].width = 40
    sheet.column_dimensions['B'].width = 25

    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return buffer

def export_inventory_report_to_pdf(items, generated_date):
    """
    Export Inventory ke PDF (WeasyPrint).
    """
    context = {'items': items, 'generated_date': generated_date}
    
    # Render HTML string dari template
    html_string = render_to_string('reports/inventory_report_pdf.html', context)
    
    # Convert HTML to PDF
    html = HTML(string=html_string)
    pdf_buffer = html.write_pdf()
    
    return io.BytesIO(pdf_buffer)

def export_customer_report_to_excel(customers, start_date, end_date):
    """
    Export Laporan Pelanggan ke Excel (Fix Timezone Error).
    """
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Laporan Pelanggan"

    bold_font = Font(bold=True)
    
    # Header
    sheet['A1'] = "Laporan Aktivitas Pelanggan"
    sheet['A1'].font = Font(bold=True, size=14)
    sheet['A2'] = f"Periode: {start_date.strftime('%d %b %Y')} - {end_date.strftime('%d %b %Y')}"

    # Judul Kolom
    headers = ['Nama Pelanggan', 'No. Telepon', 'Total Kunjungan', 'Total Belanja (Omzet)', 'Kunjungan Terakhir']
    for col_num, header_title in enumerate(headers, 1):
        cell = sheet.cell(row=4, column=col_num, value=header_title)
        cell.font = bold_font
        cell.border = Border(bottom=Side(style='medium'))

    # Isi Data
    for row_num, customer in enumerate(customers, 5):
        sheet.cell(row=row_num, column=1, value=customer.name)
        sheet.cell(row=row_num, column=2, value=customer.phone_number)
        sheet.cell(row=row_num, column=3, value=customer.total_visits)
        
        spending_cell = sheet.cell(row=row_num, column=4, value=customer.total_spending)
        spending_cell.number_format = '"Rp "#,##0'

        last_visit_cell = sheet.cell(row=row_num, column=5, value=customer.last_visit)
        if customer.last_visit:
            # FIX: Hapus info timezone agar Excel tidak error
            naive_dt = customer.last_visit.replace(tzinfo=None)
            last_visit_cell.value = naive_dt
            last_visit_cell.number_format = 'dd-mmm-yyyy'
        else:
            last_visit_cell.value = "-"

    # Lebar Kolom
    widths = [25, 20, 15, 20, 20]
    for i, width in enumerate(widths, 1):
        sheet.column_dimensions[get_column_letter(i)].width = width

    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return buffer

def export_mechanic_report_to_excel(report_data):
    """
    Fungsi Baru: Export Excel Kinerja Mekanik
    """
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

def export_expense_breakdown_to_excel(report_data): 
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Rincian Pengeluaran"
    bold_font = Font(bold=True)
    
    sheet['A1'] = "Laporan Rincian Pengeluaran"
    sheet['A1'].font = Font(bold=True, size=14)
    sheet['A2'] = f"Periode: {report_data['start_date']} - {report_data['end_date']}"
    
    headers = ['Kategori', 'Frekuensi (Kali)', 'Total Nominal', 'Persentase']
    for col, h in enumerate(headers, 1):
        sheet.cell(row=4, column=col, value=h).font = bold_font
    
    for idx, row in enumerate(report_data['breakdown'], 5):
        sheet.cell(row=idx, column=1, value=row['category'])
        sheet.cell(row=idx, column=2, value=row['count'])
        sheet.cell(row=idx, column=3, value=row['total']).number_format = '"Rp "#,##0'
        sheet.cell(row=idx, column=4, value=f"{row['percent']}%")
        
    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return buffer

def export_dead_stock_to_excel(dead_stock_data):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Dead Stock"
    bold_font = Font(bold=True)
    
    sheet['A1'] = "Laporan Barang Mati (Dead Stock)"
    sheet['A1'].font = Font(bold=True, size=14)
    sheet['A2'] = f"Generated: {datetime.now().strftime('%d %b %Y')}"
    
    headers = ['Nama Barang', 'Stok Saat Ini', 'Terakhir Terjual', 'Hari Tidak Laku', 'Nilai Aset Mandeg']
    for col, h in enumerate(headers, 1):
        sheet.cell(row=4, column=col, value=h).font = bold_font
        
    for idx, row in enumerate(dead_stock_data, 5):
        sheet.cell(row=idx, column=1, value=row['item'].name)
        sheet.cell(row=idx, column=2, value=row['item'].quantity)
        
        last = row['last_sale'].strftime('%d-%m-%Y') if row['last_sale'] else "Belum Pernah"
        sheet.cell(row=idx, column=3, value=last)
        sheet.cell(row=idx, column=4, value=row['days_inactive'])
        sheet.cell(row=idx, column=5, value=row['asset_value']).number_format = '"Rp "#,##0'

    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return buffer

def export_sales_report_to_excel(report_data):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Sales Report"
    bold_font = Font(bold=True)
    
    sheet['A1'] = "Laporan Penjualan Barang"
    sheet['A2'] = f"Periode: {report_data['start_date']} - {report_data['end_date']}"
    
    headers = ['Nama Barang', 'Qty Terjual', 'Omzet (Revenue)', 'Estimasi Profit', 'Margin %']
    for col, h in enumerate(headers, 1):
        sheet.cell(row=4, column=col, value=h).font = bold_font
        
    for idx, row in enumerate(report_data['sales_data'], 5):
        sheet.cell(row=idx, column=1, value=row['name'])
        sheet.cell(row=idx, column=2, value=row['qty'])
        sheet.cell(row=idx, column=3, value=row['revenue']).number_format = '"Rp "#,##0'
        sheet.cell(row=idx, column=4, value=row['profit']).number_format = '"Rp "#,##0'
        sheet.cell(row=idx, column=5, value=f"{round(row['margin'], 1)}%")

    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return buffer