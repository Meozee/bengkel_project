# core/middleware.py

from . import signals

class ActivityLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Sebelum view dijalankan, simpan user
        if request.user.is_authenticated:
            signals.set_current_user(request.user)

        response = self.get_response(request)
        return response