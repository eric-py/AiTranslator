from django.db import models
from django.utils import timezone

from datetime import timedelta

from books.models import Page

class UserStats(models.Model):
    """Dashboard Model"""
    user = models.OneToOneField('account.User', on_delete=models.CASCADE, verbose_name='کاربر')
    total_books = models.IntegerField(default=0, verbose_name='تعداد کل کتاب‌ها')
    total_pages = models.IntegerField(default=0, verbose_name='تعداد کل صفحات')
    total_translated_pages = models.IntegerField(default=0, verbose_name='تعداد صفحات ترجمه شده')
    monthly_books = models.IntegerField(default=0, verbose_name='کتاب‌های این ماه')
    weekly_pages = models.IntegerField(default=0, verbose_name='صفحات این هفته')
    last_activity = models.DateTimeField(auto_now=True, verbose_name='آخرین فعالیت')

    class Meta:
        verbose_name = 'آمار کاربر'
        verbose_name_plural = 'آمار کاربران'

    def __str__(self):
        return f"آمار {self.user.username}"

    def update_monthly_stats(self):
        """Update monthly statistics"""
        current_month = timezone.now().month
        monthly_books = self.user.book_set.filter(
            created_at__month=current_month
        ).count()
        self.monthly_books = monthly_books
        self.save()

    def update_translated_pages(self):
        """Update total translated pages count"""
        total_translated = Page.objects.filter(
            book__user=self.user,
            is_translated=True
        ).count()
        self.total_translated_pages = total_translated
        self.save()

    def update_weekly_stats(self):
        """Update weekly statistics"""
        week_ago = timezone.now() - timedelta(days=7)
        weekly_translated = Page.objects.filter(
            book__user=self.user,
            is_translated=True,
            book__created_at__gte=week_ago
        ).count()
        self.weekly_pages = weekly_translated
        self.save()

    def update_all_stats(self):
        """Update all statistics"""
        self.update_monthly_stats()
        self.update_weekly_stats()
        self.update_translated_pages()