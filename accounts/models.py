from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


class VerilabelUserManager(UserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        # A superuser is always an Admin, whatever else was typed.
        extra_fields['role'] = 'admin'
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    ROLE_CHOICES = [
        ('customer', 'Customer'),
        ('inspector', 'Inspector'),
        ('admin', 'Admin'),
    ]

    # The sign-in ID is stored in the built-in "username" field.
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')

    objects = VerilabelUserManager()

    REQUIRED_FIELDS = ['name']

    def __str__(self):
        return f'{self.username} ({self.role})'