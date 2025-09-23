from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import io

def generate_ticket_pdf(booking, train_start_date, from_arrival_time, to_arrival_time, to_date):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=25, leftMargin=25,
        topMargin=25, bottomMargin=25
    )
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle(
        'title',
        parent=styles['Title'],
        fontSize=20,
        textColor=colors.HexColor("#004080"),
        alignment=1,
        spaceAfter=15,
        leading=24
    )
    section_header_style = ParagraphStyle(
        'section_header',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor("#004080"),
        spaceAfter=10,
        leading=16
    )
    normal_style = ParagraphStyle(
        'normal',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=6,
        leading=14
    )
    small_style = ParagraphStyle(
        'small',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.grey,
        alignment=1,
        spaceBefore=15
    )

    story.append(Paragraph("e-Ticket Confirmation", title_style))
    story.append(Spacer(1, 12))

    booking_data = [
        ["Booking ID", booking.id],
        ["Passenger Name", f"{booking.user.first_name} {booking.user.last_name}"],
        ["Train", f"{booking.train.train_name} ({booking.train.train_number})"],
        ["From", booking.from_station.station_name],
        ["To", booking.to_station.station_name],
        ["Journey Date", booking.journey_date],
        ["Departure", f"{from_arrival_time} ({train_start_date})"],
        ["Arrival", f"{to_arrival_time} ({to_date})"],
        ["Status", booking.status],
        ["Total Fare(in rupees)", booking.total_fare]
    ]

    booking_table = Table(booking_data, hAlign="LEFT", colWidths=[130, 340])
    booking_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#004080")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("ALIGN", (0,0), (-1,-1), "LEFT"),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 11),
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ]))
    story.append(booking_table)
    story.append(Spacer(1, 20))

    story.append(Paragraph("Passenger Details", section_header_style))
    passenger_data = [["Name", "Age", "Gender", "Seat No", "Coach", "Berth Type"]]
    for passenger in booking.passengers.all():
        passenger_data.append([
            passenger.passenger_name,
            passenger.passenger_age,
            passenger.passenger_gender,
            passenger.seat.seat_number,
            passenger.seat.coach.coach_number,
            passenger.seat.berth_type
        ])

    passenger_table = Table(passenger_data, hAlign="LEFT", colWidths=[110, 40, 50, 50, 50, 70])
    ts = TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#004080")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 10),
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ])

    for i in range(1, len(passenger_data)):
        bg_color = colors.whitesmoke if i % 2 == 0 else colors.lightgrey
        ts.add("BACKGROUND", (0,i), (-1,i), bg_color)
    passenger_table.setStyle(ts)
    story.append(passenger_table)
    story.append(Spacer(1, 20))


    doc.build(story)
    buffer.seek(0)
    return buffer
