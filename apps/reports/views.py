from django.shortcuts import render
from django.http import HttpResponse
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from datetime import datetime, timedelta
from django.db.models import Sum

# Import Utils & Exports
from . import utils, exports
from apps.inventory.models import Category
from apps.master_data.models import Mechanic
from apps.expenses.models import ExpenseCategory

# Helper: Parsing Tanggal dari URL
def _get_date_range(request):
    today = timezone.now().date()
    start_str = request.GET.get('start_date')
    end_str = request.GET.get('end_date')
    
    if start_str and end_str:
        try:
            start = datetime.strptime(start_str, '%Y-%m-%d').date()
            end = datetime.strptime(end_str, '%Y-%m-%d').date()
        except ValueError:
            start = today.replace(day=1)
            end = today
    else:
        start = today.replace(day=1)
        end = today
    return start, end, start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')

@login_required
def report_index(request):
    return render(request, 'reports/report_index.html')

# ==============================================================================
# 1. FINANCIAL REPORT (LABA RUGI)
# ==============================================================================
@login_required
def financial_report_view(request):
    start_date, end_date, s_str, e_str = _get_date_range(request)
    
    data = None
    if 'start_date' in request.GET:
        data = utils.generate_financial_report(start_date, end_date)

    context = {
        'start_date': s_str,
        'end_date': e_str,
        'report_data': data
    }
    return render(request, 'reports/financial_report.html', context)

@login_required
def export_financial_report(request):
    start_date, end_date, _, _ = _get_date_range(request)
    data = utils.generate_financial_report(start_date, end_date)
    excel_file = exports.export_financial_report_to_excel(data)
    
    response = HttpResponse(excel_file, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="Laporan_Keuangan_{start_date}.xlsx"'
    return response

# ==============================================================================
# 2. INVENTORY REPORT
# ==============================================================================
@login_required
def inventory_report_view(request):
    filters = {
        'q': request.GET.get('q'),
        'category': request.GET.get('category'),
        'stock_status': request.GET.get('stock_status'),
        'status': request.GET.get('status', 'active'),
        'min_price': request.GET.get('min_price'),
        'max_price': request.GET.get('max_price'),
        'join_date_start': request.GET.get('join_date_start'),
        'join_date_end': request.GET.get('join_date_end'),
    }

    items_qs = utils.get_inventory_queryset(filters)
    
    # Hitung total aset untuk seluruh data (sebelum pagination)
    total_asset_all = sum(item.asset_value for item in items_qs)

    paginator = Paginator(items_qs, 50)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'items': page_obj,
        'categories': Category.objects.filter(is_active=True),
        'filters': filters,
        'total_asset': total_asset_all
    }
    return render(request, 'reports/inventory_report.html', context)

