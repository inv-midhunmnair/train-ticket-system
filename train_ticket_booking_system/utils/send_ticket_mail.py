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
      <head>
        <style>
          body {{
            font-family: Arial, sans-serif;
            background-color: #f4f6f8;
            margin: 0;
            padding: 20px;
          }}
          .ticket-container {{
            background: #fff;
            max-width: 700px;
            margin: auto;
            border: 1px solid #ddd;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.05);
            padding: 20px;
          }}
          .header {{
            text-align: center;
            border-bottom: 2px solid #0078d7;
            padding-bottom: 10px;
            margin-bottom: 20px;
          }}
          .header h2 {{
            margin: 0;
            color: #0078d7;
          }}
          .details {{
            margin-bottom: 20px;
          }}
          .details table {{
            width: 100%;
            border-collapse: collapse;
          }}
          .details td {{
            padding: 8px;
            border-bottom: 1px solid #eee;
          }}
          .details td:first-child {{
            font-weight: bold;
            color: #333;
            width: 35%;
          }}
          .qr {{
            text-align: center;
            margin-top: 20px;
          }}
          .footer {{
            text-align: center;
            font-size: 12px;
            color: #666;
            margin-top: 30px;
            border-top: 1px solid #eee;
            padding-top: 10px;
          }}
        </style>
      </head>
      <body>
        <div class="ticket-container">
          <div class="header">
            <h2>e-Ticket Confirmation</h2>
            <p>Thank you for booking with Us</p>
          </div>

          <div class="details">
            <table>
              <tr><td>Booking ID</td><td>{booking.id}</td></tr>
              <tr><td>Passenger</td><td>{booking.user.first_name} {booking.user.last_name}</td></tr>
              <tr><td>Train</td><td>{booking.train.train_name} ({booking.train.train_number})</td></tr>
              <tr><td>From</td><td>{booking.from_station.station_name}</td></tr>
              <tr><td>To</td><td>{booking.to_station.station_name}</td></tr>
              <tr><td>Date</td><td>{booking.journey_date}</td></tr>
              <tr><td>Departure</td><td>{from_arrival_time} ({train_start_date})</td></tr>
              <tr><td>Arrival</td><td>{to_arrival_time} ({to_date})</td></tr>
              <tr><td>Total Fare</td><td>₹{booking.total_fare}</td></tr>
            </table>
          </div>

          <div class="qr">
            <p><strong>Scan this QR at boarding:</strong></p>
            <img src="cid:qr_code" alt="Booking QR Code">
          </div>

        </div>
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
