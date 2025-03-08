from django.urls import path
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy

from . import views

app_name = 'account'

urlpatterns = [
    # Authentication URLs
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Profile URLs
    path('profile/', views.profile, name='profile'),
    path('profile/password/', views.CustomPasswordChangeView.as_view(), name='password_change'),
    path('profile/email/', views.EmailChangeView.as_view(), name='email_change'),
    path('profile/delete/', views.delete_account, name='delete_account'),

    # Password Reset URLs
    path('password-reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),

    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='account/password_reset_done.html',
             extra_context={'title': 'ارسال ایمیل', 'active': 'login'}
         ), 
         name='password_reset_done'),
    
    path('reset/<uidb64>/<token>/', 
        auth_views.PasswordResetConfirmView.as_view(
            template_name='account/password_reset_confirm.html',
            success_url=reverse_lazy('account:login'),
            extra_context={'title': 'تغییر رمز عبور', 'active': 'login'}
        ), 
        name='password_reset_confirm'),
]