@login_required
def export_inventory_excel(request):
    filters = {
        'q': request.GET.get('q'),
        'category': request.GET.get('category'),
        'stock_status': request.GET.get('stock_status'),
        'status': request.GET.get('status', 'active'),
        'min_price': request.GET.get('min_price'),
        'max_price': request.GET.get('max_price'),
        'join_date_start': request.GET.get('join_date_start'),
        'join_date_end': request.GET.get('join_date_end'),
    }
    
    # Gunakan utils yang sama agar hasil filter konsisten
    items = utils.get_inventory_queryset(filters)
    
    # Panggil fungsi export baru dari exports.py
    excel_file = exports.export_inventory_report_to_excel(items)
    
    response = HttpResponse(excel_file, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    filename = f"Laporan_Stok_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

@login_required
def export_inventory_report(request):
    filters = {
        'q': request.GET.get('q'),
        'category': request.GET.get('category'),
        'stock_status': request.GET.get('stock_status'),
        'status': request.GET.get('status', 'active'),
    }
    items = utils.get_inventory_queryset(filters)
    pdf_file = exports.export_inventory_report_to_pdf(items)
    
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="laporan_inventory.pdf"'
    return response

# ==============================================================================
# 3. MECHANIC PERFORMANCE
# ==============================================================================
@login_required
def mechanic_performance_view(request):
    start_date, end_date, s_str, e_str = _get_date_range(request)
    mechanic_ids = request.GET.getlist('mechanic')
    
    report_data = []
    if 'start_date' in request.GET: 
        report_data = utils.get_mechanic_performance_data(mechanic_ids, start_date, end_date)

    context = {
        'mechanics': Mechanic.objects.all(),
        'selected_ids': [int(x) for x in mechanic_ids if x.isdigit()],
        'start_date': s_str,
        'end_date': e_str,
        'report_data': report_data
    }
    return render(request, 'reports/mechanic_performance.html', context)

@login_required
def export_mechanic_report(request):
    start_date, end_date, _, _ = _get_date_range(request)
    mechanic_ids = request.GET.getlist('mechanic')
    data = utils.get_mechanic_performance_data(mechanic_ids, start_date, end_date)
    
    excel_file = exports.export_mechanic_report_to_excel(data, start_date, end_date)
    response = HttpResponse(excel_file, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="kinerja_mekanik.xlsx"'
    return response

# ==============================================================================
# 4. SALES REPORT
# ==============================================================================
@login_required
def sales_report_view(request):
    start_date, end_date, s_str, e_str = _get_date_range(request)
    filters = {
        'start_date': start_date,
        'end_date': end_date,
        'q': request.GET.get('q'),
        'category': request.GET.get('category')
    }

    sales_data, total_omzet, total_profit = utils.get_sales_report_data(filters)
    
    paginator = Paginator(sales_data, 50)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'sales_data': page_obj,
        'total_omzet': total_omzet,
        'total_profit': total_profit,
        'start_date': s_str,
        'end_date': e_str,
        'categories': Category.objects.filter(is_active=True),
        'filters': filters
    }
    return render(request, 'reports/sales_report.html', context)

@login_required
def export_sales_report(request):
    start_date, end_date, _, _ = _get_date_range(request)
    filters = {
        'start_date': start_date,
        'end_date': end_date,
        'q': request.GET.get('q'),
        'category': request.GET.get('category')
    }
    sales_data, _, _ = utils.get_sales_report_data(filters)
    
    # Format data for export
    report_data = {
        'sales_data': sales_data,
        'start_date': start_date,
        'end_date': end_date
    }
    
    excel_file = exports.export_sales_report_to_excel(report_data)
    response = HttpResponse(excel_file, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="laporan_penjualan.xlsx"'
    return response

# ==============================================================================
# 5. DEAD STOCK REPORT (YANG BIKIN ERROR SEBELUMNYA)
# ==============================================================================
@login_required
def dead_stock_view(request):
    days = request.GET.get('days', 90)
    cat_id = request.GET.get('category')
    q = request.GET.get('q')

    dead_stock_list = utils.get_dead_stock_queryset(days, cat_id, q)
    
    paginator = Paginator(dead_stock_list, 50)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'dead_stock': page_obj,
        'days': days,
        'categories': Category.objects.filter(is_active=True),
        'filters': {'q': q, 'category': cat_id}
    }
    return render(request, 'reports/dead_stock_report.html', context)

@login_required
def export_dead_stock(request):
    days = request.GET.get('days', 90)
    cat_id = request.GET.get('category')
    q = request.GET.get('q')
    
    data = utils.get_dead_stock_queryset(days, cat_id, q)
    excel_file = exports.export_dead_stock_to_excel(data)
    
    response = HttpResponse(excel_file, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="dead_stock_{days}_hari.xlsx"'
    return response

# ==============================================================================
# 6. EXPENSE BREAKDOWN REPORT
# ==============================================================================
@login_required
def expense_breakdown_view(request):
    start_date, end_date, s_str, e_str = _get_date_range(request)
    filters = {
        'start_date': start_date,
        'end_date': end_date,
        'category': request.GET.get('category'),
        'q': request.GET.get('q')
    }

    expenses = utils.get_expense_queryset(filters)
    total_expense = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    
    paginator = Paginator(expenses, 50)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'expenses': page_obj,
        'total_expense': total_expense,
        'categories': ExpenseCategory.objects.all(),
        'start_date': s_str, 
        'end_date': e_str,
        'filters': filters
    }
    return render(request, 'reports/expense_breakdown.html', context)

@login_required
def export_expense_breakdown(request):
    start_date, end_date, _, _ = _get_date_range(request)
    filters = {
        'start_date': start_date,
        'end_date': end_date,
        'category': request.GET.get('category'),
        'q': request.GET.get('q')
    }
    
    # Re-calculate breakdown summary for export
    expenses = utils.get_expense_queryset(filters)
    total_expense = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Manual regrouping to match export format requirement
    from django.db.models import Count
    summary_qs = expenses.values('category__name').annotate(
        total=Sum('amount'), count=Count('id')
    ).order_by('-total')
    
    breakdown_data = []
    for item in summary_qs:
        percent = (item['total'] / total_expense * 100) if total_expense > 0 else 0
        breakdown_data.append({
            'category': item['category__name'],
            'total': item['total'],
            'count': item['count'],
            'percent': round(percent, 1)
        })

    report_data = {
        'breakdown': breakdown_data,
        'start_date': start_date,
        'end_date': end_date
    }

    excel_file = exports.export_expense_breakdown_to_excel(report_data)
    response = HttpResponse(excel_file, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="rincian_pengeluaran.xlsx"'
    return response

# ==============================================================================
# 7. VEHICLE HISTORY (New Customer Report)
# ==============================================================================
@login_required
def vehicle_history_view(request):
    filters = {
        'plate': request.GET.get('plate'),
        'min_visits': request.GET.get('min_visits'),
        'sort_by': request.GET.get('sort_by', '-last_visit')
    }
    
    vehicles = utils.get_vehicle_history_queryset(filters)
    
    paginator = Paginator(vehicles, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'vehicles': page_obj,
        'filters': filters
    }
    return render(request, 'reports/vehicle_history.html', context)

# Alias agar link lama (jika ada) tidak error
@login_required
def customer_report_view(request):
    return vehicle_history_view(request)

@login_required
def export_customer_report(request):
    # Menggunakan logika vehicle history untuk export
    filters = {
        'plate': request.GET.get('plate'),
        'sort_by': request.GET.get('sort_by', '-last_visit')
    }
    vehicles = utils.get_vehicle_history_queryset(filters)
    
    # Kita buat wrapper object sederhana agar kompatibel dengan fungsi export lama
    class CustomerWrapper:
        def __init__(self, vehicle):
            self.name = vehicle.customer.name if vehicle.customer else "Umum"
            self.phone_number = vehicle.license_plate # Pakai Plat sebagai identitas utama
            self.total_visits = vehicle.total_visits
            self.total_spending = vehicle.total_spending
            self.last_visit = vehicle.last_visit

    customer_list = [CustomerWrapper(v) for v in vehicles]
    
    # Dummy dates for header
    start_date = datetime.now()
    end_date = datetime.now()

    excel_file = exports.export_customer_report_to_excel(customer_list, start_date, end_date)
    response = HttpResponse(excel_file, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="riwayat_kendaraan.xlsx"'
    return response