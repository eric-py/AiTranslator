from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    """
    Custom user creation form
    """
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

class EmailChangeForm(forms.Form):
    """
    Form to change email
    """
    new_email = forms.EmailField()
    confirm_email = forms.EmailField()

    def clean(self):
        cleaned_data = super().clean()
        new_email = cleaned_data.get('new_email')
        confirm_email = cleaned_data.get('confirm_email')

        if new_email and confirm_email:
            if new_email != confirm_email:
                raise forms.ValidationError('ایمیل‌ها باید یکسان باشند.')
            
            if User.objects.filter(email=new_email).exists():
                raise forms.ValidationError('این ایمیل قبلاً ثبت شده است.')
        
        return cleaned_data

class CustomPasswordChangeForm(PasswordChangeForm):
    """
    Custom password change form to change labels
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].label = 'رمز عبور فعلی'
        self.fields['new_password1'].label = 'رمز عبور جدید'
        self.fields['new_password2'].label = 'تکرار رمز عبور جدید'