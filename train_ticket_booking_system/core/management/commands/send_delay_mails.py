from django.core.management.base import BaseCommand
from django.core.mail import send_mail 
from core.models import Booking, Station
from django.conf import settings

class Command(BaseCommand):

    def handle(self, *args, **options):
        bookings = Booking.objects.filter(delay_minutes__gt=0, delay_email_sent=False)

        for booking in bookings:
            send_mail(
                'Notification about train delay for your journey',
                f'We regret to inform you that your train {booking.train.train_name}({booking.train.train_number}) will be delayed by {booking.delay_minutes} minutes at {booking.delay_station.station_name} ',
                settings.DEFAULT_FROM_EMAIL,
                [booking.user.email]
            )
            booking.delay_email_sent = True
            booking.save()

        self.stdout.write(self.style.SUCCESS(f'Successfully sent {bookings.count()}'))
