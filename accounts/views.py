"""
Accounts views for TeamHub.
Handles user registration and authentication.
"""
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserRegistrationForm


def register(request):
    """Handle user registration with validation."""
    if request.user.is_authenticated:
        return redirect('space_list')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome to TeamHub, {user.username}!')
            return redirect('space_list')
    else:
        form = UserRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


def user_login(request):
    """Handle user login."""
    if request.user.is_authenticated:
        return redirect('space_list')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            next_url = request.GET.get('next', 'space_list')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()

    return render(request, 'accounts/login.html', {'form': form})


def user_logout(request):
    """Log out the current user."""
    if request.method == 'POST':
        logout(request)
        messages.info(request, 'You have been logged out.')
    return redirect('login')


@login_required
def profile(request):
    """Display the current user's profile and statistics."""
    user = request.user
    owned_spaces = user.owned_spaces.count()
    member_spaces = user.space_memberships.count()
    authored_notes = user.authored_notes.count()

    return render(request, 'accounts/profile.html', {
        'owned_spaces': owned_spaces,
        'member_spaces': member_spaces,
        'authored_notes': authored_notes,
    })
