
from unittest import mock

import requests
import tablib

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from borrowing.models import BorrowRecord

from .admin import BookAdminForm
from .forms import BookForm
from .models import Book
from .resources import BookResource
from .services import adjust_book_copies


User = get_user_model()

HEADERS = [
    'isbn',
    'title',
    'author',
    'publisher',
    'publication_year',
    'description',
    'total_copies',
]


def dataset(*rows):
    return tablib.Dataset(*rows, headers=HEADERS)


class BookCsvImportTests(TestCase):

    def test_new_books_start_fully_available(self):
        result = BookResource().import_data(
            dataset([
                '978-0-306-40615-7',
                'Imported',
                'Author',
                '',
                '',
                '',
                '4',
            ]),
            raise_errors=True,
        )

        self.assertFalse(result.has_errors())

        book = Book.objects.get(isbn='9780306406157')

        self.assertEqual(
            (book.total_copies, book.available_copies),
            (4, 4),
        )

    def test_reimport_updates_by_isbn_and_shifts_available(self):
        book = Book.objects.create(
            title='Old',
            author='A',
            isbn='9780306406157',
            total_copies=3,
            available_copies=1,
        )

        user1 = User.objects.create_user(
            username='member_one',
            password='pass12345!',
        )

        user2 = User.objects.create_user(
            username='member_two',
            password='pass12345!',
        )

        BorrowRecord.objects.create(
            user=user1,
            book=book,
        )

        BorrowRecord.objects.create(
            user=user2,
            book=book,
        )

        BookResource().import_data(
            dataset([
                '9780306406157',
                'New Title',
                'A',
                '',
                '',
                '',
                '5',
            ]),
            raise_errors=True,
        )

        book.refresh_from_db()

        self.assertEqual(Book.objects.count(), 1)
        self.assertEqual(book.title, 'New Title')
        self.assertEqual(book.total_copies, 5)
        self.assertEqual(book.available_copies, 3)

    def test_invalid_total_copies_is_reported_as_row_error(self):
        result = BookResource().import_data(
            dataset([
                '9780306406157',
                'Bad',
                'A',
                '',
                '',
                '',
                '0',
            ]),
        )

        self.assertTrue(result.has_errors())
        self.assertEqual(Book.objects.count(), 0)

    def test_import_refuses_total_below_borrowed_copies(self):
        book = Book.objects.create(
            title='Borrowed Book',
            author='Author',
            isbn='9780306406157',
            total_copies=3,
            available_copies=1,
        )

        user1 = User.objects.create_user(
            username='borrower_one',
            password='pass12345!',
        )

        user2 = User.objects.create_user(
            username='borrower_two',
            password='pass12345!',
        )

        BorrowRecord.objects.create(user=user1, book=book)
        BorrowRecord.objects.create(user=user2, book=book)

        result = BookResource().import_data(
            dataset([
                '9780306406157',
                'Borrowed Book',
                'Author',
                '',
                '',
                '',
                '1',
            ]),
        )

        book.refresh_from_db()

        self.assertTrue(result.has_errors())
        self.assertEqual(book.total_copies, 3)
        self.assertEqual(book.available_copies, 1)

    def test_admin_changelist_offers_import(self):
        admin_user = User.objects.create_superuser(
            'boss',
            'b@example.com',
            'pass12345!',
        )

        self.client.force_login(admin_user)

        response = self.client.get(
            reverse('admin:catalog_book_changelist')
        )

        self.assertContains(response, 'import')


class BookCopyAdjustmentTests(TestCase):

    def test_cannot_reduce_total_below_active_borrows(self):
        book = Book.objects.create(
            title='Test Book',
            author='Author',
            isbn='9780306406157',
            total_copies=3,
            available_copies=1,
        )

        user1 = User.objects.create_user(
            username='copy_user_one',
            password='pass12345!',
        )

        user2 = User.objects.create_user(
            username='copy_user_two',
            password='pass12345!',
        )

        BorrowRecord.objects.create(user=user1, book=book)
        BorrowRecord.objects.create(user=user2, book=book)

        # Service raises ValueError when requested copies
        # are fewer than currently borrowed/reserved copies.
        with self.assertRaises(ValueError):
            adjust_book_copies(book, 1)

        book.refresh_from_db()

        self.assertEqual(book.total_copies, 3)
        self.assertEqual(book.available_copies, 1)


class ISBNFormValidationTests(TestCase):

    def test_admin_form_rejects_invalid_isbn(self):
        form = BookAdminForm(data={
            'title': 'Test Book',
            'author': 'Test Author',
            'isbn': 'hello',
            'publisher': '',
            'publication_year': '',
            'description': '',
            'total_copies': '1',
            'available_copies': '0',
        })

        self.assertFalse(form.is_valid())
        self.assertIn('isbn', form.errors)

    def test_admin_form_normalizes_isbn(self):
        form = BookAdminForm(data={
            'title': 'Test Book',
            'author': 'Test Author',
            'isbn': '978-0-306-40615-7',
            'publisher': '',
            'publication_year': '',
            'description': '',
            'total_copies': '1',
            'available_copies': '0',
        })

        self.assertTrue(form.is_valid(), form.errors)

        self.assertEqual(
            form.cleaned_data['isbn'],
            '9780306406157',
        )

    def test_website_book_form_rejects_invalid_isbn(self):
        form = BookForm(data={
            'title': 'Test Book',
            'author': 'Test Author',
            'isbn': 'hello',
            'publisher': '',
            'publication_year': '',
            'description': '',
            'total_copies': '1',
        })

        self.assertFalse(form.is_valid())
        self.assertIn('isbn', form.errors)


class ISBNLookupErrorTests(TestCase):

    def setUp(self):
        cache.clear()

        self.librarian = User.objects.create_user(
            username='lib',
            password='pass12345!',
            role=User.Role.LIBRARIAN,
        )

        self.client.force_login(self.librarian)

    def _lookup(self, side_effect):
        with mock.patch(
            'catalog.views.requests.get',
            side_effect=side_effect,
        ):
            return self.client.post(
                reverse('catalog:isbn_lookup'),
                {'isbn': '9780306406157'},
            )

    def test_unknown_isbn_says_not_found_not_connection_error(self):
        response_404 = requests.Response()
        response_404.status_code = 404

        error = requests.HTTPError(response=response_404)

        response = self._lookup(error)

        self.assertContains(
            response,
            'No book information was found',
        )

        self.assertNotContains(
            response,
            'Unable to connect',
        )

    def test_empty_title_result_is_not_cached(self):
        ok = mock.Mock()
        ok.raise_for_status.return_value = None
        ok.json.return_value = {
            'title': '',
            'authors': [],
        }

        self._lookup([ok])

        self.assertIsNone(
            cache.get('openlibrary_isbn_9780306406157')
        )
