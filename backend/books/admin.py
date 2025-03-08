from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse

from .models import Book, Page

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    """Book admin"""
    list_display = ['title', 'user_link', 'cover_preview', 'total_pages', 'translated_pages', 'status_badge', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['title', 'user__username', 'user__email']
    readonly_fields = ['cover_preview', 'file_preview', 'last_activity']
    list_per_page = 25
    
    def cover_preview(self, obj):
        if obj.cover:
            return format_html('<img src="{}" width="50" height="70" style="object-fit: cover; border-radius: 5px;" />', obj.cover.url)
        return "بدون تصویر"
    cover_preview.short_description = 'کاور'

    def user_link(self, obj):
        url = reverse("admin:account_user_change", args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'کاربر'

    def status_badge(self, obj):
        colors = {
            'pending': '#FFA500',
            'processing': '#3498db',
            'extraction_failed': '#e74c3c',
            'ready_for_translation': '#2ecc71',
            'translating': '#9b59b6',
            'translation_failed': '#c0392b',
            'completed': '#27ae60',
            'failed': '#e74c3c'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            colors.get(obj.status, '#777'),
            obj.get_status_display()
        )
    status_badge.short_description = 'وضعیت'

@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    """Page admin"""
    list_display = ['book_link', 'number', 'translation_status', 'get_updated_at']
    list_filter = ['is_translated', 'book__status']
    search_fields = ['book__title', 'original_text', 'translated_text']
    readonly_fields = ['get_updated_at']
    list_per_page = 50

    def book_link(self, obj):
        url = reverse("admin:books_book_change", args=[obj.book.id])
        return format_html('<a href="{}">{}</a>', url, obj.book.title)
    book_link.short_description = 'کتاب'

    def get_updated_at(self, obj):
        return obj.updated_at
    get_updated_at.short_description = 'آخرین بروزرسانی'
    get_updated_at.admin_order_field = 'updated_at'

    def translation_status(self, obj):
        if obj.is_translated:
            return format_html(
                '<span style="background-color: #27ae60; color: white; padding: 3px 10px; border-radius: 3px;">ترجمه شده</span>'
            )
        return format_html(
            '<span style="background-color: #e74c3c; color: white; padding: 3px 10px; border-radius: 3px;">ترجمه نشده</span>'
        )
    translation_status.short_description = 'وضعیت ترجمه'