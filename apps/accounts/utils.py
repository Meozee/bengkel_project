# apps/accounts/utils.py

from .models import ActivityLog

def get_client_ip(request):
    """Mengambil IP Address user"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def log_activity(request, action_type, target_model="", target_id="", details=""):
    """
    Fungsi helper untuk mencatat log aktivitas.
    Cara pakai di view:
    log_activity(request, 'DELETE_TRANSACTION', 'Transaction', obj.id, 'Menghapus invoice INV-001')
    """
    if request.user.is_authenticated:
        ActivityLog.objects.create(
            user=request.user,
            action_type=action_type,
            target_model=target_model,
            target_id=str(target_id),
            details=details,
            ip_address=get_client_ip(request)
        )