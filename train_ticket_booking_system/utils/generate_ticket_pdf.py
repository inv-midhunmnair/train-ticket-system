from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import io

def generate_ticket_pdf(booking,train_start_date,from_arrival_time,to_arrival_time,to_date):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("<b>Booking Confirmation</b>", styles['Title']))
    story.append(Spacer(1,20))

    story.append(Paragraph(f"Booking ID is :{booking.id}",styles['Normal']))
    story.append(Paragraph(f"Train name:{booking.train.train_name} with train number:{booking.train.train_number}"))
    story.append(Paragraph(f"Train starts on {train_start_date}"))
    story.append(Paragraph(f"Journey is on:{booking.journey_date} at {from_arrival_time}"))
    story.append(Paragraph(f"From:{booking.from_station.station_name}"))
    story.append(Paragraph(f"Destination:{booking.to_station.station_name} will reach on {to_date} at {to_arrival_time}"))
    story.append(Paragraph(f"Status:{booking.status}"))
    story.append(Paragraph(f"Total Fare:{booking.total_fare}"))
    story.append(Spacer(1,20))

    data = [["Name", "Age", "Gender", "Seat No", "Coach Number", "Berth Type"]]

    for passenger in booking.passengers.all():
        data.append([
            passenger.passenger_name,
            str(passenger.passenger_age),
            passenger.passenger_gender,
            passenger.seat.seat_number,
            passenger.seat.coach.coach_number,
            passenger.seat.berth_type
        ])

    table = Table(data, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.lightblue),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("GRID", (0,0), (-1,-1), 1, colors.black),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
    ]))
    story.append(table)

    doc.build(story)
    buffer.seek(0)
    return buffer
