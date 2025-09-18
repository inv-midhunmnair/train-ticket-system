from django.core.management.base import BaseCommand
from django.core.mail import send_mail 
from core.models import Booking
from django.conf import settings


class Command(BaseCommand):

    def handle(self, *args, **options):
        bookings = Booking.objects.filter(status='train cancelled',email_sent=False)

        for booking in bookings:
            send_mail(
                f'Notification about Train Cancellation related to Booking ID:{booking.id}',
                f'''Dear{booking.user.first_name},\n We regret to inform you that the booking train
                {booking.train.train_name}({booking.train.train_number}) on {booking.journey_date} 
                has been cancelled due to unforeseen circumstances.
                We regret any inconvenience this has caused.''',
                settings.DEFAULT_FROM_EMAIL,
                [booking.user.email]
            )
            booking.email_sent = True
            booking.save()

        self.stdout.write(self.style.SUCCESS(f'Successfully sent {bookings.count()} emails'))