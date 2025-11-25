# apps/reports/views.py

from django.shortcuts import render
from django.http import HttpResponse
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from datetime import datetime

# Import Helper Logging
from apps.accounts.utils import log_activity

# Import Logic & Exports
from .utils import (
    generate_financial_report, 
    generate_low_stock_report, 
    generate_mechanic_performance_report,
    generate_customer_report
)
from .exports import (
    export_financial_report_to_excel, 
    export_inventory_report_to_pdf,
    export_customer_report_to_excel,
    export_mechanic_report_to_excel
)
from apps.master_data.models import Mechanic

# ====================================================================
# WEB VIEWS
# ====================================================================

@login_required
def report_index(request):
    return render(request, 'reports/report_index.html')

@login_required
def financial_report_view(request):
    today = timezone.now().date()
    default_start = today.replace(day=1)
    
    start_date_str = request.GET.get('start_date', default_start.strftime('%Y-%m-%d'))
    end_date_str = request.GET.get('end_date', today.strftime('%Y-%m-%d'))

    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        report_data = generate_financial_report(start_date, end_date)
        
        # LOG (Target diawali "Report:")
        log_activity(request, 'VIEW_REPORT', 'Report: Financial', '', f"Melihat Laporan Keuangan: {start_date_str} s/d {end_date_str}")
    except ValueError:
        report_data = None

    context = {'start_date': start_date_str, 'end_date': end_date_str, 'report_data': report_data}
    return render(request, 'reports/financial_report.html', context)

@login_required
def inventory_report_view(request):
    low_stock_items = generate_low_stock_report()
    
    # LOG
    log_activity(request, 'VIEW_REPORT', 'Report: Inventory', '', f"Melihat Laporan Stok Rendah ({low_stock_items.count()} item)")

    context = {'items': low_stock_items, 'generated_date': timezone.now()}
    return render(request, 'reports/inventory_report.html', context)

@login_required
def mechanic_performance_view(request):
    today = timezone.now().date()
    default_start = today.replace(day=1)
    
    start_date_str = request.GET.get('start_date', default_start.strftime('%Y-%m-%d'))
    end_date_str = request.GET.get('end_date', today.strftime('%Y-%m-%d'))
    mechanic_id = request.GET.get('mechanic')

    report_data = None
    if mechanic_id:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            report_data = generate_mechanic_performance_report(mechanic_id, start_date, end_date)
            
            # LOG
            mech_name = report_data['mechanic'].name
            log_activity(request, 'VIEW_REPORT', 'Report: Mechanic', mechanic_id, f"Melihat Kinerja Mekanik: {mech_name}")
        except (ValueError, Mechanic.DoesNotExist):
            pass

    context = {
        'mechanics': Mechanic.objects.all(),
        'selected_mechanic_id': int(mechanic_id) if mechanic_id else None,
        'start_date': start_date_str,
        'end_date': end_date_str,
        'report_data': report_data
    }
    return render(request, 'reports/mechanic_performance.html', context)

@login_required
def customer_report_view(request):
    today = timezone.now().date()
    default_start = today.replace(day=1)
    
    start_date_str = request.GET.get('start_date', default_start.strftime('%Y-%m-%d'))
    end_date_str = request.GET.get('end_date', today.strftime('%Y-%m-%d'))
    sort_by = request.GET.get('sort_by', '-total_spending')

    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        report_data = generate_customer_report(start_date, end_date, sort_by)
        
        # LOG
        log_activity(request, 'VIEW_REPORT', 'Report: Customer', '', f"Melihat Analisis Pelanggan ({report_data.count()} rows)")
    except ValueError:
        report_data = []

    context = {'start_date': start_date_str, 'end_date': end_date_str, 'report_data': report_data, 'sort_by': sort_by}
    return render(request, 'reports/customer_report.html', context)

# ====================================================================
# EXPORT VIEWS
# ====================================================================

@login_required
def export_financial_report(request):
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        report_data = generate_financial_report(start_date, end_date)
        excel_buffer = export_financial_report_to_excel(report_data)
        
        log_activity(request, 'EXPORT_EXCEL', 'Report: Financial', '', f"Download Laporan Keuangan Excel")
        
        response = HttpResponse(excel_buffer, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="laporan_keuangan_{start_date_str}_{end_date_str}.xlsx"'
        return response
    except (ValueError, TypeError):
        return HttpResponse("Error generate report", status=400)

@login_required
def export_inventory_report(request):
    items = generate_low_stock_report()
    pdf_buffer = export_inventory_report_to_pdf(items, timezone.now())
    
    log_activity(request, 'EXPORT_PDF', 'Report: Inventory', '', "Download Laporan Stok Rendah PDF")
    
    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="laporan_stok_rendah.pdf"'
    return response

@login_required
def export_customer_report(request):
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    sort_by = request.GET.get('sort_by', '-total_spending')
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        customers = generate_customer_report(start_date, end_date, sort_by)
        excel_buffer = export_customer_report_to_excel(customers, start_date, end_date)
        
        log_activity(request, 'EXPORT_EXCEL', 'Report: Customer', '', f"Download Laporan Pelanggan Excel")
        
        response = HttpResponse(excel_buffer, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="laporan_pelanggan_{start_date_str}_{end_date_str}.xlsx"'
        return response
    except (ValueError, TypeError):
        return HttpResponse("Error generate report", status=400)

@login_required
def export_mechanic_report(request):
    mechanic_id = request.GET.get('mechanic')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        report_data = generate_mechanic_performance_report(mechanic_id, start_date, end_date)
        excel_buffer = export_mechanic_report_to_excel(report_data)
        
        log_activity(request, 'EXPORT_EXCEL', 'Report: Mechanic', mechanic_id, f"Export Mechanic Performance")
        
        response = HttpResponse(excel_buffer, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="kinerja_mekanik_{report_data["mechanic"].name}.xlsx"'
        return response
    except Exception:
        return HttpResponse("Error generate report", status=400)