
from django.db import transaction

from .models import Book


def adjust_book_copies(book, new_total):
    """
    Safely update a book's total copies.

    Active borrow records and READY reservations represent
    allocated copies, so they cannot be removed from stock.
    Newly added copies are offered to waiting reservations
    in FIFO order.
    """

    if new_total < 1:
        raise ValueError("Total copies must be at least 1.")

    with transaction.atomic():
        locked_book = Book.objects.select_for_update().get(
            pk=book.pk
        )

        # Count copies currently allocated to members.
        from borrowing.models import BorrowRecord
        from reservations.models import Reservation

        active_borrows = BorrowRecord.objects.filter(
            book=locked_book,
            returned_at__isnull=True,
        ).count()

        ready_reservations = Reservation.objects.filter(
            book=locked_book,
            status=Reservation.Status.READY,
        ).count()

        allocated_copies = active_borrows + ready_reservations

        # Never reduce total copies below allocated copies.
        if new_total < allocated_copies:
            raise ValueError(
                f"Cannot reduce total copies to {new_total}. "
                f"{allocated_copies} copies are currently "
                "borrowed or reserved."
            )

        old_total = locked_book.total_copies

        # Recalculate available copies from actual allocations.
        locked_book.total_copies = new_total
        locked_book.available_copies = (
            new_total - allocated_copies
        )

        locked_book.save(
            update_fields=[
                "total_copies",
                "available_copies",
                "updated_at",
            ]
        )

        # Allocate available copies to waiting members.
        if new_total > old_total:
            from reservations.services import prepare_next_reservation

            while locked_book.available_copies > 0:
                reservation = prepare_next_reservation(
                    locked_book
                )

                if reservation is None:
                    break

                locked_book.refresh_from_db(
                    fields=["available_copies"]
                )

        locked_book.refresh_from_db()

        return locked_book
