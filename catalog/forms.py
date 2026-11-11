
import re

from django import forms
from .models import Book


def normalize_and_validate_isbn(isbn):
    """
    Normalize ISBN and validate ISBN-10 or ISBN-13 format.
    """
    isbn = isbn.replace('-', '').replace(' ', '').upper()

    if not re.fullmatch(r'(?:\d{9}[\dX]|\d{13})', isbn):
        raise forms.ValidationError(
            'Enter a valid ISBN-10 or ISBN-13 number.'
        )

    return isbn


class ISBNLookupForm(forms.Form):
    isbn = forms.CharField(
        max_length=17,
        label='ISBN Number',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter ISBN-10 or ISBN-13',
        })
    )

    def clean_isbn(self):
        isbn = self.cleaned_data['isbn']
        return normalize_and_validate_isbn(isbn)


class BookForm(forms.ModelForm):

    class Meta:
        model = Book

        fields = [
            'title',
            'author',
            'isbn',
            'publisher',
            'publication_year',
            'description',
            'total_copies',
        ]

        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'author': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'isbn': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'publisher': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'publication_year': forms.NumberInput(attrs={
                'class': 'form-control',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
            }),
            'total_copies': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
            }),
        }

    def clean_isbn(self):
        isbn = self.cleaned_data['isbn']
        return normalize_and_validate_isbn(isbn)

    def save(self, commit=True):
        book = super().save(commit=False)

        # A new book starts with every copy available.
        if book.pk is None:
            book.available_copies = book.total_copies

        if commit:
            book.save()

        return book
