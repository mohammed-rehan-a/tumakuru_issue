from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.views import LoginView, LogoutView
from .forms import CitizenRegistrationForm, CitizenLoginForm, ProfileUpdateForm
from .models import CitizenProfile, CitizenCertificate, OTPToken


def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = CitizenRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome to Tumakuru Civic Portal, {user.first_name}! Your account has been created.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CitizenRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})


def citizen_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = CitizenLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            return redirect(request.GET.get('next', 'dashboard'))
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = CitizenLoginForm()
    return render(request, 'accounts/login.html', {'form': form})


def citizen_logout(request):
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('home')


@login_required
def profile(request):
    profile = request.user.profile
    certificates = profile.certificates.all()
    reports = request.user.reports.order_by('-created_at')[:10]

    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user.first_name = form.cleaned_data['first_name']
            profile.user.last_name = form.cleaned_data['last_name']
            profile.user.email = form.cleaned_data['email']
            profile.user.save()
            profile.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=profile)

    return render(request, 'accounts/profile.html', {
        'form': form,
        'profile': profile,
        'certificates': certificates,
        'recent_reports': reports,
    })

def request_otp(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        phone = request.POST.get('phone', '').strip()
        if not phone:
            messages.error(request, 'Please enter your phone number.')
            return redirect('request_otp')
            
        # Find user by profile phone
        profile = CitizenProfile.objects.filter(phone=phone).first()
        if not profile:
            messages.error(request, 'No account found with this phone number.')
            return redirect('request_otp')
            
        import random, string, requests
        from django.conf import settings
        
        # Generate 6 digit OTP
        token = ''.join(random.choices(string.digits, k=6))
        
        # Save token
        OTPToken.objects.filter(user=profile.user, is_used=False).update(is_used=True) # invalidate old ones
        OTPToken.objects.create(user=profile.user, token=token)
        
        # Send via Fast2SMS
        api_key = getattr(settings, 'FAST2SMS_API_KEY', '')
        if api_key:
            try:
                msg = f"Your Tumakuru Civic Portal login OTP is {token}. Valid for 10 minutes."
                clean_phone = ''.join(filter(str.isdigit, phone))
                if clean_phone.startswith('91') and len(clean_phone) == 12:
                    clean_phone = clean_phone[2:]
                url = "https://www.fast2sms.com/dev/bulkV2"
                payload = {"route": "q", "message": msg, "language": "english", "flash": 0, "numbers": clean_phone}
                headers = {"authorization": api_key, "Content-Type": "application/json"}
                requests.post(url, json=payload, headers=headers, timeout=5)
            except Exception as e:
                pass
        
        request.session['otp_phone'] = phone
        messages.success(request, 'OTP sent to your mobile number.')
        return redirect('verify_otp')
        
    return render(request, 'accounts/request_otp.html')

def verify_otp(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    phone = request.session.get('otp_phone')
    if not phone:
        return redirect('request_otp')
        
    if request.method == 'POST':
        token = request.POST.get('token', '').strip()
        
        profile = CitizenProfile.objects.filter(phone=phone).first()
        if profile:
            otp_obj = OTPToken.objects.filter(user=profile.user, token=token, is_used=False).order_by('-created_at').first()
            if otp_obj and otp_obj.is_valid():
                otp_obj.is_used = True
                otp_obj.save()
                
                # Log the user in
                login(request, profile.user)
                del request.session['otp_phone']
                
                messages.success(request, f'Welcome back, {profile.user.first_name or profile.user.username}!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid or expired OTP.')
        else:
            messages.error(request, 'Account not found.')
            
    return render(request, 'accounts/verify_otp.html', {'phone': phone})

