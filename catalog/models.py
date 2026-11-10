from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class Book(models.Model):

    title = models.CharField(
        max_length=250
    )

    author = models.CharField(
        max_length=200
    )

    isbn = models.CharField(
        max_length=17,
        unique=True,
        help_text='Enter ISBN-10 or ISBN-13.'
    )

    publisher = models.CharField(
        max_length=200,
        blank=True
    )

    publication_year = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    description = models.TextField(
        blank=True
    )

    total_copies = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )

    available_copies = models.PositiveIntegerField(
        default=1
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ['title']
        verbose_name = 'Book'
        verbose_name_plural = 'Books'

    def clean(self):
        super().clean()

        if self.available_copies > self.total_copies:
            raise ValidationError({
                'available_copies': (
                    'Available copies cannot be greater than total copies.'
                )
            })

    def __str__(self):
        return f'{self.title} by {self.author}'
