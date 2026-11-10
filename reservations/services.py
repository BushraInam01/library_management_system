
from django.db import IntegrityError, transaction
from django.db.models import F

from catalog.models import Book

from .models import Reservation


def create_reservation(user, book):
    """Reserve a book that has no generally available copies."""

    try:
        with transaction.atomic():
            book = Book.objects.select_for_update().get(
                pk=book.pk
            )

            if book.available_copies > 0:
                raise ValueError(
                    'This book is currently available. You can borrow it instead.'
                )

            existing = Reservation.objects.filter(
                user=user,
                book=book,
                status__in=[
                    Reservation.Status.WAITING,
                    Reservation.Status.READY,
                ],
            ).exists()

            if existing:
                raise ValueError(
                    'You already have an active reservation for this book.'
                )

            return Reservation.objects.create(
                user=user,
                book=book,
                status=Reservation.Status.WAITING,
            )

    except IntegrityError:
        raise ValueError(
            'You already have an active reservation for this book.'
        )


def prepare_next_reservation(book):
    """Allocate one available copy to the oldest waiting member."""

    with transaction.atomic():
        book = Book.objects.select_for_update().get(
            pk=book.pk
        )

        if book.available_copies <= 0:
            return None

        next_reservation = (
            Reservation.objects
            .select_for_update()
            .filter(
                book=book,
                status=Reservation.Status.WAITING,
            )
            .order_by('reserved_at', 'id')
            .first()
        )

        if next_reservation is None:
            return None

        next_reservation.status = Reservation.Status.READY
        next_reservation.save(
            update_fields=['status', 'updated_at']
        )

        Book.objects.filter(
            pk=book.pk,
            available_copies__gt=0,
        ).update(
            available_copies=F('available_copies') - 1
        )

        return next_reservation


def cancel_reservation(reservation):
    """Cancel an active reservation and release its allocated copy."""

    with transaction.atomic():
        reservation = Reservation.objects.select_for_update().get(
            pk=reservation.pk
        )

        if reservation.status not in [
            Reservation.Status.WAITING,
            Reservation.Status.READY,
        ]:
            raise ValueError(
                'Only active reservations can be cancelled.'
            )

        was_ready = (
            reservation.status == Reservation.Status.READY
        )

        reservation.status = Reservation.Status.CANCELLED
        reservation.save(
            update_fields=['status', 'updated_at']
        )

        if was_ready:
            book = Book.objects.select_for_update().get(
                pk=reservation.book_id
            )

            Book.objects.filter(
                pk=book.pk
            ).update(
                available_copies=F('available_copies') + 1
            )

            book.refresh_from_db()

            return prepare_next_reservation(book)

        return None
