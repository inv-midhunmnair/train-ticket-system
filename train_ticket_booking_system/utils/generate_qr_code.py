import qrcode
from io import BytesIO
from django.core.files.base import ContentFile

def generate_qrcode(booking):

    data = (
        f"Booking Id:{booking.id},\nTrain Name:{booking.train.train_name},\nTrain Number:{booking.train.train_number},\nFrom:{booking.from_station.station_name},\nTo:{booking.to_station.station_name},\nStatus:Confirmed,\nJourney Date:{booking.journey_date},\nTotal Fare:{booking.total_fare}"
    )

    qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_L,
    box_size=4,
    border=4,
)

    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return ContentFile(buffer.read(), name="booking_qr.png")