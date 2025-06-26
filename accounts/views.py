## accounts/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import CreateView, UpdateView
from django.urls import reverse_lazy
from django.core.mail import send_mail
from django.conf import settings
from django.utils.crypto import get_random_string
from django.contrib.auth import get_user_model
from .forms import SignUpForm, ProfileForm

User = get_user_model()

# View do Signup
class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = 'accounts/signup.html'
    success_url = reverse_lazy('accounts:login')
    
    
    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_active = False  # Deactivate account until email verification
        user.email_verification_token = get_random_string(50)
        user.save()
        
        # Send verification email
        self.send_verification_email(user)
        
        messages.success(
            self.request, 
            'Account created successfully! Please check your email to verify your account.'
        )
        return super().form_valid(form)
    
    def send_verification_email(self, user):
        subject = 'Verify your Amazon Clone account'
        verification_url = self.request.build_absolute_uri(
            f'/accounts/verify-email/{user.email_verification_token}/'
        )
        message = f'''
        Hi {user.first_name},
        
        Please click the link below to verify your email address:
        {verification_url}
        
        If you didn't create this account, please ignore this email.
        
        Best regards,
        Amazon Clone Team
        '''
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )

def verify_email(request, token):
    try:
        user = User.objects.get(email_verification_token=token)
        user.is_active = True
        user.is_email_verified = True
        user.email_verification_token = ''
        user.save()
        
        messages.success(request, 'Email verified successfully! You can now login.')
        return redirect('accounts:login')
    except User.DoesNotExist:
        messages.error(request, 'Invalid verification token.')
        return redirect('accounts:signup')

class ProfileView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = ProfileForm
    template_name = 'accounts/profile.html'
    success_url = reverse_lazy('accounts:profile')
    
    def get_object(self):
        return self.request.user
    
    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully!')
        return super().form_valid(form)