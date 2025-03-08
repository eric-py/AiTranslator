from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

class EmailService:
    @staticmethod
    def send_book_status_email(user, book, template_name):
        """Send email about book status changes"""
        subject = {
            'ready_for_translation': 'استخراج متن کتاب با موفقیت انجام شد',
            'extraction_failed': 'خطا در استخراج متن کتاب',
            'completed': 'ترجمه کتاب با موفقیت انجام شد',
            'translation_failed': 'خطا در ترجمه کتاب',
        }.get(book.status, 'بروزرسانی وضعیت کتاب')

        context = {
            'user': user,
            'book': book,
            'site_url': settings.SITE_URL,
        }

        html_message = render_to_string(f'emails/{template_name}.html', context)
        
        send_mail(
            subject=subject,
            message='',
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
            html_message=html_message
        )