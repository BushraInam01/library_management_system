from django.contrib import admin
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


@admin.register(LibraryCard)
class LibraryCardAdmin(admin.ModelAdmin):

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
