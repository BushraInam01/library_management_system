from uuid import uuid4

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    class Role(models.TextChoices):
        MEMBER = 'MEMBER', 'Member'
        LIBRARIAN = 'LIBRARIAN', 'Librarian'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.MEMBER,
    )

    def __str__(self):
        return self.username


class LibraryCard(models.Model):

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='library_card',
    )

    card_number = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
    )

    issued_at = models.DateTimeField(auto_now_add=True)

    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.card_number:
            self.card_number = f'LIB-{uuid4().hex[:12].upper()}'

        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.card_number} - {self.user.username}'