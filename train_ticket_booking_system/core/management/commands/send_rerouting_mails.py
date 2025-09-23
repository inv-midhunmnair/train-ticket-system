from django.core.management.base import BaseCommand
from django.core.mail import send_mail 
from core.models import Booking, Station
from django.conf import settings

class Command(BaseCommand):

    def handle(self, *args, **options):
        bookings = Booking.objects.filter(train_rerouted=True,reroute_email_sent=False)

        for booking in bookings:
        
            if booking.boarding_station and booking.get_off_station:
                send_mail(
                    f'Notification about train rerouting for your journey {booking.id}',
                    f'We regret to inform you that your train {booking.train.train_name}({booking.train.train_number}) will be re routed from {booking.rerouted_station.station_name} due to some unforseeen circumstances. The nearest stations are {booking.boarding_station.station_name} and {booking.get_off_station.station_name}, please plan accordingly Any inconvenience caused is regreted',
                    settings.DEFAULT_FROM_EMAIL,
                    [booking.user.email]
                )
                booking.reroute_email_sent = True
                booking.save()
            
            elif booking.boarding_station:
                send_mail(
                    f'Notification about train rerouting for your journey {booking.id}',
                    f'We regret to inform you that your train {booking.train.train_name}({booking.train.train_number}) will be re routed from {booking.rerouted_station.station_name} due to some unforseeen circumstances. The nearest station is {booking.boarding_station.station_name}, please plan accordingly Any inconvenience caused is regreted',
                    settings.DEFAULT_FROM_EMAIL,
                    [booking.user.email]
                )
                booking.reroute_email_sent = True
                booking.save()

            else:
                send_mail(
                        f'Notification about train rerouting for your journey {booking.id}',
                        f'We regret to inform you that your train {booking.train.train_name}({booking.train.train_number}) will be re routed from {booking.rerouted_station.station_name} due to some unforseeen circumstances. The nearest station is {booking.get_off_station.station_name}, please plan accordingly Any inconvenience caused is regreted',
                        settings.DEFAULT_FROM_EMAIL,
                        [booking.user.email]
                    )
                booking.reroute_email_sent = True
                booking.save()
                
        self.stdout.write(self.style.SUCCESS(f'Successfully sent {bookings.count()} rerouting emails'))