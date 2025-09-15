from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from email.mime.image import MIMEImage

from .generate_ticket_pdf import generate_ticket_pdf
from .generate_qr_code import generate_qrcode


def send_booking_email(booking, train_start_date, from_arrival_time, to_arrival_time, to_date):
    # Generate QR code image
    qr_file = generate_qrcode(booking)

    html_body = f"""
    <html>
      <body>
        <p>Dear {booking.user.first_name} {booking.user.last_name},</p>
        <p>Here are your e-tickets for your journey with us.</p>
        <br>
        <p><strong>Booking ID:</strong> {booking.id}</p>
        <p><strong>Train:</strong> {booking.train.train_name} ({booking.train.train_number})</p>
        <p><strong>From:</strong> {booking.from_station.station_name} → 
           <strong>To:</strong> {booking.to_station.station_name}</p>
        <p><strong>Date:</strong> {booking.journey_date}</p>
        <p><strong>Total Fare:</strong> ₹{booking.total_fare}</p>
        <br>
        <p>Scan this QR at boarding:</p>
        <img src="cid:qr_code" alt="Booking QR Code">
      </body>
    </html>
    """

    email = EmailMultiAlternatives(
        subject="Booking confirmation for your journey with us",
        body="Please view this email in HTML mode to see the QR code and ticket.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[booking.user.email],
    )

    email.attach_alternative(html_body, "text/html")

    qr_image = MIMEImage(qr_file.read())
    qr_image.add_header('Content-ID', '<qr_code>')
    qr_image.add_header('Content-Disposition', 'inline')
    email.attach(qr_image)

    pdf_buffer = generate_ticket_pdf(booking, train_start_date, from_arrival_time, to_arrival_time, to_date)
    email.attach(f"booking_{booking.id}.pdf", pdf_buffer.getvalue(), "application/pdf")

    email.send()
