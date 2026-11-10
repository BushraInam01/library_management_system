import re

from django import forms
from .models import Book


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
        isbn = isbn.replace('-', '').replace(' ', '').upper()

        if not re.fullmatch(r'(?:\d{9}[\dX]|\d{13})', isbn):
            raise forms.ValidationError(
                'Enter a valid ISBN-10 or ISBN-13 number.'
            )

        return isbn



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
            'available_copies',
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
            'available_copies': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
            }),
        }