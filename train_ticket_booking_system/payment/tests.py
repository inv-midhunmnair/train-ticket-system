from django.test import TestCase
from rest_framework.test import APIRequestFactory,force_authenticate
from rest_framework import status
from .models import *
from core.models import User,Station,Booking,Train
from .views import *
from datetime import date
from unittest.mock import patch,MagicMock

# Create your tests here.

class PaymentInitiateViewTest(TestCase):

    def setUp(self):

        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='password123',
            role=1,  
            username="testuser",
            first_name="Test",
            last_name="User",
            phone_number="1234567890"
        )

        self.train = Train.objects.create(
            train_name="Mangala Lakshwadeep",
            train_number=12625,
            schedule_days="Mon,Wed,Fri"
        )
        self.from_station = Station.objects.create(
            station_name="Aluva",
            station_code="ALV"
        )
        self.to_station = Station.objects.create(
            station_name="Thrissur",
            station_code="TCR"
        )
        self.booking = Booking.objects.create(
            user=self.user,
            train=self.train,
            from_station=self.from_station,
            to_station=self.to_station,
            journey_date=date(2025, 9, 11),
            status="confirmed",
            total_fare = 2000
        )

        self.payment = Payment.objects.create(
            booking = self.booking,
            payment_status = "pending",
            payment_id = "razorpay_payment_id",
            order_id = "razorpay_order_id",
        )

        self.train_route_from = Trainroute.objects.create(
            train=self.train,
            station=self.from_station,
            stop_order=1,
            arrival_time="08:40:00",
            departure_time="08:45:00",
            day_offset=0,
            distance=0
        )

        self.train_route_to = Trainroute.objects.create(
            train=self.train,
            station=self.to_station,
            stop_order=2,
            arrival_time="10:00:00",
            departure_time="10:05:00",
            day_offset=0,
            distance=50
        )

    def test_payment_initiate_success_post(self):
        request = self.factory.post('/payment/initiate/',data={"booking_id":self.booking.id})

        force_authenticate(request,user=self.user)

        view = PaymentInitiateView.as_view()
        response = view(request)

        self.assertEqual(response.status_code,status.HTTP_200_OK)
        self.assertEqual(True,response.data['success'])
        
class VerifyPaymentViewTest(TestCase):

    def setUp(self):

        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='password123',
            role=1,  
            username="testuser",
            first_name="Test",
            last_name="User",
            phone_number="1234567890"
        )

        self.train = Train.objects.create(
            train_name="Mangala Lakshwadeep",
            train_number=12625,
            schedule_days="Mon,Wed,Fri"
        )
        self.from_station = Station.objects.create(
            station_name="Aluva",
            station_code="ALV"
        )
        self.to_station = Station.objects.create(
            station_name="Thrissur",
            station_code="TCR"
        )
        self.booking = Booking.objects.create(
            user=self.user,
            train=self.train,
            from_station=self.from_station,
            to_station=self.to_station,
            journey_date=date(2025, 9, 11),
            status="confirmed",
            total_fare = 2000
        )

        self.payment = Payment.objects.create(
            booking = self.booking,
            payment_status = "pending",
            payment_id = "razorpay_payment_id",
            order_id = "razorpay_order_id",
        )

        self.train_route_from = Trainroute.objects.create(
            train=self.train,
            station=self.from_station,
            stop_order=1,
            arrival_time="08:40:00",
            departure_time="08:45:00",
            day_offset=0,
            distance=0
        )

        self.train_route_to = Trainroute.objects.create(
            train=self.train,
            station=self.to_station,
            stop_order=2,
            arrival_time="10:00:00",
            departure_time="10:05:00",
            day_offset=0,
            distance=50
        )

    def test_payment_verification_failure_post(self):
        data = {
            "razorpay_order_id":"razorpay_order_id",
            "razorpay_payment_id":"razorpay_payment_id",
            "razorpay_signature":"razorpay_signature"
        }

        request = self.factory.post('/payment/verify-payment',data=data)
        force_authenticate(request,user=self.user)

        view = VerifyPaymentView.as_view()
        response = view(request)
        self.assertEqual(response.status_code,status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data,{'error':'Signature verification failed'})

    @patch("razorpay.utility.utility.Utility.verify_payment_signature")
    def test_payment_verification_success_post(self,mock_verify):
        
        mock_verify.return_value = True
        data = {
            "razorpay_order_id":"razorpay_order_id",
            "razorpay_payment_id":"razorpay_payment_id",
            "razorpay_signature":"razorpay_signature",
            "booking_id":self.booking.id
        }

        request = self.factory.post('/payment/verify-payment',data=data)
        force_authenticate(request,user=self.user)
        view = VerifyPaymentView.as_view()
        response = view(request)
        self.assertEqual(response.status_code,status.HTTP_200_OK)
        self.assertEqual(response.data,{"message":"Payment Successfull tickets have been sent to your mail"})

class RefundViewTest(TestCase):

    def setUp(self):
        
        self.factory = APIRequestFactory()

        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='password123',
            role=1,  
            username="testuser",
            first_name="Test",
            last_name="User",
            phone_number="1234567890"
        )

        self.train = Train.objects.create(
            train_name="Mangala Lakshwadeep",
            train_number=12625,
            schedule_days="Mon,Wed,Fri"
        )

        self.from_station = Station.objects.create(
            station_name="Aluva",
            station_code="ALV"
        )
        self.to_station = Station.objects.create(
            station_name="Thrissur",
            station_code="TCR"
        )

        self.booking = Booking.objects.create(
            user=self.user,
            train=self.train,
            from_station=self.from_station,
            to_station=self.to_station,
            journey_date=date(2025, 9, 11),
            status="cancelled",
            total_fare = 2000
        )

        self.payment = Payment.objects.create(
            booking = self.booking,
            payment_status = "pending",
            payment_id = "razorpay_payment_id",
            order_id = "razorpay_order_id",
        )

        self.refund = Refund.objects.create(
            status = "",
            refund_amount = 0,
            refund_id = "",
            booking = self.booking,
            payment = self.payment
        )
    
    @patch("payment.views.razorpay.Client")
    def test_refund_successfull_post(self,mock_razorpay_client):
        
        mock_instance = MagicMock()
        mock_instance.payment.refund.return_value = {
            "id": "",
            "status": "processed"
        }
        mock_razorpay_client.return_value = mock_instance

        request = self.factory.delete('/payment/refund/',data={"booking_id":self.booking.id})
        view = RefundView.as_view()

        force_authenticate(request,user=self.user)
        response = view(request)

        self.assertEqual(response.status_code,status.HTTP_200_OK)
        self.assertEqual(response.data,{"message":"Refund Successful"})