from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class User(AbstractUser):
    """
    Custom user model
    """
    email = models.EmailField(unique=True, verbose_name='ایمیل')

    def __str__(self):
        return self.email
    
    class Meta:
        verbose_name = 'کاربر'
        verbose_name_plural = 'کاربران'