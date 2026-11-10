from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin

from .models import User, LibraryCard


@admin.register(User)
class CustomUserAdmin(UserAdmin):

    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'role',
        'is_active',
        'is_staff',
    )

    list_filter = (
        'role',
        'is_active',
        'is_staff',
    )

    fieldsets = UserAdmin.fieldsets + (
        ('Library Information', {
            'fields': ('role',),
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Library Information', {
            'fields': ('role',),
        }),
    )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        # Members created in the admin get a library card, like those
        # who register on the website.
        if (
            not change
            and obj.role == User.Role.MEMBER
            and not obj.is_superuser
        ):
            LibraryCard.objects.get_or_create(user=obj)


@admin.action(description='Activate selected library cards')
def activate_cards(modeladmin, request, queryset):
    count = queryset.update(is_active=True)
    modeladmin.message_user(
        request, f'{count} card(s) activated.', messages.SUCCESS
    )


@admin.action(description='Deactivate selected library cards')
def deactivate_cards(modeladmin, request, queryset):
    count = queryset.update(is_active=False)
    modeladmin.message_user(
        request, f'{count} card(s) deactivated.', messages.SUCCESS
    )


@admin.register(LibraryCard)
class LibraryCardAdmin(admin.ModelAdmin):

    actions = [activate_cards, deactivate_cards]

    list_display = (
        'card_number',
        'user',
        'issued_at',
        'is_active',
    )

    list_filter = (
        'is_active',
        'issued_at',
    )

    search_fields = (
        'card_number',
        'user__username',
        'user__email',
    )

    readonly_fields = (
        'card_number',
        'issued_at',
    )
