from decimal import Decimal

from django import forms


class FinePaymentForm(forms.Form):
    amount = forms.DecimalField(
        label='Payment Amount (Rs.)',
        min_value=Decimal('0.01'),
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter payment amount',
            'step': '0.01',
            'min': '0.01',
        }),
    )

    def __init__(self, *args, fine=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fine = fine

    def clean_amount(self):
        amount = self.cleaned_data['amount']

        if self.fine is None:
            raise forms.ValidationError(
                'Fine information is required.'
            )

        outstanding = self.fine.outstanding_amount

        if amount > outstanding:
            raise forms.ValidationError(
                f'Payment cannot exceed the outstanding amount '
                f'of Rs. {outstanding}.'
            )

        return amount