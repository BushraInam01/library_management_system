
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from accounts.models import LibraryCard
from catalog.models import Book
from reservations.models import Reservation
from reservations.services import (
    create_reservation,
    prepare_next_reservation,
)

from .models import BorrowRecord


User = get_user_model()


class ReservationBorrowingIntegrationTests(TestCase):

    def setUp(self):

        # Create first library member.
        self.member1 = User.objects.create_user(
            username='member_one',
            password='TestPassword123!',
            role=User.Role.MEMBER,
        )

        # Create second library member.
        self.member2 = User.objects.create_user(
            username='member_two',
            password='TestPassword123!',
            role=User.Role.MEMBER,
        )

        # Create third library member for FIFO testing.
        self.member3 = User.objects.create_user(
            username='member_three',
            password='TestPassword123!',
            role=User.Role.MEMBER,
        )

        # Give every member an active library card.
        LibraryCard.objects.create(user=self.member1)
        LibraryCard.objects.create(user=self.member2)
        LibraryCard.objects.create(user=self.member3)

        # Create librarian.
        self.librarian = User.objects.create_user(
            username='test_librarian',
            password='TestPassword123!',
            role=User.Role.LIBRARIAN,
        )

        # Create a book with no available copies.
        self.book = Book.objects.create(
            title='Integration Test Book',
            author='Test Author',
            isbn='9781234567893',
            total_copies=2,
            available_copies=0,
        )

    def make_reservation_ready(self, member):

        # Create WAITING reservation while no copies are available.
        reservation = create_reservation(
            user=member,
            book=self.book,
        )

        # Simulate a returned copy becoming available.
        Book.objects.filter(pk=self.book.pk).update(
            available_copies=1
        )

        # Allocate the copy to the oldest waiting member.
        ready_reservation = prepare_next_reservation(self.book)

        return ready_reservation

    def test_ready_reservation_holder_can_borrow_book(self):

        reservation = self.make_reservation_ready(self.member1)

        self.assertEqual(
            reservation.status,
            Reservation.Status.READY,
        )

        # The copy is already allocated.
        self.book.refresh_from_db()
        self.assertEqual(self.book.available_copies, 0)

        self.client.force_login(self.member1)

        response = self.client.post(
            reverse(
                'borrowing:borrow_book',
                kwargs={'pk': self.book.pk},
            )
        )

        reservation.refresh_from_db()
        self.book.refresh_from_db()

        self.assertEqual(response.status_code, 302)

        self.assertEqual(
            reservation.status,
            Reservation.Status.FULFILLED,
        )

        self.assertTrue(
            BorrowRecord.objects.filter(
                user=self.member1,
                book=self.book,
                returned_at__isnull=True,
            ).exists()
        )

        # Stock must not decrease a second time.
        self.assertEqual(self.book.available_copies, 0)

    def test_other_member_cannot_borrow_ready_reserved_copy(self):

        self.make_reservation_ready(self.member1)

        self.client.force_login(self.member2)

        response = self.client.post(
            reverse(
                'borrowing:borrow_book',
                kwargs={'pk': self.book.pk},
            )
        )

        self.assertEqual(response.status_code, 302)

        # The second member must not receive the allocated copy.
        self.assertFalse(
            BorrowRecord.objects.filter(
                user=self.member2,
                book=self.book,
                returned_at__isnull=True,
            ).exists()
        )

        self.book.refresh_from_db()

        self.assertEqual(self.book.available_copies, 0)

    def test_ready_reservation_becomes_fulfilled_after_borrowing(self):

        reservation = self.make_reservation_ready(self.member1)

        self.client.force_login(self.member1)

        self.client.post(
            reverse(
                'borrowing:borrow_book',
                kwargs={'pk': self.book.pk},
            )
        )

        reservation.refresh_from_db()

        self.assertEqual(
            reservation.status,
            Reservation.Status.FULFILLED,
        )

    def test_returned_book_makes_oldest_waiting_reservation_ready(self):

        # Create two reservations in FIFO order.
        first_reservation = create_reservation(
            user=self.member2,
            book=self.book,
        )

        second_reservation = create_reservation(
            user=self.member3,
            book=self.book,
        )

        # Simulate an existing borrowing record.
        borrow_record = BorrowRecord.objects.create(
            user=self.member1,
            book=self.book,
        )

        self.client.force_login(self.librarian)

        response = self.client.post(
            reverse(
                'borrowing:return_book',
                kwargs={'pk': borrow_record.pk},
            )
        )

        first_reservation.refresh_from_db()
        second_reservation.refresh_from_db()
        borrow_record.refresh_from_db()
        self.book.refresh_from_db()

        self.assertEqual(response.status_code, 302)

        self.assertIsNotNone(borrow_record.returned_at)

        # The oldest reservation should become READY.
        self.assertEqual(
            first_reservation.status,
            Reservation.Status.READY,
        )

        # The next reservation should remain WAITING.
        self.assertEqual(
            second_reservation.status,
            Reservation.Status.WAITING,
        )

        # The returned copy has been allocated to the first member.
        self.assertEqual(self.book.available_copies, 0)

    def test_return_without_waiting_reservations_increases_stock(self):

        borrow_record = BorrowRecord.objects.create(
            user=self.member1,
            book=self.book,
        )

        self.client.force_login(self.librarian)

        response = self.client.post(
            reverse(
                'borrowing:return_book',
                kwargs={'pk': borrow_record.pk},
            )
        )

        self.book.refresh_from_db()
        borrow_record.refresh_from_db()

        self.assertEqual(response.status_code, 302)

        self.assertIsNotNone(borrow_record.returned_at)

        # No waiting reservation exists, so the copy remains available.
        self.assertEqual(self.book.available_copies, 1)

