from django.apps import AppConfig


class BooksConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'books'
    verbose_name = 'کتاب'
    verbose_name_plural = 'کتاب ها'

    def ready(self):
        import books.signals