from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import JsonResponse, Http404,FileResponse
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.views.generic.edit import DeleteView
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django.conf import settings

from .models import Book, Page

from extensions.utils import create_word_document, create_zip_archive
from translator.tasks import process_pdf_pages, translate_book

import tempfile, fitz, os



@login_required
def book_list(request):
    """View for showing all books of the user"""
    books = Book.objects.filter(user=request.user).select_related('user')
    
    context = {
        'title': 'کتاب‌های من',
        'active': 'books',
        'books': books,
    }
    return render(request, 'books/books.html', context)

@login_required
def upload(request):
    """View for uploading and processing a new book"""
    if request.method != 'POST':
        messages.error(request, 'درخواست نامعتبر')
        return redirect('dashboard:dashboard')

    if 'file' not in request.FILES:
        messages.error(request, 'لطفا یک فایل انتخاب کنید')
        return redirect('dashboard:dashboard')

    uploaded_file = request.FILES['file']
    book = None
    
    try:
        # Check file extension
        if not uploaded_file.name.lower().endswith('.pdf'):
            messages.error(request, 'فقط فایل PDF پشتیبانی می‌شود')
            return redirect('dashboard:dashboard')

        # Create book instance
        book = Book.objects.create(
            user=request.user,
            title=os.path.splitext(uploaded_file.name)[0],
            status='pending'
        )

        # Save uploaded file
        file_name = f"{book.id}_{uploaded_file.name}"
        file_path = os.path.join('books/files', file_name)
        book.file.save(file_name, uploaded_file)

        # Get PDF info and create cover
        pdf_document = fitz.open(book.file.path)
        book.total_pages = len(pdf_document)

        # Generate and save cover image
        first_page = pdf_document[0]
        pix = first_page.get_pixmap(matrix=fitz.Matrix(2, 2))
        
        # Save cover image
        cover_name = f"{book.id}_cover.png"
        cover_path = os.path.join('books/covers', cover_name)
        cover_full_path = os.path.join(settings.MEDIA_ROOT, cover_path)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(cover_full_path), exist_ok=True)
        
        # Save the cover image
        pix.save(cover_full_path)
        book.cover = cover_path
        
        # Close PDF and save changes
        pdf_document.close()
        book.save()
        
       # Start PDF processing task
        task = process_pdf_pages.apply_async(
            kwargs={'book_id': book.id},
            queue='users',
            routing_key='users.tasks'
        )
        print(f"Task scheduled: {task.id} in queue users")
        
        messages.success(request, 'کتاب با موفقیت آپلود شد')
        return JsonResponse({
            'status': 'success',
            'message': 'کتاب با موفقیت آپلود شد',
            'redirect_url': reverse('books:list')
        })

    except Exception as e:
        print(f"Error uploading file: {str(e)}")
        messages.error(request, 'خطا در آپلود فایل')
        if book and book.id:
            # Cleanup on error
            if book.file:
                book.file.delete(save=False)
            if book.cover:
                try:
                    os.remove(os.path.join(settings.MEDIA_ROOT, book.cover.path))
                except:
                    pass
            book.delete()
        return redirect('dashboard:dashboard')

class BookDeleteView(UserPassesTestMixin, DeleteView):
    """
    Delete a pdf (data and files)
    """
    model = Book
    success_url = reverse_lazy('books:list')
    template_name = 'books/book_confirm_delete.html'
    
    def test_func(self):
        """Check if user has permission to delete the book"""
        book = self.get_object()
        return self.request.user.is_superuser or book.user == self.request.user

    def handle_no_permission(self):
        raise Http404("شما اجازه دسترسی به این صفحه را ندارید")

    def delete(self, request, *args, **kwargs):
        """Override delete to clean up files"""
        book = self.get_object()
        try:
            # Delete PDF file
            if book.file:
                book.file.delete(save=False)
            # Delete cover image
            if book.cover:
                book.cover.delete(save=False)
            # Delete the book (this will trigger signals)
            response = super().delete(request, *args, **kwargs)
            messages.success(request, 'کتاب با موفقیت حذف شد')
            return response
        except Exception as e:
            messages.error(request, 'خطا در حذف کتاب')
            return redirect('books:list')

@login_required 
def book_detail(request, pk):
    """View for showing details of a book"""
    try:
        book = Book.objects.filter(user=request.user).select_related('user').get(pk=pk)

        if not (request.user.is_superuser or request.user == book.user):
            raise Http404("شما اجازه دسترسی به این صفحه را ندارید")
        
        # Get page number from GET parameters
        page_number = request.GET.get('page', 1)
        try:
            page_number = int(page_number)
            if page_number < 1:
                page_number = 1
            elif page_number > book.total_pages:
                page_number = book.total_pages
        except ValueError:
            page_number = 1

        # Calculate reading progress for current page
        if page_number == book.total_pages:
            page_progress = 100
        else:
            page_progress = (page_number / book.total_pages) * 100
        
        # Get all pages for this book and filter by page number
        pages = book.pages.all()
        current_page = pages.filter(number=page_number).first()
        
        # Handle case where page doesn't exist yet
        if not current_page:
            context = {
                'number': page_number,
                'original_text': 'صفحه در حال پردازش است...',
                'translated_text': 'لطفا صبر کنید...',
                'is_translated': False,
                'original_direction': 'rtl',
                'translated_direction': 'ltr'
            }
        else:
            context = {
                'number': current_page.number,
                'original_text': current_page.original_text,
                'translated_text': current_page.translated_text,
                'is_translated': current_page.is_translated,
                'original_direction': current_page.detect_direction(),
                'translated_direction': current_page.detect_translated_direction()
            }

        return render(request, 'books/translator.html', {
            'title': book.title,
            'active': 'books',
            'book': book,
            'current_page': context,
            'page_number': page_number,
            'total_pages': book.total_pages,
            'has_next': page_number < book.total_pages,
            'has_previous': page_number > 1,
            'next_page': page_number + 1 if page_number < book.total_pages else None,
            'previous_page': page_number - 1 if page_number > 1 else None,
            'page_progress': round(page_progress, 1)
        })
        
    except Book.DoesNotExist:
        raise Http404("کتاب مورد نظر یافت نشد")
    
