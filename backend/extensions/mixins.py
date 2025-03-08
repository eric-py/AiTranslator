from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect

class AnonymousRequiredMixin(UserPassesTestMixin):
    """
    Mixin to restrict access to anonymous users only.
    Redirects authenticated users to Dashboard page.
    """
    def test_func(self):
        """Check if user is anonymous"""
        return not self.request.user.is_authenticated

    def handle_no_permission(self):
        """Redirect authenticated users to profile"""
        return redirect('dashboard:dashboard')

    def dispatch(self, request, *args, **kwargs):
        """Override dispatch to handle both GET and POST requests appropriately"""
        user_test_result = self.get_test_func()()
        if not user_test_result and self.request.user.is_authenticated:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)