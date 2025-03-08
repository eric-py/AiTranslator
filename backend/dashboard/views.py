from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from .models import UserStats

@login_required
def dashboard(request):
    """Dashboard view showing user statistics and recent translations"""
    # Get or create user stats
    stats, created = UserStats.objects.get_or_create(user=request.user)
    
    # Update all stats
    stats.update_all_stats()
    
    context = {
        'title': 'داشبورد',
        'active': 'dashboard',
        'stats': stats,
        'recent_books': request.user.book_set.all()[:3]
    }
    return render(request, 'dashboard/dashboard.html', context)