from django.shortcuts import render
from django.http import HttpResponse
from django.utils import timezone
from datetime import datetime, timedelta
from .utils import (
    generate_financial_report, 
    generate_low_stock_report, 
    generate_mechanic_performance_report,
    generate_customer_report
)
from .exports import (
    export_financial_report_to_excel, 
    export_inventory_report_to_pdf,
    export_customer_report_to_excel
)
from apps.master_data.models import Mechanic

def report_index(request):
    return render(request, 'reports/report_index.html')

def financial_report_view(request):
    today = timezone.now().date()
    default_start = today - timedelta(days=30)
    
    start_date_str = request.GET.get('start_date', default_start.strftime('%Y-%m-%d'))
    end_date_str = request.GET.get('end_date', today.strftime('%Y-%m-%d'))

    report_data = generate_financial_report(
        datetime.strptime(start_date_str, '%Y-%m-%d').date(),
        datetime.strptime(end_date_str, '%Y-%m-%d').date()
    )
        
    context = {
        'start_date': start_date_str,
        'end_date': end_date_str,
        'report_data': report_data
    }
    return render(request, 'reports/financial_report.html', context)

def inventory_report_view(request):
    low_stock_items = generate_low_stock_report()
    context = {
        'items': low_stock_items,
        'generated_date': timezone.now()
    }
    return render(request, 'reports/inventory_report.html', context)

def mechanic_performance_view(request):
    today = timezone.now().date()
    default_start = today - timedelta(days=30)
    
    start_date_str = request.POST.get('start_date', default_start.strftime('%Y-%m-%d'))
    end_date_str = request.POST.get('end_date', today.strftime('%Y-%m-%d'))
    mechanic_id = request.POST.get('mechanic')

    report_data = None
    if request.method == 'POST' and mechanic_id:
        report_data = generate_mechanic_performance_report(
            mechanic_id, 
            datetime.strptime(start_date_str, '%Y-%m-%d').date(), 
            datetime.strptime(end_date_str, '%Y-%m-%d').date()
        )

    context = {
        'mechanics': Mechanic.objects.all(),
        'selected_mechanic_id': int(mechanic_id) if mechanic_id else None,
        'start_date': start_date_str,
        'end_date': end_date_str,
        'report_data': report_data
    }
    return render(request, 'reports/mechanic_performance.html', context)

def customer_report_view(request):
    today = timezone.now().date()
    default_start = today - timedelta(days=30)
    
    start_date_str = request.GET.get('start_date', default_start.strftime('%Y-%m-%d'))
    end_date_str = request.GET.get('end_date', today.strftime('%Y-%m-%d'))
    sort_by = request.GET.get('sort_by', '-total_spending')

    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    
    report_data = generate_customer_report(start_date, end_date, sort_by)
        
    context = {
        'start_date': start_date_str,
        'end_date': end_date_str,
        'report_data': report_data,
        'sort_by': sort_by
    }
    return render(request, 'reports/customer_report.html', context)

# === EXPORT VIEWS ===

def export_financial_report(request):
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return HttpResponse("Format tanggal tidak valid.", status=400)

    report_data = generate_financial_report(start_date, end_date)
    excel_buffer = export_financial_report_to_excel(report_data)
    
    response = HttpResponse(
        excel_buffer,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="laporan_keuangan_{start_date_str}_sd_{end_date_str}.xlsx"'
    return response

def export_inventory_report(request):
    items = generate_low_stock_report()
    pdf_buffer = export_inventory_report_to_pdf(items, timezone.now())

    response = HttpResponse(
        pdf_buffer,
        content_type='application/pdf'
    )
    response['Content-Disposition'] = 'attachment; filename="laporan_stok_rendah.pdf"'
    return response

def export_customer_report(request):
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    sort_by = request.GET.get('sort_by', '-total_spending')

    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return HttpResponse("Format tanggal tidak valid.", status=400)

    customers = generate_customer_report(start_date, end_date, sort_by)
    excel_buffer = export_customer_report_to_excel(customers, start_date, end_date)
    
    response = HttpResponse(
        excel_buffer,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="laporan_pelanggan_{start_date_str}_sd_{end_date_str}.xlsx"'
    return response