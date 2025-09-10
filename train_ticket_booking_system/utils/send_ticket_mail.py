from django.conf import settings
from .generate_ticket_pdf import generate_ticket_pdf
from django.core.mail import EmailMessage

def send_booking_email(booking,train_start_date,from_arrival_time,to_arrival_time,to_date):
    subject = "Booking confirmation for your journey with us"
    body = f"Dear {booking.user.first_name}{booking.user.last_name},\n\nHere are your e-tickets for your journey with us"
    email = EmailMessage(subject, body, settings.DEFAULT_FROM_EMAIL, [booking.user.email])

    pdf_buffer = generate_ticket_pdf(booking,train_start_date,from_arrival_time,to_arrival_time,to_date)
    email.attach(f"booking_{booking.id}.pdf", pdf_buffer.getvalue(), "application/pdf")
    email.send()