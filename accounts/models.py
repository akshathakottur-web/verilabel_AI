
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ('customer', 'Customer'),
        ('inspector', 'Inspector'),
        ('admin', 'Admin'),
    ]

    # The sign-in ID is stored in the built-in "username" field.
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')

    REQUIRED_FIELDS = ['name', 'role']

    def __str__(self):
        return f'{self.username} ({self.role})'
