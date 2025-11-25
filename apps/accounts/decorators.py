# apps/accounts/decorators.py

from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import UserPassesTestMixin
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

# 1. Decorator untuk Function Based View (def view)
def owner_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        if request.user.role == 'OWNER':
            return view_func(request, *args, **kwargs)
        else:
            # Jika Admin mencoba akses, lempar error atau redirect
            messages.error(request, "Akses Ditolak! Hanya Owner yang bisa melakukan ini.")
            return redirect(request.META.get('HTTP_REFERER', 'dashboard:index'))
            
    return _wrapped_view

# 2. Mixin untuk Class Based View (class View)
class OwnerRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'OWNER'

    def handle_no_permission(self):
        messages.error(self.request, "Akses Ditolak! Hanya Owner yang bisa akses halaman ini.")
        return redirect('dashboard:index')