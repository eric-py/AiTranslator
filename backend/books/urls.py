from django.urls import path
from . import views

app_name = 'books'

urlpatterns = [
    # Book URLs
    path('', views.book_list, name='list'),

    # Upload URLs
    path('upload/', views.upload, name='upload'),
    
    # Delete URLs
    path('delete/<int:pk>/', views.BookDeleteView.as_view(), name='delete'),
    
    # Detail URLs
    path('translate/<int:pk>/', views.book_detail, name='translate'),
    path('page-image/<int:pk>/<int:page_number>/', views.get_page_image, name='page_image'), # AJAX

    # Download URLs
    path('download/<int:pk>/', views.download, name='download'),
    path('download/<int:pk>/original/docx/', views.download_original_docx, name='download_original_docx'),
    path('download/<int:pk>/translation/docx/', views.download_translation_docx, name='download_translation_docx'),
    path('download/<int:pk>/all/', views.download_all, name='download_all'),

    # Single Page opetations URLs (AJAX)
    path('retry-extraction/<int:pk>/', views.retry_extraction, name='retry_extraction'),
    path('retry-translation/<int:pk>/', views.retry_translation, name='retry_translation'),
    path('retry-page-translation/<int:pk>/<int:page_number>/', views.retry_page_translation, name='retry_page_translation'),
    path('retry-page-extraction/<int:pk>/<int:page_number>/', views.retry_page_extraction, name='retry_page_extraction'),
]