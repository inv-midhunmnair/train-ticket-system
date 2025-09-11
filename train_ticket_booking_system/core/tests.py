from datetime import date, timedelta, timezone
from django.test import TestCase
from rest_framework.test import APIRequestFactory,force_authenticate
from rest_framework import status
from .models import User,Booking,Train,Station,TrainCoach,Seat,Passenger,Trainroute
from .serializers import TrainSearchSerializer,BookingSerializer,NewbookingSerializer, TrainSerializer, UserSerializer, UpdateSerializer,StationSerializer,GetUserSerializer, TrainrouteSerializer
from .views import BookingView,LoginOTPView,VerifyPasswordOTPView, SingleBookingView, StationViewset, TrainDetailsViewset, TrainTrackingView, TrainroutesViewset, UserViewset,VerifyEmailView,GetUserViewset,SearchResultsview

# Create your tests here.

class SingleBookingViewTest(TestCase):
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

        self.coach = TrainCoach.objects.create(
            train=self.train,
            capacity=72,
            coach_type="sleeper",
            coach_number="S2",
            base_price=200,
            fare_per_km=2
        )

        self.seat = Seat.objects.create(
            coach=self.coach,
            berth_type="upper",
            seat_number=1
        )

        self.booking = Booking.objects.create(
            user=self.user,
            train=self.train,
            from_station=self.from_station,
            to_station=self.to_station,
            journey_date=date(2025, 9, 11),
            status="confirmed"
        )

        self.passenger = Passenger.objects.create(
            booking=self.booking,
            seat=self.seat,
            passenger_name="Midhun",
            passenger_age=23,
            passenger_gender="male"
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

    def test_get_single_booking_success(self):
        request = self.factory.get(f'/users/profile/{self.booking.id}')
        force_authenticate(request,user=self.user)
        
        view = SingleBookingView.as_view()
        response = view(request, booking_id=self.booking.id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_data = BookingSerializer(self.booking).data
        self.assertEqual(response.data,expected_data)
    
    def test_get_single_booking_fail(self):
        request = self.factory.get(f'/users/profile/2')
        force_authenticate(request,user=self.user)

        view = SingleBookingView.as_view()
        response = view(request, booking_id=2)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class BookingViewTest(TestCase):
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

        self.user1 = User.objects.create_user(
            email='tesuser@example.com',
            password='password123',
            role=1, 
            username="testser",
            first_name="Test",
            last_name="User",
            phone_number="1214567890"
        )

        self.train = Train.objects.create(
            train_name="Mangala Lakshwadeep",
            train_number=12625,
            schedule_days="monday,wednesday,friday"
        )

        self.from_station = Station.objects.create(
            station_name="Aluva",
            station_code="ALV"
        )
        self.to_station = Station.objects.create(
            station_name="Thrissur",
            station_code="TCR"
        )

        self.coach = TrainCoach.objects.create(
            train=self.train,
            capacity=72,
            coach_type="sleeper",
            coach_number="S2",
            base_price=200,
            fare_per_km=2
        )

        self.seat = Seat.objects.create(
            coach=self.coach,
            berth_type="upper",
            seat_number=1
        )

        self.booking = Booking.objects.create(
            user=self.user,
            train=self.train,
            from_station=self.from_station,
            to_station=self.to_station,
            journey_date=date(2025, 9, 11),
            status="confirmed"
        )

        self.passenger = Passenger.objects.create(
            booking=self.booking,
            seat=self.seat,
            passenger_name="Midhun",
            passenger_age=23,
            passenger_gender="male"
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

    def test_get_booking_list_success(self):
        request = self.factory.get('/users/booking')
        force_authenticate(request,user=self.user)

        view = BookingView.as_view()
        response = view(request)

        self.assertEqual(response.status_code,status.HTTP_200_OK)

        expected_data = BookingSerializer(Booking.objects.filter(user=self.user), many=True).data
        self.assertEqual(response.data,expected_data)
    
    def test_get_booking_list_fail(self):
        request = self.factory.get('/users/booking')
        force_authenticate(request,user=self.user1)

        view = BookingView.as_view()
        response = view(request)

        self.assertEqual(response.status_code,status.HTTP_400_BAD_REQUEST)

    def test_add_booking_post_success(self):
        data = {
    "train_number":12625,
    "from_id":self.from_station.id,
    "to_id":self.to_station.id,
    "date":date(2025,9,1).isoformat(),  
    "coach_type":"sleeper",
    "passengers":[
        {"name":"Rishu","age":24,"gender":"male"}
        ]
    }
        request = self.factory.post('/users/booking',data,format='json')
        force_authenticate(request,user=self.user)

        view = BookingView.as_view()
        response = view(request)

        self.assertEqual(response.status_code,status.HTTP_200_OK)
        self.assertEqual(response.data,{'message': 'Successfully booked 1 tickets,tickets have been sent to your mail'})

class SearchResultsviewTest(TestCase):
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

        self.user1 = User.objects.create_user(
            email='tesuser@example.com',
            password='password123',
            role=1, 
            username="testser",
            first_name="Test",
            last_name="User",
            phone_number="1214567890"
        )

        self.train = Train.objects.create(
            train_name="Mangala Lakshwadeep",
            train_number=12625,
            schedule_days="monday,wednesday,friday"
        )

        self.from_station = Station.objects.create(
            station_name="Aluva",
            station_code="ALV"
        )
        self.to_station = Station.objects.create(
            station_name="Thrissur",
            station_code="TCR"
        )

        self.coach = TrainCoach.objects.create(
            train=self.train,
            capacity=72,
            coach_type="sleeper",
            coach_number="S2",
            base_price=200,
            fare_per_km=2
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

    def test_filter_trains_get(self):
        params = {
            "from_station": 'Aluva',
            "to_station": 'Thrissur',
            "date": date(2025,9,1).isoformat(),
            "minutes": "60",
            "train_name": "Mangala Lakshwadeep",
            "train_number": "12625",
            "time": "08:40",
            "type": "sleeper",
            "min": "100",
            "max": "500"
        }

        request = self.factory.get('/users/search',data=params)
        force_authenticate(request,user=self.user)
        view=SearchResultsview.as_view()
        response = view(request)

        self.assertEqual(response.status_code,status.HTTP_200_OK)

class TrainTrackingViewTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

        # self.user = User.objects.create_user(
        #     email='testuser@example.com',
        #     password='password123',
        #     role=1, 
        #     username="testuser",
        #     first_name="Test",
        #     last_name="User",
        #     phone_number="1234567890"
        # )

        # self.user1 = User.objects.create_user(
        #     email='tesuser@example.com',
        #     password='password123',
        #     role=1, 
        #     username="testser",
        #     first_name="Test",
        #     last_name="User",
        #     phone_number="1214567890"
        # )

        self.train = Train.objects.create(
            train_name="Mangala Lakshwadeep",
            train_number=12625,
            schedule_days="monday,wednesday,friday"
        )

        self.from_station = Station.objects.create(
            station_name="Aluva",
            station_code="ALV"
        )
        self.to_station = Station.objects.create(
            station_name="Thrissur",
            station_code="TCR"
        )

        # self.coach = TrainCoach.objects.create(
        #     train=self.train,
        #     capacity=72,
        #     coach_type="sleeper",
        #     coach_number="S2",
        #     base_price=200,
        #     fare_per_km=2
        # )

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

    def test_get_train_tracking_info_success(self):
        params = {
            "train_number":12625,
            "date": date(2025,9,1).isoformat(),
        }
        request = self.factory.get('/users/status/',data=params)
        view = TrainTrackingView.as_view()
        response = view(request)
        self.assertEqual(response.status_code,status.HTTP_200_OK)

class VerifyPasswordOTPViewTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='password123',
            role=1, 
            username="testuser",
            first_name="Test",
            last_name="User",
            phone_number="1234567890",
            forgot_password_otp=1234,
        )
    
    def test_password_verify_post_success(self):
        data = {
            "email":self.user.email,
            "otp":self.user.forgot_password_otp
        }

        request = self.factory.post('/verify-password-otp',data,'json')
        view = VerifyPasswordOTPView.as_view()
        response = view(request)
        self.assertEqual(response.data,"hi")
        # self.assertEqual(response.status_code,status.HTTP_200_OK)
    
    def test_password_verify_post_email_fail(self):
        data = {
            "email":"",
            "otp":""
        }

        request = self.factory.post('/verify-password-otp',data)
        view = VerifyPasswordOTPView.as_view()
        response = view(request)
        self.assertEqual(response.status_code,status.HTTP_401_UNAUTHORIZED)

class LoginOTPViewTest(TestCase):
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
    # def test_login_post_fail(self):
    #     data = {
    #         "email":self.user.email,
    #         "password":self.user.password
    #     }
    #     request = self.factory.post('/login',data)
    #     view = LoginOTPView.as_view()
    #     response = view(request)

    #     self.assertEqual(response.status_code,status.HTTP_400_BAD_REQUEST)
