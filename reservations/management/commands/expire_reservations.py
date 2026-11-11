
from django.core.management.base import BaseCommand
from django.utils import timezone

from reservations.models import Reservation
from reservations.services import cancel_reservation


class Command(BaseCommand):
    help = 'Cancel expired READY reservations and release their books.'

    def handle(self, *args, **options):
        now = timezone.now()

        expired_reservations = Reservation.objects.filter(
            status=Reservation.Status.READY,
            ready_until__lte=now,
        ).order_by('ready_until', 'id')

        expired_count = 0

        for reservation in expired_reservations:
            try:
                cancel_reservation(reservation)
                expired_count += 1

                self.stdout.write(
                    self.style.SUCCESS(
                        f'Expired reservation #{reservation.pk} '
                        f'for {reservation.user.username}.'
                    )
                )

            except ValueError as error:
                self.stdout.write(
                    self.style.WARNING(
                        f'Skipped reservation #{reservation.pk}: {error}'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Expiry process completed. '
                f'{expired_count} reservation(s) expired.'
            )
        )
