from django.core.exceptions import ValidationError
from django.utils.html import format_html
from django.utils import timezone
from django.db import models

from langdetect import detect

# Create your models here.

class Book(models.Model):
    """Book model"""
    STATUS_CHOICES = [
        ('pending', 'در صف پردازش'),
        ('processing', 'در حال استخراج متن'),
        ('extraction_failed', 'خطا در استخراج متن'),
        ('ready_for_translation', 'آماده برای ترجمه'),
        ('translating', 'در حال ترجمه'),
        ('translation_failed', 'خطا در ترجمه'),
        ('completed', 'تکمیل شده'),
        ('failed', 'خطا')
    ]

    user = models.ForeignKey('account.User', on_delete=models.CASCADE)
    title = models.CharField(max_length=255, verbose_name='عنوان')
    file = models.FileField(upload_to='books/files/', verbose_name='فایل PDF')
    cover = models.ImageField(upload_to='books/covers/', null=True, blank=True, verbose_name='تصویر کاور')
    total_pages = models.IntegerField(default=0, verbose_name='تعداد صفحات')
    translated_pages = models.IntegerField(default=0, verbose_name='صفحات ترجمه شده')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending', verbose_name='وضعیت')
    last_processed_page = models.IntegerField(default=0, verbose_name='آخرین صفحه پردازش شده')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    last_activity = models.DateTimeField(auto_now=True, verbose_name='آخرین فعالیت')

    class Meta:
        verbose_name = 'کتاب'
        verbose_name_plural = 'کتاب‌ها'
        ordering = ['-created_at']

    def __str__(self):
        return self.title
    
    def is_stuck(self):
        """Check if book is stuck in processing/translating for more than 2 minutes"""
        if self.status in ['processing', 'translating']:
            time_diff = timezone.now() - self.last_activity
            return time_diff.total_seconds() > 3600  # 1 hour
        return False

    @property
    def progress(self):
        """محاسبه درصد پیشرفت ترجمه"""
        if self.status == 'completed':
            return 100
        elif self.status == 'translating' or self.status == 'ready_for_translation':
            return int((self.translated_pages / self.total_pages) * 50 + 50)
        else:
            return int((self.translated_pages / self.total_pages) * 50)
        
    def file_preview(self):
        if self.file:
            return format_html('<a href="{}" target="_blank">مشاهده فایل</a>', self.file.url)
        return "بدون فایل"
    file_preview.short_description = 'پیش‌نمایش فایل'
    

class Page(models.Model):
    """Page model"""
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='pages')
    number = models.IntegerField(verbose_name='شماره صفحه')
    original_text = models.TextField(verbose_name='متن اصلی')
    translated_text = models.TextField(null=True, blank=True, verbose_name='متن ترجمه شده')
    is_translated = models.BooleanField(default=False, verbose_name='ترجمه شده')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')
    
    class Meta:
        verbose_name = 'صفحه'
        verbose_name_plural = 'صفحات'
        ordering = ['number']
        unique_together = ['book', 'number']

    def __str__(self):
        return f"{self.book.title} - صفحه {self.number}"
    
    def detect_direction(self):
        """Detect text direction based on content"""
        try:
            # Check if text contains Persian/Arabic characters
            if any('\u0600' <= c <= '\u06FF' for c in self.original_text):
                return 'rtl'
            elif detect(self.original_text) in ['fa', 'ar']:
                return 'rtl'
            return 'ltr'
        except:
            return 'rtl'

    def detect_translated_direction(self):
        """Detect translated text direction"""
        try:
            if self.translated_text:
                if any('\u0600' <= c <= '\u06FF' for c in self.translated_text):
                    return 'rtl'
                elif detect(self.translated_text) in ['fa', 'ar']:
                    return 'rtl'
            return 'ltr'
        except:
            return 'ltr'