
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from catalog.models import Book

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

        self.assertEqual(
            Reservation.objects.count(),
            1,
        )

    def test_reservation_rejected_when_book_available(self):
        self.book.available_copies = 1
        self.book.save()

        with self.assertRaises(ValueError):
            create_reservation(
                self.member1,
                self.book,
            )

    def test_duplicate_active_reservation_rejected(self):
        create_reservation(
            self.member1,
            self.book,
        )

        with self.assertRaises(ValueError):
            create_reservation(
                self.member1,
                self.book,
            )

        self.assertEqual(
            Reservation.objects.count(),
            1,
        )

    def test_fifo_queue_selects_oldest_reservation(self):
        first = create_reservation(
            self.member1,
            self.book,
        )

        second = create_reservation(
            self.member2,
            self.book,
        )

        # Make the first reservation older.
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

    def test_no_waiting_reservation_returns_none(self):
        result = prepare_next_reservation(self.book)

        self.assertIsNone(result)

    def test_cancel_waiting_reservation(self):
        reservation = create_reservation(
            self.member1,
            self.book,
        )

        cancel_reservation(reservation)

        reservation.refresh_from_db()

        self.assertEqual(
            reservation.status,
            Reservation.Status.CANCELLED,
        )

    def test_cancel_ready_reservation_releases_book(self):
        reservation = create_reservation(
            self.member1,
            self.book,
        )

        self.book.available_copies = 1
        self.book.save()

        ready = prepare_next_reservation(self.book)

        self.assertEqual(
            ready.status,
            Reservation.Status.READY,
        )

        cancel_reservation(ready)

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

    def test_cancelled_reservation_can_be_created_again(self):
        reservation = create_reservation(
            self.member1,
            self.book,
        )

        cancel_reservation(reservation)

        new_reservation = create_reservation(
            self.member1,
            self.book,
        )

        self.assertNotEqual(
            reservation.pk,
            new_reservation.pk,
        )

        self.assertEqual(
            new_reservation.status,
            Reservation.Status.WAITING,
        )

