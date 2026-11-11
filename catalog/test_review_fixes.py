from unittest import mock

import requests
import tablib
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from borrowing.models import BorrowRecord

from .models import Book
from .resources import BookResource

User = get_user_model()

HEADERS = ['isbn', 'title', 'author', 'publisher', 'publication_year',
           'description', 'total_copies']


def dataset(*rows):
    return tablib.Dataset(*rows, headers=HEADERS)


class BookCsvImportTests(TestCase):

    def test_new_books_start_fully_available(self):
        result = BookResource().import_data(dataset(
            ['978-0-306-40615-7', 'Imported', 'Author', '', '', '', '4'],
        ), raise_errors=True)

        self.assertFalse(result.has_errors())
        book = Book.objects.get(isbn='9780306406157')
        self.assertEqual((book.total_copies, book.available_copies), (4, 4))

    def test_reimport_updates_by_isbn_and_shifts_available(self):
        book = Book.objects.create(
            title='Old',
            author='A',
            isbn='9780306406157',
            total_copies=3,
            available_copies=1,
        )

        # Create two actual active borrow records.
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
        result = BookResource().import_data(dataset(
            ['9780306406157', 'Bad', 'A', '', '', '', '0'],
        ))

        self.assertTrue(result.has_errors())
        self.assertEqual(Book.objects.count(), 0)

    def test_admin_changelist_offers_import(self):
        admin_user = User.objects.create_superuser('boss', 'b@example.com', 'pass12345!')
        self.client.force_login(admin_user)
        response = self.client.get(reverse('admin:catalog_book_changelist'))
        self.assertContains(response, 'import')


class ISBNLookupErrorTests(TestCase):

    def setUp(self):
        cache.clear()
        self.librarian = User.objects.create_user(
            username='lib', password='pass12345!', role=User.Role.LIBRARIAN,
        )
        self.client.force_login(self.librarian)

    def _lookup(self, side_effect):
        with mock.patch('catalog.views.requests.get', side_effect=side_effect):
            return self.client.post(
                reverse('catalog:isbn_lookup'), {'isbn': '9780306406157'}
            )

    def test_unknown_isbn_says_not_found_not_connection_error(self):
        response_404 = requests.Response()
        response_404.status_code = 404
        error = requests.HTTPError(response=response_404)

        response = self._lookup(error)

        self.assertContains(response, 'No book information was found')
        self.assertNotContains(response, 'Unable to connect')

    def test_empty_title_result_is_not_cached(self):
        ok = mock.Mock()
        ok.raise_for_status.return_value = None
        ok.json.return_value = {'title': '', 'authors': []}

        self._lookup([ok])

        self.assertIsNone(cache.get('openlibrary_isbn_9780306406157'))
