
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView

from accounts.mixins import LibrarianRequiredMixin
from accounts.models import LibraryCard, User
from catalog.models import Book

from .models import Reservation
from .services import create_reservation, cancel_reservation


class MemberAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    login_url = 'accounts:login'

    def test_func(self):
        return self.request.user.role == User.Role.MEMBER


class CreateReservationView(LoginRequiredMixin, View):
    login_url = 'accounts:login'

    def post(self, request, book_id, *args, **kwargs):

        if request.user.role != User.Role.MEMBER:
            return HttpResponseForbidden(
                'Only library members can reserve books.'
            )

        has_active_card = LibraryCard.objects.filter(
            user=request.user,
            is_active=True,
        ).exists()

        if not has_active_card:
            messages.error(
                request,
                'You need an active library card to reserve books.'
            )
            return redirect('catalog:book_detail', pk=book_id)

        book = get_object_or_404(Book, pk=book_id)

        try:
            reservation = create_reservation(
                user=request.user,
                book=book,
            )

            messages.success(
                request,
                f'Reservation created successfully for "{book.title}". '
                f'Your status is {reservation.get_status_display()}.'
            )

        except ValueError as error:
            messages.warning(request, str(error))

        return redirect('catalog:book_detail', pk=book_id)


class MyReservationsView(MemberAccessMixin, ListView):
    model = Reservation
    template_name = 'reservations/my_reservations.html'
    context_object_name = 'reservations'

    def get_queryset(self):
        return Reservation.objects.filter(
            user=self.request.user
        ).select_related(
            'book'
        ).order_by('-reserved_at')


class CancelReservationView(MemberAccessMixin, View):

    def post(self, request, pk, *args, **kwargs):

        reservation = get_object_or_404(
            Reservation,
            pk=pk,
            user=request.user,
        )

        try:
            next_reservation = cancel_reservation(reservation)

            messages.success(
                request,
                'Your reservation has been cancelled successfully.'
            )

            if next_reservation:
                messages.info(
                    request,
                    f'The next reservation for "{reservation.book.title}" '
                    f'is now ready.'
                )

        except ValueError as error:
            messages.warning(request, str(error))

        return redirect('reservations:my_reservations')


class LibrarianReservationsView(LibrarianRequiredMixin, ListView):
    model = Reservation
    template_name = 'reservations/manage_reservations.html'
    context_object_name = 'reservations'

    def get_queryset(self):
        return Reservation.objects.select_related(
            'user',
            'book',
        ).order_by(
            'book__title',
            'reserved_at',
            'id',
        )
