from django.contrib.auth.decorators import user_passes_test
from django.urls import reverse_lazy

def anonymous_required(function):
    """
    Decorator to restrict access to logged in users
    """
    def check_anonymous(user):
        return not user.is_authenticated
    
    actual_decorator = user_passes_test(
        check_anonymous,
        login_url=reverse_lazy('dashboard:dashboard'),
        redirect_field_name=None
    )
    
    if function:
        return actual_decorator(function)
    return actual_decorator