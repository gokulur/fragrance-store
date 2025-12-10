from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
import secrets
import random
from django.core.mail import send_mail
from django.conf import settings
from .models import EmailOTP,Profile
from django.utils import timezone
from datetime import timedelta 
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse
password_reset_tokens = {}
print(password_reset_tokens)


# -----------------------------
# REGISTER
# -----------------------------
def register_page(request):
   
    return render(request, 'register.html')

def register_action(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password != confirm_password:
            messages.error(request, "Passwords do not match!")
            return redirect('register_page')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists!")
            return redirect('register_page')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists!")
            return redirect('register_page')

        # Create user
        user = User.objects.create_user(username=username, email=email, password=password)
        user.is_active = False
        user.save()

        # Create profile manually
        Profile.objects.create(user=user, phone=phone)

        # Generate and send OTP
        otp = str(random.randint(100000, 999999))
        EmailOTP.objects.update_or_create(user=user, defaults={'otp': otp})

        subject = "Your Account Verification OTP"
        message = f"Hello {username},\n\nYour OTP for account verification is: {otp}\n\nDo not share this code with anyone.\n\nThank you!"
        send_mail(subject, message, settings.EMAIL_HOST_USER, [email])

        request.session['pending_user'] = username
        messages.info(request, "OTP sent to your email. Please verify to activate your account.")
        return redirect('verify_otp_page')
    
# -----------------------------
# verify otp
# -----------------------------


def verify_otp_page(request):
    return render(request, 'verify_otp.html')

def verify_otp_action(request):
    if request.method == 'POST':
        otp_entered = request.POST.get('otp')
        username = request.session.get('pending_user')

        if not username:
            messages.error(request, "Session expired. Please register again.")
            return redirect('register_page')

        user = User.objects.get(username=username)
        saved_otp = EmailOTP.objects.get(user=user).otp

        if otp_entered == saved_otp:
            user.is_active = True
            user.save()
            EmailOTP.objects.filter(user=user).delete()
            del request.session['pending_user']
            messages.success(request, "Account verified successfully! Please login.")
            return redirect('login_page')
        else:
            messages.error(request, "Invalid OTP. Try again.")
            return redirect('verify_otp_page')

# -----------------------------
# LOGIN
# -----------------------------
def login_page(request):
    
    return render(request,'login.html')

def login_action(request):
    if request.method == 'POST':
        email = request.POST.get('username')
        password = request.POST.get('password')
        
        # Try to find user by email
        try:
            user_obj = User.objects.get(email=email)
            username = user_obj.username
        except User.DoesNotExist:
            messages.error(request, "No account found with this email!")
            return redirect('login_page')
        
        # Authenticate
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome {user.first_name or user.username}!")
            
            # Check for 'next' parameter (for redirects after login)
            next_url = request.GET.get('next') or request.POST.get('next')
            
            if next_url:
                # User came from a protected page
                return redirect(next_url)
            
            # Default redirects based on role
            if user.is_superuser or user.is_staff:
                return redirect(reverse('admin_dashboard'))
            else:
                return redirect('all_collections')
        else:
            messages.error(request, "Invalid email or password!")
            return redirect('login_page')
    
    return redirect('login_page')

# -----------------------------
# LOGOUT
# -----------------------------
def logout_action(request):
    logout(request)
    messages.info(request, "You have logged out.")
    return redirect('/')

# -----------------------------
# PASSWORD CHANGE
# -----------------------------
@login_required
def password_change_page(request):
    
    return render(request, 'password_change.html')

@login_required
def password_change_action(request):
   
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if new_password != confirm_password:
            messages.error(request, "Passwords do not match!")
            return redirect('password_change_page')

        user = request.user
        if not user.check_password(old_password):
            messages.error(request, "Old password is incorrect!")
            return redirect('password_change_page')

        user.set_password(new_password)
        user.save()
        update_session_auth_hash(request, user)
        messages.success(request, "Password changed successfully!")
        return redirect('/')

# -----------------------------
# PASSWORD RESET
# -----------------------------
def password_reset_page(request):
    return render(request, 'password_reset.html')


def password_reset_action(request):
    if request.method == 'POST':
        email = request.POST.get('email')

        try:
            user = User.objects.get(email=email)
            token = secrets.token_urlsafe(16)

            # Store with expiry time
            password_reset_tokens[token] = {
                "username": user.username,
                "expires_at": timezone.now() + timedelta(minutes=15)   
            }

            reset_link = f"http://127.0.0.1:8000/reset/{token}/"

            # Send email
            subject = "Password Reset Request"
            message = f"Hello {user.username},\n\nWe received a request to reset your password.\nClick the link below to set a new password:\n\n{reset_link}\n\nIf you didn’t request this, please ignore this email.\n\nThis link will expire in 15 minutes."
            send_mail(subject, message, settings.EMAIL_HOST_USER, [email])

            messages.success(request, "Password reset link sent to your email!")
            return redirect('password_reset_page')

        except User.DoesNotExist:
            messages.error(request, "No account found with that email!")
            return redirect('password_reset_page')


# -----------------------------
# PASSWORD RESET CONFIRM
# -----------------------------
def password_reset_confirm_page(request, token):
    """Show reset password form if token valid"""
    if token not in password_reset_tokens:
        messages.error(request, "Invalid or expired token!")
        return redirect('password_reset_page')

    return render(request, 'password_reset_confirm.html', {'token': token})


def password_reset_confirm_action(request, token):
    """POST: handle new password form submission"""
    if token not in password_reset_tokens:
        messages.error(request, "Invalid or expired token!")
        return redirect('password_reset_page')

    username = password_reset_tokens[token]

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        messages.error(request, "User not found!")
        del password_reset_tokens[token]
        return redirect('password_reset_page')

    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if not new_password or not confirm_password:
            messages.error(request, "All fields are required!")
            return redirect('password_reset_confirm_page', token=token)

        if new_password != confirm_password:
            messages.error(request, "Passwords do not match!")
            return redirect('password_reset_confirm_page', token=token)

        user.set_password(new_password)
        user.save()

        # delete used token
        del password_reset_tokens[token]

        messages.success(request, "Password reset successful! Please log in.")
        return redirect('login_page')

    return redirect('password_reset_confirm_page', token=token)


#user profile
def user_profile(request):
   
    return render(request, 'user_profile.html', {
        
    })