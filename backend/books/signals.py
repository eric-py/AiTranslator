from django.db.models.signals import post_save, post_delete, pre_delete
from django.dispatch import receiver
from django.db.models import F
from django.utils import timezone

from datetime import timedelta

from extensions.send_mail import EmailService
from dashboard.models import UserStats

from .models import Book, Page


@receiver([post_save], sender=Book)
def update_stats_on_book_create(sender, instance, created, **kwargs):
    """Update user stats when a book is created"""
    if created:
        stats, _ = UserStats.objects.get_or_create(user=instance.user)
        stats.total_books = F('total_books') + 1
        stats.total_pages = F('total_pages') + instance.total_pages
        
        # Update monthly books
        if instance.created_at.month == timezone.now().month:
            stats.monthly_books = F('monthly_books') + 1
        
        stats.save()

@receiver([post_save], sender=Page)
def update_stats_on_page_translate(sender, instance, created, **kwargs):
    """Update user stats when a page is translated"""
    # Only update if page is translated and saved (not created)
    if not created and instance.translated_text and instance.is_translated:
        stats, _ = UserStats.objects.get_or_create(user=instance.book.user)
        
        # Use F() for atomic updates
        stats.total_translated_pages = F('total_translated_pages') + 1
        
        # Update weekly pages if book was created within last 7 days
        if instance.book.created_at >= timezone.now() - timedelta(days=7):
            stats.weekly_pages = F('weekly_pages') + 1
        
        stats.save()
        
        # Refresh from database to get actual values
        stats.refresh_from_db()

@receiver([post_delete], sender=Book)
def update_stats_on_book_delete(sender, instance, **kwargs):
    """Update user stats when a book is deleted"""
    try:
        stats = UserStats.objects.get(user=instance.user)
        stats.total_books = F('total_books') - 1
        stats.total_pages = F('total_pages') - instance.total_pages
        
        # Update translated pages
        translated_pages = instance.pages.filter(is_translated=True).count()
        if translated_pages > 0:
            stats.total_translated_pages = F('total_translated_pages') - translated_pages
            
        # Update monthly books if deleted in same month
        if instance.created_at.month == timezone.now().month:
            stats.monthly_books = F('monthly_books') - 1
            
        stats.save()
    except UserStats.DoesNotExist:
        pass

@receiver(pre_delete, sender=Book)
def delete_book_files(sender, instance, **kwargs):
    """Delete associated files when book is deleted"""
    try:
        # Delete PDF file
        if instance.file:
            instance.file.delete(save=False)
        # Delete cover image
        if instance.cover:
            instance.cover.delete(save=False)
    except Exception as e:
        print(f"Error deleting files for book {instance.id}: {str(e)}")

@receiver(post_save, sender=Book)
def notify_user_on_book_status_change(sender, instance, created, **kwargs):
    """Send email notifications on book status changes"""
    if not created and instance.user.email:  # Only for status updates, not new books
        status = instance.status
        template_map = {
            'ready_for_translation': 'book_extraction_success',
            'extraction_failed': 'book_extraction_failed',
            'completed': 'book_translation_completed',
            'translation_failed': 'book_translation_failed',
        }
        
        if status in template_map:
            EmailService.send_book_status_email(
                user=instance.user,
                book=instance,
                template_name=template_map[status]
            )