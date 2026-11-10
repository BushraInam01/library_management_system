from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.views.generic.edit import FormView

from accounts.mixins import LibrarianRequiredMixin

from .forms import FinePaymentForm
from .models import Fine, FinePayment
from django.views.generic import ListView


class FinePaymentView(LibrarianRequiredMixin, FormView):
    template_name = 'fines/record_payment.html'
    form_class = FinePaymentForm

    @property
    def fine(self):
        if not hasattr(self, '_fine'):
            self._fine = get_object_or_404(
                Fine.objects.select_related(
                    'borrow_record__user',
                    'borrow_record__book',
                ),
                pk=self.kwargs['pk'],
            )
        return self._fine

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['fine'] = self.fine
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['fine'] = self.fine
        return context

    def form_valid(self, form):
        with transaction.atomic():
            fine = Fine.objects.select_for_update().get(
                pk=self.fine.pk
            )

            outstanding = fine.outstanding_amount
            amount = form.cleaned_data['amount']

            if outstanding <= 0:
                form.add_error(
                    None,
                    'This fine has already been fully paid.'
                )
                return self.form_invalid(form)

            if amount > outstanding:
                form.add_error(
                    'amount',
                    f'Payment cannot exceed Rs. {outstanding}.'
                )
                return self.form_invalid(form)

            FinePayment.objects.create(
                fine=fine,
                amount=amount,
                received_by=self.request.user,
            )

        messages.success(
            self.request,
            f'Payment of Rs. {amount} received successfully.'
        )

        return redirect('fines:fine_list')


class FineListView(LibrarianRequiredMixin, ListView):
    model = Fine
    template_name = 'fines/fine_list.html'
    context_object_name = 'fines'

    def get_queryset(self):
        return Fine.objects.select_related(
            'borrow_record__user',
            'borrow_record__book',
        ).prefetch_related('payments').order_by('-created_at')