@login_required
def get_page_image(request, pk, page_number):
    """Export a page as an image"""
    try:
        book = Book.objects.get(pk=pk, user=request.user)
        
        pdf_document = fitz.open(book.file.path)
        
        if 1 <= page_number <= len(pdf_document):
            page = pdf_document[page_number - 1]
            
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                pix.save(tmp.name)
                tmp.seek(0)
                response = FileResponse(open(tmp.name, 'rb'), content_type='image/png')
                
            pdf_document.close()
            return response
            
        pdf_document.close()
        raise Http404("صفحه مورد نظر یافت نشد")
        
    except Book.DoesNotExist:
        raise Http404("کتاب مورد نظر یافت نشد")
    
@login_required
def download(request, pk):
    """
    Download as pdf or word or txt or in general both for the original text and for translation
    """

    book = Book.objects.filter(user=request.user).select_related('user').get(pk=pk)

    if not (request.user.is_superuser or request.user == book.user) or book.status != 'completed':
        raise Http404("شما اجازه دسترسی به این صفحه را ندارید")

    context = {
        'book': book
    }
    return render(request, 'books/download.html', context)

@login_required
def download_original_docx(request, pk):
    """Download the original text as a docx file"""
    book = get_object_or_404(Book, pk=pk, user=request.user, status='completed')
    pages = book.pages.all().order_by('number')
    tmp_path = create_word_document(pages, is_translation=False)
    return FileResponse(
        open(tmp_path, 'rb'),
        as_attachment=True,
        filename=f"{book.title}_original.docx"
    )

@login_required
def download_translation_docx(request, pk):
    """Download the translated text as a docx file"""
    book = get_object_or_404(Book, pk=pk, user=request.user, status='completed')
    pages = book.pages.all().order_by('number')
    tmp_path = create_word_document(pages, is_translation=True)
    return FileResponse(
        open(tmp_path, 'rb'),
        as_attachment=True,
        filename=f"{book.title}_translation.docx"
    )

@login_required
def download_all(request, pk):
    """Download all files (pdf, docx, txt) as a zip file"""
    book = get_object_or_404(Book, pk=pk, user=request.user, status='completed')
    tmp_path = create_zip_archive(book)
    return FileResponse(
        open(tmp_path, 'rb'),
        as_attachment=True,
        filename=f"{book.title}_all_files.zip"
    )

@login_required
def retry_extraction(request, pk):
    """Retry failed text extraction"""
    book = get_object_or_404(Book, pk=pk, user=request.user)
    
    if book.status in ['extraction_failed', 'failed']:
        process_pdf_pages.apply_async(
            kwargs={
                'book_id': book.id,
                'start_page': book.last_processed_page
            },
            queue='users',
            routing_key='users.tasks'
        )
        messages.success(request, 'پردازش مجدد آغاز شد')
    
    return redirect('books:translate', pk=pk)

@login_required
def retry_translation(request, pk):
    """Retry failed translation"""
    book = get_object_or_404(Book, pk=pk, user=request.user)
    
    if book.status in ['translation_failed', 'failed']:
        translate_book.apply_async(
            kwargs={'book_id': book.id},
            queue='users',
            routing_key='users.tasks'
        )
        messages.success(request, 'ترجمه مجدد آغاز شد')
    
    return redirect('books:translate', pk=pk)

@login_required
def retry_page_translation(request, pk, page_number):
    """Retry translation for a specific page"""
    book = get_object_or_404(Book, pk=pk, user=request.user)
    page = get_object_or_404(Page, book=book, number=page_number)
    
    try:
        translate_book.apply_async(
            kwargs={
                'book_id': book.id,
                'start_page': page_number,
                'single_page': True
            },
            queue='users',
            routing_key='users.tasks'
        )
        messages.success(request, f'ترجمه مجدد صفحه {page_number} آغاز شد')
    except Exception as e:
        messages.error(request, 'خطا در شروع ترجمه مجدد')
    
    return redirect(f'{reverse("books:translate", kwargs={"pk": pk})}?page={page_number}')

@login_required
def retry_page_extraction(request, pk, page_number):
    """Retry extraction for a specific page"""
    book = get_object_or_404(Book, pk=pk, user=request.user)
    
    try:
        process_pdf_pages.apply_async(
            kwargs={
                'book_id': book.id,
                'start_page': page_number - 1,
                'single_page': True
            },
            queue='users',
            routing_key='users.tasks'
        )
        messages.success(request, f'استخراج مجدد صفحه {page_number} آغاز شد')
    except Exception as e:
        messages.error(request, 'خطا در شروع استخراج مجدد')
    
    return redirect(f'{reverse("books:translate", kwargs={"pk": pk})}?page={page_number}')