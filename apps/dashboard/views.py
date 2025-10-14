# apps/dashboard/views.py
from django.shortcuts import render

def dashboard_view(request):
    # Nanti kita akan isi dengan data sungguhan
    context = {
        'total_revenue': 12500000,
        'total_transactions': 152,
    }
    return render(request, 'dashboard/index.html', context)