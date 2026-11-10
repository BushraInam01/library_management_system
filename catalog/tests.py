
from datetime import date

from unittest.mock import Mock, patch

from django.test import TestCase
from django.urls import reverse
from django.core.cache import cache
from django.contrib.auth import get_user_model

from .models import Book
from .forms import ISBNLookupForm, BookForm

from borrowing.models import BorrowRecord
from reservations.models import Reservation


User = get_user_model()


class CatalogTestDataMixin:

    @classmethod
    def setUpTestData(cls):
        cls.member = User.objects.create_user(
            username='test_member',
            password='TestPassword123!',
            role=User.Role.MEMBER,
        )

        cls.librarian = User.objects.create_user(
            username='test_librarian',
            password='TestPassword123!',
            role=User.Role.LIBRARIAN,
        )

        cls.admin = User.objects.create_superuser(
            username='test_admin',
            email='admin@example.com',
            password='TestPassword123!',
        )

        cls.book = Book.objects.create(
            title='Python Testing',
            author='Test Author',
            isbn='9781234567890',
            publisher='Test Publisher',
            publication_year=2025,
            description='A book for testing.',
            total_copies=5,
            available_copies=5,
        )


class BookListViewTests(CatalogTestDataMixin, TestCase):

    def test_book_list_page_loads(self):
        response = self.client.get(
            reverse('catalog:book_list')
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Python Testing')

    def test_book_search_by_title(self):
        Book.objects.create(
            title='Django Development',
            author='Another Author',
            isbn='9781234567891',
        )

        response = self.client.get(
            reverse('catalog:book_list'),
            {'q': 'Django'}
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Django Development')
        self.assertNotContains(response, 'Python Testing')

    def test_book_search_by_author(self):
        response = self.client.get(
            reverse('catalog:book_list'),
            {'q': 'Test Author'}
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Python Testing')

    def test_book_search_by_isbn(self):
        response = self.client.get(
            reverse('catalog:book_list'),
            {'q': '9781234567890'}
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Python Testing')

    def test_book_list_pagination(self):
        for number in range(11):
            Book.objects.create(
                title=f'Extra Book {number}',
                author='Pagination Author',
                isbn=f'9781234567{number:03d}',
            )

        response = self.client.get(
            reverse('catalog:book_list')
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_paginated'])
        self.assertEqual(
            len(response.context['books']),
            10
        )


class BookDetailViewTests(CatalogTestDataMixin, TestCase):

    def test_book_detail_page_loads(self):
        response = self.client.get(
            reverse(
                'catalog:book_detail',
                kwargs={'pk': self.book.pk}
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context['book'],
            self.book
        )

    def test_member_ready_reservation_context(self):
        Reservation.objects.create(
            user=self.member,
            book=self.book,
            status=Reservation.Status.READY,
        )

        self.client.login(
            username='test_member',
            password='TestPassword123!',
        )

        response = self.client.get(
            reverse(
                'catalog:book_detail',
                kwargs={'pk': self.book.pk}
            )
        )

        self.assertTrue(response.context['ready_reservation'])
        self.assertFalse(response.context['active_borrowing'])

    def test_member_active_borrowing_context(self):
        BorrowRecord.objects.create(
            user=self.member,
            book=self.book,
            due_date=date.today(),
        )

        self.client.login(
            username='test_member',
            password='TestPassword123!',
        )

        response = self.client.get(
            reverse(
                'catalog:book_detail',
                kwargs={'pk': self.book.pk}
            )
        )

        self.assertTrue(response.context['active_borrowing'])
        self.assertFalse(response.context['ready_reservation'])

    def test_anonymous_user_has_no_member_actions_context(self):
        response = self.client.get(
            reverse(
                'catalog:book_detail',
                kwargs={'pk': self.book.pk}
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['ready_reservation'])
        self.assertFalse(response.context['active_borrowing'])


class ISBNLookupViewTests(CatalogTestDataMixin, TestCase):

    def setUp(self):
        cache.clear()

    def test_anonymous_user_redirected_to_login(self):
        response = self.client.get(
            reverse('catalog:isbn_lookup')
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn(
            reverse('accounts:login'),
            response.url
        )

    def test_member_cannot_access_isbn_lookup(self):
        self.client.login(
            username='test_member',
            password='TestPassword123!',
        )

        response = self.client.get(
            reverse('catalog:isbn_lookup')
        )

        self.assertEqual(response.status_code, 403)

    @patch('catalog.views.requests.get')
    def test_librarian_can_lookup_isbn(self, mock_get):

        api_response = Mock()

        api_response.raise_for_status.return_value = None

        api_response.json.return_value = {
            'title': 'Python API Testing',
            'publishers': ['Test Publisher'],
            'publish_date': '2025',
            'description': {
                'value': 'A test book description.'
            },
            'authors': [],
        }

        mock_get.return_value = api_response

        self.client.login(
            username='test_librarian',
            password='TestPassword123!',
        )

        response = self.client.post(
            reverse('catalog:isbn_lookup'),
            {'isbn': '978-1234567890'}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context['book_data']['title'],
            'Python API Testing'
        )

        mock_get.assert_called_once()

    def test_invalid_isbn_rejected(self):
        self.client.login(
            username='test_librarian',
            password='TestPassword123!',
        )

        response = self.client.post(
            reverse('catalog:isbn_lookup'),
            {'isbn': 'INVALID-ISBN'}
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['form'].is_valid())


class BookCreateViewTests(CatalogTestDataMixin, TestCase):

    def test_member_cannot_add_book(self):
        self.client.login(
            username='test_member',
            password='TestPassword123!',
        )

        response = self.client.get(
            reverse('catalog:book_create')
        )

        self.assertEqual(response.status_code, 403)

    def test_librarian_can_add_book(self):
        self.client.login(
            username='test_librarian',
            password='TestPassword123!',
        )

        response = self.client.post(
            reverse('catalog:book_create'),
            {
                'title': 'New Django Book',
                'author': 'New Author',
                'isbn': '9781234567892',
                'publisher': 'New Publisher',
                'publication_year': 2026,
                'description': 'A new test book.',
                'total_copies': 3,
            }
        )

        self.assertEqual(response.status_code, 302)

        book = Book.objects.get(isbn='9781234567892')
        self.assertEqual(book.total_copies, 3)
        self.assertEqual(book.available_copies, 3)


class CatalogFormTests(TestCase):

    def test_isbn_form_accepts_valid_isbn(self):
        form = ISBNLookupForm(
            data={'isbn': '978-1234567890'}
        )

        self.assertTrue(form.is_valid())
        self.assertEqual(
            form.cleaned_data['isbn'],
            '9781234567890'
        )

    def test_book_form_has_no_available_copies_field(self):
        self.assertNotIn('available_copies', BookForm().fields)

    def test_new_book_starts_with_all_copies_available(self):
        form = BookForm(
            data={
                'title': 'Five Copies',
                'author': 'Test Author',
                'isbn': '9781234567893',
                'publisher': 'Test Publisher',
                'publication_year': 2025,
                'description': 'Copy count check.',
                'total_copies': 5,
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        book = form.save()
        self.assertEqual(book.available_copies, 5)

