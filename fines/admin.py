from django.contrib import admin
from .models import Fine, FinePayment


@admin.register(Fine)
class FineAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'borrow_record',
        'overdue_days',
        'rate_per_day',
        'total_amount',
        'amount_paid',
        'outstanding_amount',
        'payment_status',
        'created_at',
    )

    list_filter = (
        'created_at',
        'overdue_days',
    )

    search_fields = (
        'borrow_record__user__username',
        'borrow_record__book__title',
    )

    readonly_fields = (
        'borrow_record',
        'overdue_days',
        'rate_per_day',
        'total_amount',
        'created_at',
    )

    list_select_related = ('borrow_record', 'borrow_record__user', 'borrow_record__book')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(FinePayment)
class FinePaymentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'fine',
        'amount',
        'received_by',
        'payment_date',
    )

    list_filter = ('payment_date',)

    search_fields = (
        'fine__borrow_record__user__username',
        'fine__borrow_record__book__title',
        'received_by__username',
    )

    readonly_fields = (
        'fine',
        'amount',
        'received_by',
        'payment_date',
    )

    list_select_related = (
        'fine',
        'received_by',
        'fine__borrow_record',
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
