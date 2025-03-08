from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView, PasswordChangeView, PasswordResetView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.views.generic import CreateView
from django.views import View
from django.urls import reverse_lazy
from django.contrib import messages

from extensions.decorators import anonymous_required
from extensions.mixins import AnonymousRequiredMixin

from .forms import (
    CustomUserCreationForm,
    EmailChangeForm, 
    CustomPasswordChangeForm
)


@anonymous_required
def home(request):
    """View for home page - only accessible to anonymous users"""
    context = {
        'title': 'صفحه اصلی',
        'active': 'home',
    }
    return render(request, 'account/home.html', context)


class CustomLoginView(AnonymousRequiredMixin, LoginView):
    """Custom login view """
    template_name = 'account/login.html'
    success_url = reverse_lazy('dashboard:dashboard')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'active': 'login',
            'title': 'ورود'
        })
        return context


class RegisterView(AnonymousRequiredMixin, CreateView):
    """User registration view"""
    form_class = CustomUserCreationForm
    template_name = 'account/register.html'
    success_url = reverse_lazy('account:login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'active': 'register',
            'title': 'ثبت نام'
        })
        return context


@login_required
def profile(request):
    """User profile view"""
    context = {
        'title': 'پروفایل',
        'active': 'profile'
    }
    return render(request, 'account/profile.html', context)


class CustomPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    """Custom password change view with success message"""
    form_class = CustomPasswordChangeForm
    template_name = 'account/profile.html'
    success_url = reverse_lazy('account:profile')

    def form_valid(self, form):
        messages.success(self.request, 'رمز عبور با موفقیت تغییر کرد.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'لطفاً خطاهای فرم را برطرف کنید.')
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'پروفایل',
            'active': 'profile'
        })
        return context

class EmailChangeView(LoginRequiredMixin, View):
    """View for handling email change requests"""
    def post(self, request):
        form = EmailChangeForm(request.POST)
        if form.is_valid():
            new_email = form.cleaned_data['new_email']
            user = request.user
            user.email = new_email
            user.save()
            messages.success(request, 'ایمیل با موفقیت تغییر کرد.')
            return redirect('account:profile')
        
        context = {
            'title': 'پروفایل',
            'active': 'profile',
            'email_form': form
        }
        return render(request, 'account/profile.html', context)

@login_required
def delete_account(request):
    """View for handling account deletion"""
    if request.method == 'POST':
        user = request.user
        user.delete()
        messages.success(request, 'حساب کاربری شما با موفقیت حذف شد.')
        return redirect('home')
    return redirect('account:profile')

@method_decorator(anonymous_required, name='dispatch')
class CustomPasswordResetView(PasswordResetView):
    """Custom password reset view"""
    template_name = 'account/password_reset.html'
    email_template_name = 'account/password_reset_email.html'
    success_url = reverse_lazy('account:password_reset_done')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'فراموشی رمز عبور',
            'active': 'login'
        })
        return context