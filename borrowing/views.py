
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import IntegrityError, transaction
from django.db.models import F
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views import View
from django.views.generic import ListView

from accounts.models import LibraryCard, User
from catalog.models import Book
from fines.services import create_fine_for_return
from reservations.models import Reservation
from reservations.services import prepare_next_reservation

from .models import BorrowRecord


class LibrarianAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    login_url = 'accounts:login'

    def test_func(self):
        user = self.request.user

        return (
            user.is_superuser
            or user.role == User.Role.LIBRARIAN
        )


class BorrowBookView(LoginRequiredMixin, View):
    login_url = 'accounts:login'

    def post(self, request, pk, *args, **kwargs):

        if request.user.role != User.Role.MEMBER:
            return HttpResponseForbidden(
                'Only library members can borrow books.'
            )

        has_active_card = LibraryCard.objects.filter(
            user=request.user,
            is_active=True,
        ).exists()

        if not has_active_card:
            messages.error(
                request,
                'You need an active library card to borrow books.'
            )
            return redirect('catalog:book_detail', pk=pk)

        book = get_object_or_404(Book, pk=pk)

        try:
            with transaction.atomic():

                # Lock the book row while processing the borrowing.
                book = Book.objects.select_for_update().get(pk=book.pk)

                already_borrowed = BorrowRecord.objects.filter(
                    user=request.user,
                    book=book,
                    returned_at__isnull=True,
                ).exists()

                if already_borrowed:
                    messages.warning(
                        request,
                        'You have already borrowed this book and have not returned it.'
                    )
                    return redirect('catalog:book_detail', pk=pk)

                # Check whether this member has a READY reservation.
                ready_reservation = Reservation.objects.select_for_update().filter(
                    user=request.user,
                    book=book,
                    status=Reservation.Status.READY,
                ).first()

                if ready_reservation:

                    # This copy was already allocated when the reservation
                    # became READY, so do not decrease stock again.
                    borrow_record = BorrowRecord.objects.create(
                        user=request.user,
                        book=book,
                    )

                    ready_reservation.status = Reservation.Status.FULFILLED
                    ready_reservation.save(
                        update_fields=['status', 'updated_at']
                    )

                    reservation_fulfilled = True

                else:

                    # No READY reservation belongs to this member.
                    # They can borrow only an unallocated available copy.
                    updated_rows = Book.objects.filter(
                        pk=book.pk,
                        available_copies__gt=0,
                    ).update(
                        available_copies=F('available_copies') - 1
                    )

                    if updated_rows == 0:
                        messages.error(
                            request,
                            'Sorry, this book is currently not available. '
                            'Please make a reservation.'
                        )
                        return redirect('catalog:book_detail', pk=pk)

                    borrow_record = BorrowRecord.objects.create(
                        user=request.user,
                        book=book,
                    )

                    reservation_fulfilled = False

            if reservation_fulfilled:
                messages.success(
                    request,
                    f'Your reserved book "{book.title}" has been borrowed successfully! '
                    f'Please return it by {borrow_record.due_date}.'
                )
            else:
                messages.success(
                    request,
                    f'Book borrowed successfully! Please return it by {borrow_record.due_date}.'
                )

        except IntegrityError:
            messages.warning(
                request,
                'You already have an active borrowing record for this book.'
            )

        return redirect('catalog:book_detail', pk=pk)


class MyBorrowedBooksView(
    LoginRequiredMixin,
    UserPassesTestMixin,
    ListView
):
    model = BorrowRecord
    template_name = 'borrowing/my_borrowed_books.html'
    context_object_name = 'borrow_records'

    def test_func(self):
        return self.request.user.role == User.Role.MEMBER

    def get_queryset(self):
        return (
            BorrowRecord.objects
            .filter(user=self.request.user)
            .select_related('book')
            .order_by('-borrowed_at')
        )


class LibrarianBorrowedBooksView(
    LibrarianAccessMixin,
    ListView
):
    model = BorrowRecord
    template_name = 'borrowing/librarian_borrowed_books.html'
    context_object_name = 'borrow_records'

    def get_queryset(self):
        return (
            BorrowRecord.objects
            .filter(returned_at__isnull=True)
            .select_related('book', 'user')
            .order_by('due_date')
        )


class ReturnBookView(LibrarianAccessMixin, View):

    def post(self, request, pk, *args, **kwargs):

        with transaction.atomic():

            borrow_record = get_object_or_404(
                BorrowRecord.objects.select_for_update().select_related(
                    'book',
                    'user',
                ),
                pk=pk,
            )

            if borrow_record.returned_at is not None:
                messages.warning(
                    request,
                    'This book has already been returned.'
                )
                return redirect(
                    'borrowing:librarian_borrowed_books'
                )

            returned_at = timezone.now()

            borrow_record.returned_at = returned_at
            borrow_record.save(
                update_fields=['returned_at']
            )

            # Increase the available stock after returning the book.
            Book.objects.filter(
                pk=borrow_record.book_id
            ).update(
                available_copies=F('available_copies') + 1
            )

            # Check the FIFO reservation queue.
            # The oldest WAITING reservation receives the returned copy.
            book = Book.objects.get(pk=borrow_record.book_id)

            next_reservation = prepare_next_reservation(book)

            # Calculate an overdue fine, if applicable.
            fine = create_fine_for_return(
                borrow_record,
                returned_at=returned_at,
            )

        if next_reservation:
            messages.info(
                request,
                f'The book is now READY for member '
                f'{next_reservation.user.username}.'
            )

        if fine:
            messages.success(
                request,
                f'Book returned successfully. '
                f'Overdue fine: Rs. {fine.total_amount}.'
            )
        else:
            messages.success(
                request,
                f'"{borrow_record.book.title}" has been returned successfully. '
                f'No fine is due.'
            )

        return redirect(
            'borrowing:librarian_borrowed_books'
        )
