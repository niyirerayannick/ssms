from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User, Group
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from .forms import UserUpdateForm, ProfileUpdateForm
from .models import Profile


@require_http_methods(["GET", "POST"])
def login_view(request):
    """User login view."""
    if request.user.is_authenticated:
        return redirect('dashboard:index')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
            return redirect('dashboard:index')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'accounts/login.html')


@login_required
def logout_view(request):
    """User logout view."""
    from django.contrib.auth import logout
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('accounts:login')


# Helper function to check if user is admin or staff
def is_admin_or_staff(user):
    return user.is_staff or user.is_superuser or user.groups.filter(name='Admin').exists()


@login_required
@user_passes_test(is_admin_or_staff)
def user_list(request):
    """List all users with their roles."""
    search_query = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')
    
    users = User.objects.all().prefetch_related('groups')
    
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    if role_filter:
        users = users.filter(groups__name=role_filter)
    
    users = users.order_by('username')
    
    # Get all available roles
    roles = Group.objects.all().order_by('name')
    
    context = {
        'users': users,
        'roles': roles,
        'search_query': search_query,
        'role_filter': role_filter,
    }
    return render(request, 'accounts/user_list.html', context)


@login_required
@user_passes_test(is_admin_or_staff)
def user_create(request):
    """Create a new user."""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        role = request.POST.get('role')
        is_active = request.POST.get('is_active') == 'on'
        
        # Validation
        if not all([username, password, role]):
            messages.error(request, 'Username, password, and role are required.')
            return redirect('accounts:user_create')
        
        if password != password_confirm:
            messages.error(request, 'Passwords do not match.')
            return redirect('accounts:user_create')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, f'Username "{username}" already exists.')
            return redirect('accounts:user_create')
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password,
            is_active=is_active
        )
        
        # Assign role
        try:
            group = Group.objects.get(name=role)
            user.groups.add(group)
            
            # If Admin role, also set is_staff
            if role == 'Admin':
                user.is_staff = True
                user.save()
            
            if email and settings.DEFAULT_FROM_EMAIL and settings.EMAIL_HOST_USER:
                login_url = request.build_absolute_uri('/login/')
                
                # Prepare HTML content
                context = {
                    'name': first_name or username,
                    'username': username,
                    'password': password,
                    'login_url': login_url,
                }
                html_message = render_to_string('emails/user_welcome.html', context)
                plain_message = strip_tags(html_message)
                
                send_mail(
                    subject='Your SIMS account credentials',
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    html_message=html_message,
                    fail_silently=True,
                )
            messages.success(request, f'User "{username}" created successfully with role: {role}')
            return redirect('accounts:user_list')
        except Group.DoesNotExist:
            messages.error(request, f'Role "{role}" does not exist. Please run setup_user_roles command.')
            user.delete()
            return redirect('accounts:user_create')
    
    # Get available roles
    roles = Group.objects.all().order_by('name')
    
    return render(request, 'accounts/user_form.html', {
        'roles': roles,
        'is_edit': False
    })


@login_required
@user_passes_test(is_admin_or_staff)
def user_edit(request, user_id):
    """Edit an existing user."""
    user_to_edit = get_object_or_404(User, pk=user_id)
    
    # Prevent editing superusers unless you are a superuser
    if user_to_edit.is_superuser and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to edit superusers.')
        return redirect('accounts:user_list')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        role = request.POST.get('role')
        is_active = request.POST.get('is_active') == 'on'
        new_password = request.POST.get('new_password')
        password_confirm = request.POST.get('password_confirm')
        
        # Update user info
        user_to_edit.email = email
        user_to_edit.first_name = first_name
        user_to_edit.last_name = last_name
        user_to_edit.is_active = is_active
        
        # Update password if provided
        if new_password:
            if new_password != password_confirm:
                messages.error(request, 'Passwords do not match.')
                return redirect('accounts:user_edit', user_id=user_id)
            user_to_edit.set_password(new_password)
        
        user_to_edit.save()
        
        # Update role
        user_to_edit.groups.clear()
        try:
            group = Group.objects.get(name=role)
            user_to_edit.groups.add(group)
            
            # If Admin role, also set is_staff
            if role == 'Admin':
                user_to_edit.is_staff = True
            else:
                user_to_edit.is_staff = False
            user_to_edit.save()
            
            messages.success(request, f'User "{user_to_edit.username}" updated successfully.')
            return redirect('accounts:user_list')
        except Group.DoesNotExist:
            messages.error(request, f'Role "{role}" does not exist.')
            return redirect('accounts:user_edit', user_id=user_id)
    
    # Get available roles
    roles = Group.objects.all().order_by('name')
    current_role = user_to_edit.groups.first()
    
    return render(request, 'accounts/user_form.html', {
        'user_to_edit': user_to_edit,
        'roles': roles,
        'current_role': current_role,
        'is_edit': True
    })


@login_required
@user_passes_test(is_admin_or_staff)
def user_delete(request, user_id):
    """Delete a user."""
    user_to_delete = get_object_or_404(User, pk=user_id)
    
    # Prevent deleting superusers or yourself
    if user_to_delete.is_superuser:
        messages.error(request, 'Cannot delete superuser accounts.')
        return redirect('accounts:user_list')
    
    if user_to_delete.id == request.user.id:
        messages.error(request, 'Cannot delete your own account.')
        return redirect('accounts:user_list')
    
    if request.method == 'POST':
        username = user_to_delete.username
        user_to_delete.delete()
        messages.success(request, f'User "{username}" deleted successfully.')
        return redirect('accounts:user_list')
    
    return render(request, 'accounts/user_confirm_delete.html', {
        'user_to_delete': user_to_delete
    })

@login_required
def profile_view(request):
    """User profile view."""
    # Ensure profile exists
    if not hasattr(request.user, 'profile'):
        Profile.objects.create(user=request.user)

    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)

        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Your account has been updated!')
            return redirect('accounts:profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        'u_form': u_form,
        'p_form': p_form,
        'title': 'Profile'
    }

    return render(request, 'accounts/profile.html', context)
