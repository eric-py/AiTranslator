from django.conf import settings
from django.utils import timezone
from celery import shared_task
from books.models import Book, Page
from .services import GeminiService
from billiard.exceptions import TimeLimitExceeded

import fitz, time

@shared_task(bind=True, queue='default')
def process_pdf_pages(self, book_id, start_page=None, single_page=False):
    """Process PDF pages one by one"""
    print(f"Starting PDF processing for book {book_id}")
    try:
        book = Book.objects.get(id=book_id)
        user_queue = 'users'
        print(f"Processing in queue {user_queue}")
        self.request.delivery_info['routing_key'] = 'users.tasks'
        
        if not single_page:
            book.status = 'processing'
            book.save()

        pdf_document = fitz.open(book.file.path)
        total_pages = len(pdf_document)
        gemini = GeminiService()

        start_from = start_page if start_page is not None else book.last_processed_page
        consecutive_failures = 0
        last_successful_page = None
        extraction_failed = False
        
        # Filter pages based on single_page mode
        page_range = [start_from] if single_page else range(start_from, total_pages)
        
        for page_num in page_range:
            try:
                print(f"\nProcessing page {page_num + 1}/{total_pages} for user {book.user.id}")
                
                # Update last activity timestamp
                book.save()
                
                # Check if page already exists
                existing_page = Page.objects.filter(book=book, number=page_num + 1).first()
                if existing_page:
                    if single_page:
                        # For single page, delete existing page to re-extract
                        existing_page.delete()
                        print(f"Deleted existing page {page_num + 1} for re-extraction")
                    else:
                        print(f"Page {page_num + 1} already exists, skipping...")
                        last_successful_page = page_num + 1
                        consecutive_failures = 0
                        continue

                page = pdf_document[page_num]
                pix = page.get_pixmap()
                img_data = pix.tobytes("png")
                
                extracted_text = gemini.extract_text_from_image(img_data)
                
                if extracted_text is None:
                    consecutive_failures += 1
                    print(f"Extraction failed for page {page_num + 1}")
                    
                    if single_page:
                        print("Single page extraction failed")
                        extraction_failed = True
                        break
                    
                    if consecutive_failures >= 3:
                        print("Three consecutive failures detected. Stopping extraction.")
                        book.status = 'extraction_failed'
                        if last_successful_page:
                            book.last_processed_page = last_successful_page
                        book.save()
                        pdf_document.close()
                        return
                    continue

                # Valid text check
                if extracted_text and len(extracted_text.strip()) > 50:
                    Page.objects.create(
                        book=book,
                        number=page_num + 1,
                        original_text=extracted_text,
                    )
                    book.last_processed_page = page_num + 1
                    last_successful_page = page_num + 1
                    book.save()
                    print(f"Successfully extracted text from page {page_num + 1}")
                    consecutive_failures = 0
                else:
                    consecutive_failures += 1
                    print(f"Invalid text extracted from page {page_num + 1}")
                    
                    if single_page:
                        print("Single page extraction failed")
                        extraction_failed = True
                        break
                    
                    if consecutive_failures >= 3:
                        print("Three consecutive failures detected. Stopping extraction.")
                        book.status = 'extraction_failed'
                        if last_successful_page:
                            book.last_processed_page = last_successful_page
                        book.save()
                        pdf_document.close()
                        return
                    continue

                time.sleep(1)

            except Exception as e:
                consecutive_failures += 1
                print(f"Error processing page {page_num + 1}: {str(e)}")
                
                if single_page:
                    print("Single page extraction failed")
                    extraction_failed = True
                    break
                
                if consecutive_failures >= 3:
                    print("Three consecutive failures detected. Stopping extraction.")
                    book.status = 'extraction_failed'
                    if last_successful_page:
                        book.last_processed_page = last_successful_page
                    book.save()
                    pdf_document.close()
                    return
                continue

        pdf_document.close()
        
        if single_page:
            if extraction_failed:
                book.status = 'extraction_failed'
            book.save()
        else:
            if book.last_processed_page > 0:
                book.status = 'ready_for_translation'
                book.save()
                translate_book.apply_async(args=[book.id], queue=user_queue)
            else:
                book.status = 'extraction_failed'
                book.save()

    except TimeLimitExceeded as e:
        print(f"Time limit exceeded: {str(e)}")
        if book:
            book.status = 'extraction_failed'
            if last_successful_page:
                book.last_processed_page = last_successful_page
            book.save()
        raise e

    except Exception as e:
        print(f"Error processing PDF: {str(e)}")
        if book:
            book.status = 'failed'
            if last_successful_page:
                book.last_processed_page = last_successful_page
            book.save()
        raise e

