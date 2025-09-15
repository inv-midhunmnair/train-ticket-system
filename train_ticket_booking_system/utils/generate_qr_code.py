import qrcode
from io import BytesIO
from django.core.files.base import ContentFile

def generate_qrcode(booking):

    data = {
        "Booking Id":booking.id,
        "Train Name":booking.train.train_name,
        "Train Number":booking.train.train_number,
        "From":booking.from_station.station_name,
        "To":booking.to_station.station_name,
        "Status":"Confirmed",
        "Journey Date":booking.journey_date,
        "Total Fare":booking.total_fare
    }

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