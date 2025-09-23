from django.core.mail import send_mail
from django.conf import settings

def send_cancel_mail(booking):

    send_mail(
            "You're ticket cancellation has been successful",
            f"You're booking with booking id {booking.id} has been cancelled successfully upon you're request",
            settings.DEFAULT_FROM_EMAIL,
            [booking.user.email],
            fail_silently=False
        )