@shared_task(bind=True, queue='default')
def translate_book(self, book_id, start_page=None, single_page=False):
    """Translate book pages one by one"""
    book = None
    try:
        book = Book.objects.get(id=book_id)
        user_queue = 'users'
        self.request.delivery_info['routing_key'] = 'users.tasks'
        
        if not single_page:
            book.status = 'translating'
            book.save()

        gemini = GeminiService()
        pages = book.pages.all().order_by('number')
        consecutive_failures = 0
        last_successful_page = None
        translation_failed = False
        
        if start_page is not None:
            pages = pages.filter(number__gte=start_page)
            if single_page:
                pages = pages[:1]
        else:
            pages = pages.filter(is_translated=False)

        for page in pages:
            try:
                print(f"\nTranslating page {page.number} for user {book.user.id}")
                
                # Update last activity timestamp
                book.save()
                
                translated_text = gemini.translate_text(page.original_text)
                
                if translated_text is None:
                    consecutive_failures += 1
                    print(f"Translation failed for page {page.number}")
                    
                    if single_page:
                        print("Single page translation failed")
                        translation_failed = True
                        break
                    
                    if consecutive_failures >= 3:
                        print("Three consecutive failures detected. Stopping translation.")
                        book.status = 'translation_failed'
                        book.last_processed_page = last_successful_page if last_successful_page else (start_page - 1 if start_page else 0)
                        book.save()
                        return
                    continue

                # Valid translation check
                if translated_text and len(translated_text.strip()) > 50:
                    page.translated_text = translated_text
                    page.is_translated = True
                    page.save()
                    
                    if not single_page:
                        book.translated_pages = book.pages.filter(is_translated=True).count()
                        book.save()
                    
                    print(f"Successfully translated page {page.number}")
                    consecutive_failures = 0
                    last_successful_page = page.number
                else:
                    consecutive_failures += 1
                    print(f"Invalid translation for page {page.number}")
                    
                    if single_page:
                        print("Single page translation failed")
                        translation_failed = True
                        break
                    
                    if consecutive_failures >= 3:
                        print("Three consecutive failures detected. Stopping translation.")
                        book.status = 'translation_failed'
                        book.last_processed_page = last_successful_page if last_successful_page else (start_page - 1 if start_page else 0)
                        book.save()
                        return
                    continue

                time.sleep(1)

            except Exception as e:
                consecutive_failures += 1
                print(f"Error translating page {page.number}: {str(e)}")
                
                if single_page:
                    print("Single page translation failed")
                    translation_failed = True
                    break
                
                if consecutive_failures >= 3:
                    print("Three consecutive failures detected. Stopping translation.")
                    book.status = 'translation_failed'
                    book.last_processed_page = last_successful_page if last_successful_page else (start_page - 1 if start_page else 0)
                    book.save()
                    return
                continue

        # Final status update
        if single_page:
            if translation_failed:
                book.status = 'translation_failed'
            book.save()
        else:
            if book.translated_pages > 0:
                book.status = 'completed' if book.translated_pages == book.total_pages else 'translation_failed'
            else:
                book.status = 'translation_failed'
            book.save()

    except TimeLimitExceeded as e:
        print(f"Time limit exceeded: {str(e)}")
        if book:
            print(f"Saving progress before timeout. Last successful page: {last_successful_page}")
            book.status = 'translation_failed'
            if last_successful_page:
                book.last_processed_page = last_successful_page
            book.save()
        raise e

    except Exception as e:
        print(f"Error translating book: {str(e)}")
        if book:
            book.status = 'translation_failed'
            if last_successful_page:
                book.last_processed_page = last_successful_page
            book.save()
        raise e

    finally:
        if book and not single_page and book.status not in ['completed', 'translation_failed']:
            book.status = 'translation_failed'
            if last_successful_page:
                book.last_processed_page = last_successful_page
            book.save()
            
@shared_task
def check_stuck_books():
    """Check for books stuck in processing/translating state"""
    try:
        # Get books in processing or translating state
        stuck_books = Book.objects.filter(
            status__in=['processing', 'translating']
        )
        
        for book in stuck_books:
            if book.is_stuck():
                # Update book status based on current state
                if book.status == 'processing':
                    book.status = 'extraction_failed'
                else:
                    book.status = 'translation_failed'
                
                print(f"Book {book.id} was stuck in {book.status} state for more than 2 hours. Marking as failed.")
                book.save()
                
    except Exception as e:
        print(f"Error checking stuck books: {str(e)}")