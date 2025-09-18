from django.core.management.base import BaseCommand
from django.core.mail import send_mail 
from core.models import Booking, Station
from django.conf import settings

class Command(BaseCommand):

    def handle(self, *args, **options):
        bookings = Booking.objects.filter(train_rerouted=True,reroute_email_sent=False)

        for booking in bookings:

            send_mail(
                'Notification about train rerouting for your journey',
                f'We regret to inform you that your train {booking.train.train_name}({booking.train.train_number}) will be re routed from {booking.rerouted_station.station_name} due to some unforseeen circumstances. Any inconvenience caused is regreted',
                settings.DEFAULT_FROM_EMAIL,
                [booking.user.email]
            )
            booking.reroute_email_sent = True
            booking.save()

        self.stdout.write(self.style.SUCCESS(f'Successfully sent {bookings.count()} rerouting emails'))