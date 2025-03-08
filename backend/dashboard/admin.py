from django.contrib import admin
from .models import UserStats

# Register your models here.

@admin.register(UserStats)
class UserStatsAdmin(admin.ModelAdmin):
    """UserStats admin"""
    list_display = ['user', 'total_books', 'total_pages', 'total_translated_pages', 'last_activity']
    list_filter = ['last_activity']
    search_fields = ['user__username', 'user__email']
