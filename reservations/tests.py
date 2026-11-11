
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from catalog.models import Book
from catalog.services import adjust_book_copies
from borrowing.models import BorrowRecord
from django.core.management import call_command

from .models import Reservation
from .services import (
    create_reservation,
    prepare_next_reservation,
    cancel_reservation,
)


User = get_user_model()


class ReservationServiceTests(TestCase):

    def setUp(self):
        self.member1 = User.objects.create_user(
            username='member_one',
            password='TestPassword123!',
        )

        self.member2 = User.objects.create_user(
            username='member_two',
            password='TestPassword123!',
        )

        self.member3 = User.objects.create_user(
            username='member_three',
            password='TestPassword123!',
        )

        self.member4 = User.objects.create_user(
            username='member_four',
            password='TestPassword123!',
        )

        self.book = Book.objects.create(
            title='Reservation Test Book',
            author='Test Author',
            isbn='9781234567892',
            total_copies=2,
            available_copies=0,
        )

    def test_create_reservation_for_unavailable_book(self):
        reservation = create_reservation(
            self.member1,
            self.book,
        )

        self.assertEqual(
            reservation.status,
            Reservation.Status.WAITING,
        )

        self.assertEqual(Reservation.objects.count(), 1)

    def test_reservation_rejected_when_book_available(self):
        self.book.available_copies = 1
        self.book.save()

        with self.assertRaises(ValueError):
            create_reservation(self.member1, self.book)

    def test_duplicate_active_reservation_rejected(self):
        create_reservation(self.member1, self.book)

        with self.assertRaises(ValueError):
            create_reservation(self.member1, self.book)

        self.assertEqual(Reservation.objects.count(), 1)

    def test_member_cannot_reserve_book_already_borrowed(self):
        BorrowRecord.objects.create(
            user=self.member1,
            book=self.book,
        )

        with self.assertRaisesMessage(
            ValueError,
            'You already have this book borrowed.',
        ):
            create_reservation(
                self.member1,
                self.book,
            )

        self.assertFalse(
            Reservation.objects.filter(
                user=self.member1,
                book=self.book,
            ).exists()
        )

    def test_fifo_queue_selects_oldest_reservation(self):
        first = create_reservation(self.member1, self.book)
        second = create_reservation(self.member2, self.book)

        first.reserved_at = timezone.now() - timedelta(minutes=10)
        first.save(update_fields=['reserved_at'])

        self.book.available_copies = 1
        self.book.save()

        ready = prepare_next_reservation(self.book)

        first.refresh_from_db()
        second.refresh_from_db()

        self.assertEqual(ready.pk, first.pk)
        self.assertEqual(first.status, Reservation.Status.READY)
        self.assertEqual(second.status, Reservation.Status.WAITING)

    def test_increased_book_copies_allocate_to_oldest_waiting_reservation(self):
        # Two copies are already borrowed.
        BorrowRecord.objects.create(
            user=self.member1,
            book=self.book,
        )

        BorrowRecord.objects.create(
            user=self.member2,
            book=self.book,
        )

        # Two members are waiting for the next available copies.
        first = create_reservation(self.member3, self.book)
        second = create_reservation(self.member4, self.book)

        first.reserved_at = timezone.now() - timedelta(minutes=10)
        first.save(update_fields=['reserved_at'])

        # Increase total copies from 2 to 3.
        updated_book = adjust_book_copies(
            self.book,
            new_total=3,
        )

        first.refresh_from_db()
        second.refresh_from_db()

        self.assertEqual(
            first.status,
            Reservation.Status.READY,
        )

        self.assertEqual(
            second.status,
            Reservation.Status.WAITING,
        )

        self.assertEqual(updated_book.total_copies, 3)
        self.assertEqual(updated_book.available_copies, 0)

    def test_no_waiting_reservation_returns_none(self):
        result = prepare_next_reservation(self.book)

        self.assertIsNone(result)

    def test_cancel_waiting_reservation(self):
        reservation = create_reservation(self.member1, self.book)

        cancel_reservation(reservation)

        reservation.refresh_from_db()

        self.assertEqual(
            reservation.status,
            Reservation.Status.CANCELLED,
        )

    def test_cancel_ready_reservation_releases_book(self):
        reservation = create_reservation(self.member1, self.book)

        self.book.available_copies = 1
        self.book.save()

        ready = prepare_next_reservation(self.book)

        self.assertEqual(ready.status, Reservation.Status.READY)

        cancel_reservation(ready)

        reservation.refresh_from_db()
        self.book.refresh_from_db()

        self.assertEqual(
            reservation.status,
            Reservation.Status.CANCELLED,
        )

        self.assertEqual(self.book.available_copies, 1)

    def test_cancelled_reservation_can_be_created_again(self):
        reservation = create_reservation(self.member1, self.book)

        cancel_reservation(reservation)

        new_reservation = create_reservation(
            self.member1,
            self.book,
        )

        self.assertNotEqual(reservation.pk, new_reservation.pk)

        self.assertEqual(
            new_reservation.status,
            Reservation.Status.WAITING,
        )



    def test_expired_ready_reservation_is_cancelled_and_next_member_gets_book(self):
        first = create_reservation(self.member1, self.book)
        second = create_reservation(self.member2, self.book)

        # Make one copy available and allocate it to the first member.
        self.book.available_copies = 1
        self.book.save()

        prepare_next_reservation(self.book)

        first.refresh_from_db()
        second.refresh_from_db()

        self.assertEqual(
            first.status,
            Reservation.Status.READY,
        )

        self.assertEqual(
            second.status,
            Reservation.Status.WAITING,
        )

        # Move the first member's deadline into the past.
        first.ready_until = timezone.now() - timedelta(days=1)
        first.save(update_fields=['ready_until'])

        # Run the expiry management command.
        call_command('expire_reservations')

        first.refresh_from_db()
        second.refresh_from_db()
        self.book.refresh_from_db()

        self.assertEqual(
            first.status,
            Reservation.Status.CANCELLED,
        )

        self.assertEqual(
            second.status,
            Reservation.Status.READY,
        )

        self.assertGreater(
            second.ready_until,
            timezone.now(),
        )

        self.assertEqual(
            self.book.available_copies,
            0,
        )

    def test_future_ready_reservation_is_not_expired(self):
        reservation = create_reservation(
            self.member1,
            self.book,
        )

        self.book.available_copies = 1
        self.book.save()

        prepare_next_reservation(self.book)

        reservation.refresh_from_db()

        self.assertEqual(
            reservation.status,
            Reservation.Status.READY,
        )

        self.assertGreater(
            reservation.ready_until,
            timezone.now(),
        )

        call_command('expire_reservations')

        reservation.refresh_from_db()
        self.book.refresh_from_db()

        self.assertEqual(
            reservation.status,
            Reservation.Status.READY,
        )

        self.assertEqual(
            self.book.available_copies,
            0,
        )

    def test_expired_reservation_releases_book_when_no_one_is_waiting(self):
        reservation = create_reservation(
            self.member1,
            self.book,
        )

        self.book.available_copies = 1
        self.book.save()

        prepare_next_reservation(self.book)

        reservation.refresh_from_db()

        reservation.ready_until = timezone.now() - timedelta(days=1)
        reservation.save(update_fields=['ready_until'])

        call_command('expire_reservations')

        reservation.refresh_from_db()
        self.book.refresh_from_db()

        self.assertEqual(
            reservation.status,
            Reservation.Status.CANCELLED,
        )

        self.assertEqual(
            self.book.available_copies,
            1,
        )
