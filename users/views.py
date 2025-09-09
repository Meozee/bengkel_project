# users/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .decorators import role_required
from .models import Customer, User
from .forms import CustomerForm, UserCreationForm, UserUpdateForm
from core.models import ActivityLog

@login_required
@role_required(allowed_roles=['admin', 'staff'])
def user_management_view(request):
    customers = Customer.objects.all().order_by('-id')
    users = User.objects.all().order_by('username')
    logs = ActivityLog.objects.all()[:20]
    context = {
        'title': 'Manajemen Sistem',
        'customers': customers,
        'users': users,
        'logs': logs,
    }
    return render(request, 'users/user_management.html', context)

# --- CRUD Customer ---
@login_required
@role_required(allowed_roles=['admin', 'staff'])
def customer_create_view(request):
    form = CustomerForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('users:user_management')
    return render(request, 'users/customer_form.html', {'form': form, 'title': 'Tambah Customer'})

@login_required
@role_required(allowed_roles=['admin', 'staff'])
def customer_update_view(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    form = CustomerForm(request.POST or None, instance=customer)
    if form.is_valid():
        form.save()
        return redirect('users:user_management')
    return render(request, 'users/customer_form.html', {'form': form, 'title': f'Edit Customer: {customer.nama}'})

@login_required
@role_required(allowed_roles=['admin', 'staff'])
def customer_delete_view(request, pk):
    item = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        item.delete()
        return redirect('users:user_management')
    return render(request, 'users/confirm_delete.html', {'item': item})

# --- CRUD User (Akun Login) ---
@login_required
@role_required(allowed_roles=['admin', 'staff'])
def user_create_view(request):
    form = UserCreationForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('users:user_management')
    return render(request, 'users/user_form.html', {'form': form, 'title': 'Buat Akun Login Baru'})

@login_required
@role_required(allowed_roles=['admin', 'staff'])
def user_update_view(request, pk):
    user = get_object_or_404(User, pk=pk)
    form = UserUpdateForm(request.POST or None, instance=user)
    if form.is_valid():
        form.save()
        if request.user == user:
            update_session_auth_hash(request, user)
        return redirect('users:user_management')
    return render(request, 'users/user_form.html', {'form': form, 'title': f'Edit User: {user.username}'})

@login_required
@role_required(allowed_roles=['admin', 'staff'])
def user_delete_view(request, pk):
    item = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        item.delete()
        return redirect('users:user_management')
    return render(request, 'users/confirm_delete.html', {'item': item})

# --- Login & Logout ---
def login_view(request):
    if request.user.is_authenticated: return redirect('dashboard')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
    form = AuthenticationForm()
    return render(request, 'users/login.html', {'form': form, 'title': 'Login'})

def logout_view(request):
    logout(request)
    return redirect('login')