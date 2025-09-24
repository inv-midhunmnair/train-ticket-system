import razorpay
from django.conf import settings
from rest_framework.response import Response
from core.models import Booking
from rest_framework.views import APIView
from .models import Payment, Refund
from core.models import Trainroute
from razorpay.errors import SignatureVerificationError
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from utils.send_ticket_mail import send_booking_email
from datetime import timedelta
from datetime import datetime

# Create your views here.

class PaymentInitiateView(APIView):

    permission_classes = [IsAuthenticated]
    
    def post(self,request):

        booking_id = request.data.get("booking_id")

        try:
            booking = Booking.objects.get(id=booking_id)

        except Booking.DoesNotExist:
            return Response({"error": "Booking not found"}, status=status.HTTP_404_NOT_FOUND)
        
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        
        amount_in_paise = int(booking.total_fare*100)

        order = client.order.create(
            {
                "amount": amount_in_paise,
                "currency": "INR",
                "payment_capture":1
            }
        )

        Payment.objects.create(
            booking = booking,
            order_id = order['id'],
            payment_status = "Payment Initiated"
        )

        return Response({
            "success":True,
            "order_id": order['id'],
            "amount": amount_in_paise,
            "key": settings.RAZORPAY_KEY_ID
        })

class VerifyPaymentView(APIView):

    permission_classes = [IsAuthenticated]
    
    def post(self,request):
        razorpay_order_id = request.data.get("razorpay_order_id")
        razorpay_payment_id = request.data.get("razorpay_payment_id")
        razorpay_signature = request.data.get("razorpay_signature")
        booking_id = request.data.get("booking_id")

        params_dict = {
            "razorpay_order_id":razorpay_order_id,
            "razorpay_payment_id":razorpay_payment_id,
            "razorpay_signature":razorpay_signature
        }

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID,settings.RAZORPAY_KEY_SECRET))

        try:
            client.utility.verify_payment_signature(params_dict)
            payment = Payment.objects.get(booking=booking_id)
            payment.payment_id = razorpay_payment_id
            payment.order_id = razorpay_order_id
            payment.payment_status = "success"

            payment.save()

            booking = payment.booking
            booking.status = "confirmed"
            
            booking.save()
            train_routes = Trainroute.objects.filter(train=booking.train)
            from_station=booking.from_station
            to_station=booking.to_station
            from_route = train_routes.filter(station=from_station).first()
            to_route = train_routes.filter(station=to_station).first()
            train_start_date = booking.journey_date - timedelta(days=from_route.day_offset)
            to_date = train_start_date+timedelta(days=to_route.day_offset)
            from_arrival_time = from_route.arrival_time
            to_arrival_time = to_route.arrival_time

            send_booking_email(booking,train_start_date,from_arrival_time,to_arrival_time,to_date)

            return Response({"message":"Payment Successfull tickets have been sent to your mail"})
        
        except SignatureVerificationError:
            return Response({"error":"Signature verification failed"},status=status.HTTP_400_BAD_REQUEST)

class RefundView(APIView):
    
    def delete(self,request):

        SERVICE_CHARGE = 10

        booking_id = request.data.get("booking_id")

        if not booking_id:
            return Response({"error":"Booking id is required"},status=status.HTTP_400_BAD_REQUEST)
        
        booking = Booking.objects.get(id=booking_id)

        if not booking:
            return Response({"error":"Booking not found"},status=status.HTTP_404_NOT_FOUND)

        payment = Payment.objects.get(booking=booking)

        if not payment:
            return Response({"error":"No payment found associated with the booking"},status=status.HTTP_404_NOT_FOUND)

        if booking.status != 'cancelled':
            return Response({"error":"This booking is still active so refund is not possible"})

        refund_amount = ((booking.total_fare)*(booking.cancellation_percentage/100))-SERVICE_CHARGE

        if booking.total_fare<SERVICE_CHARGE:
            refund_amount = 0
            
        refund_amount_paise = refund_amount*100
        print(refund_amount)
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID,settings.RAZORPAY_KEY_SECRET))

        refund = client.payment.refund(
            payment.payment_id,
            {"amount":refund_amount_paise}
        )

        Refund.objects.create(
            booking=booking,
            payment=payment,
            refund_amount = refund_amount,
            refund_id = refund.get("id"),
            status = refund.get("status")
        )

        return Response({"message":"Refund Successful"})
        
