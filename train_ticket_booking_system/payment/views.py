# import razorpay
# from django.conf import settings
# from rest_framework.response import Response
# from core.models import Booking
# from rest_framework.views import APIView
# from .models import Payment
# from razorpay.errors import SignatureVerificationError
# from rest_framework import status

# # Create your views here.

# class PaymentInitiateView(APIView):

#     def post(self,request):

#         booking_id = request.data.get("booking_id")

#         try:
#             booking = Booking.objects.get(id=booking_id)

#         except Booking.DoesNotExist:
#             return Response({"error": "Booking not found"}, status=404)
        
#         client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        
#         amount_in_paise = int(booking.total_fare*100)

#         order = client.order.create(
#             {
#                 "amount": amount_in_paise,
#                 "currency": "INR",
#                 "payment_capture":1
#             }
#         )

#         Payment.objects.create(
#             booking = booking,
#             order_id = order['id'],
#             payment_status = "Payment Initiated"
#         )

#         return Response({
#             "success":True,
#             "order_id": order['id'],
#             "amount": amount_in_paise,
#             "key": settings.RAZORPAY_KEY_ID
#         })

# class VerifyPaymentView(APIView):

#     def post(self,request):
#         razorpay_order_id = request.data.get("razorpay_order_id")
#         razorpay_payment_id = request.data.get("razorpay_payment_id")
#         razorpay_signature = request.data.get("razorpay_signature")
#         booking_id = request.data.get("booking_id")

#         params_dict = {
#             "razorpay_order_id":razorpay_order_id,
#             "razorpay_payment_id":razorpay_payment_id,
#             "razorpay_signature":razorpay_signature
#         }

#         client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID,settings.RAZORPAY_KEY_SECRET))

#         try:
#             client.utility.verify_payment_signature(params_dict)
#             payment = Payment.objects.get(booking=booking_id)
#             payment.payment_id = razorpay_payment_id
#             payment.order_id = razorpay_order_id
#             payment.payment_status = "success"

#             payment.save()

#             booking = payment.booking
#             booking.status = "confirmed"
            
#             booking.save()

#             return Response({"message":"Payment Successfull"})
        
#         except SignatureVerificationError:
#             return Response({"error":"Signature verification failed"},status=status.HTTP_400_BAD_REQUEST)



            
