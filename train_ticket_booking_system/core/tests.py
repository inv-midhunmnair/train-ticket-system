from datetime import date, datetime, timedelta
from django.utils import timezone
from django.test import TestCase
from rest_framework.test import APIRequestFactory,force_authenticate
from rest_framework import status
from django.contrib.auth.tokens import default_token_generator
from rest_framework import serializers
from freezegun import freeze_time
from .validators import validate_name
from .models import TrainCancellation, User,Booking,Train,Station,TrainCoach,Seat,Passenger,Trainroute
from .serializers import BookingSerializer 
from .views import AdminDashboardviewset, AvailabilityView, ForgotPasswordOTPView,BookingView,VerifyOTPView,LoginOTPView,VerifyPasswordOTPView, SingleBookingView, StationViewset, TrainDetailsViewset, TrainTrackingView, TrainroutesViewset, UserViewset,VerifyEmailView,GetUserViewset,SearchResultsview

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
        expected_data = {'error': 'Booking not found'}
        self.assertEqual(response.data,expected_data)

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
        
        expected_data = {'error': 'no associated bookings'}
        self.assertEqual(response.data,expected_data)
        self.assertEqual(response.status_code,status.HTTP_400_BAD_REQUEST)

    def test_add_booking_post_success(self):

        data = {
                "train_number":12625,
                "from_id":self.from_station.id,
                "to_id":self.to_station.id,
                "date":'2025-09-01',  
                "coach_type":"sleeper",
                "passengers":[{"name":"Rishu","age":24,"gender":"male"}]
               }
        
        request = self.factory.post('/users/booking',data,format='json')
        force_authenticate(request,user=self.user)

        view = BookingView.as_view()
        response = view(request)

        self.assertEqual(response.status_code,status.HTTP_200_OK)
        self.assertEqual(response.data,{"message":"Successfully entered details now confirm the payment for booking the tickets"})

    def test_date_change_train_success_put(self):
        request = self.factory.put(f'users/booking/{self.booking.id}',data={"new_journey_date":"2025-09-08"})
        force_authenticate(request, user=self.user)

        view = BookingView.as_view()
        response = view(request,booking_id=self.booking.id)

        self.assertEqual(response.status_code,status.HTTP_200_OK)
        self.assertIn("Date changed successfully",response.data['message'])

    def test_cancel_booking_success_delete(self):
        request = self.factory.delete(f'users/booking/{self.booking.id}')
        force_authenticate(request,user=self.user)

        view = BookingView.as_view()
        response = view(request,booking_id=self.booking.id)

        self.assertEqual(response.data,{'error': 'Train already started cancellation unavailable'})

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
            "date":'2025-09-01',
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

        self.train = Train.objects.create(
            train_name="Mangala Lakshwadeep",
            train_number=12625,
            schedule_days=["monday","wednesday","friday"]
        )

        self.from_station = Station.objects.create(
            station_name="Aluva",
            station_code="ALV"
        )
        self.to_station = Station.objects.create(
            station_name="Thrissur",
            station_code="TCR"
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

    @freeze_time("2025-09-01 08:00:00")
    def test_get_train_tracking_info_before_starting_success(self):
        params = {
            "train_number":12625,
            "date": '2025-09-01'
        }
        request = self.factory.get('/users/status/',data=params)
        view = TrainTrackingView.as_view()
        response = view(request)

        self.assertIn(f'Train has not yet arrived at {self.from_station.station_name}',response.data['status'])
        self.assertEqual(response.status_code,status.HTTP_200_OK)

    @freeze_time("2025-09-01 08:41:00")
    def test_get_train_tracking_info_from_station_success(self):

        params = {
            "train_number":12625,
            "date": '2025-09-01'
        }
        request = self.factory.get('/users/status/',data=params)
        view = TrainTrackingView.as_view()
        response = view(request)

        self.assertIn(f'Train is currently at {self.from_station.station_name}',response.data['status'])
        self.assertEqual(response.status_code,status.HTTP_200_OK)

    @freeze_time("2025-09-01 09:00:00")
    def test_get_train_tracking_info_between_station_success(self):

        params = {
            "train_number":12625,
            "date": '2025-09-01'
        }
        request = self.factory.get('/users/status/',data=params)
        view = TrainTrackingView.as_view()
        response = view(request)

        self.assertIn(f'Train is running between {self.from_station.station_name} and {self.to_station.station_name}',response.data['status'])
        self.assertEqual(response.status_code,status.HTTP_200_OK)
    
    @freeze_time("2025-09-01 11:00:00")
    def test_get_train_tracking_info_last_station_success(self):

        params = {
            "train_number":12625,
            "date": '2025-09-01'
        }
        request = self.factory.get('/users/status/',data=params)
        view = TrainTrackingView.as_view()
        response = view(request)

        self.assertIn(f"Train has completed its journey. Last stop: {self.to_station.station_name} on 2025-09-01 {self.train_route_to.arrival_time}",response.data['status'])
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
            forgot_password_otp_expiry = timezone.now()+timedelta(minutes=10)
        )
    
    def test_password_verify_post_success(self):
        data = {
            "email":self.user.email,
            "otp":self.user.forgot_password_otp
        }

        request = self.factory.post('/verify-password-otp',data,'json')
        view = VerifyPasswordOTPView.as_view()
        response = view(request)
        self.assertEqual(response.data,{'message': 'Reset password email successfully sent to your email'} )
        self.assertEqual(response.status_code,status.HTTP_200_OK)
    
    def test_password_verify_post_email_fail(self):
        data = {
            "email":"sdf@gmail.com",
            "otp":3453
        }

        request = self.factory.post('/verify-password-otp',data)
        view = VerifyPasswordOTPView.as_view()
        response = view(request)
        self.assertEqual(response.status_code,status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data,{'error': 'User with that email does not exist'})

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
            phone_number="1234567890",
            is_email_verified=1
        )
    def test_login_post_fail(self):
        data = {
            "email":'abc@gmail.com',
            "password":self.user.password
        }
        request = self.factory.post('/login',data)
        view = LoginOTPView.as_view()
        response = view(request)

        self.assertEqual(response.data,{'error': 'Invalid credentials'})
        self.assertEqual(response.status_code,status.HTTP_401_UNAUTHORIZED)
    
    def test_login_post_success(self):
        data = {
            "email":'testuser@example.com',
            "password":'password123'
        }
        request = self.factory.post('/login',data)
        view = LoginOTPView.as_view()
        response = view(request)
        
        self.assertEqual(response.data,{'message': 'OTP sent to your mail. Please verify to continue'})
        self.assertEqual(response.status_code,status.HTTP_200_OK)

class VerifyOTPViewTest(TestCase):
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
            otp=1234,
            otp_expires_at = timezone.now()+timedelta(minutes=10),
            is_email_verified = 1
        )

        self.user1 = User.objects.create_user(
            email='testuser@exampe.com',
            password='password123',
            role=1, 
            username="tesuser",
            first_name="Test",
            last_name="User",
            phone_number="1234567890",
            otp=1234,
            otp_expires_at = timezone.now()+timedelta(minutes=10),
            is_email_verified = 0
        )
    
    def test_otp_verification_success_post(self):
        data = {
            "email":self.user.email,
            "otp":self.user.otp
        }
        request = self.factory.post('verify-otp/',data)
        view = VerifyOTPView.as_view()
        response = view(request)

        self.assertIn("Successfull Login!!",response.data['message'])
        self.assertEqual(response.status_code,status.HTTP_200_OK)
    
    def test_otp_not_equal_fail(self):
        data = {
            "email":self.user.email,
            "otp":""
        }
        request = self.factory.post('verify-otp/',data)
        view = VerifyOTPView.as_view()
        response = view(request)

        self.assertEqual(response.data,{'error': 'Wrong OTP'})
        self.assertEqual(response.status_code,status.HTTP_400_BAD_REQUEST)

    def test_email_not_verified(self):
        data = {
            "email":self.user1.email,
            "otp":self.user1.otp
        }
        request = self.factory.post('verify-otp/',data)
        view = VerifyOTPView.as_view()
        response = view(request)

        self.assertEqual(response.data,{'error': "You are either blocked or email isn't verified"})
        self.assertEqual(response.status_code,status.HTTP_401_UNAUTHORIZED)

    def test_user_not_exist(self):
        data = {
            "email":'abc@gmail.com',
            "otp":self.user.otp
        }
        request = self.factory.post('verify-otp/',data)
        view = VerifyOTPView.as_view()
        response = view(request)

        self.assertEqual(response.data,{"error":"User with that email does not exist"})
        self.assertEqual(response.status_code,status.HTTP_401_UNAUTHORIZED)

class TrainDetailsViewTest(TestCase):
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
            otp=1234,
            otp_expires_at = timezone.now()+timedelta(minutes=10),
            is_email_verified = 1
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

        Trainroute.objects.create(train=self.train, stop_order=1, day_offset=0,arrival_time='8:30',departure_time='8:45',station_id=self.from_station.id)
        self.booking = Booking.objects.create(
            user=self.user,
            train=self.train,
            from_station=self.from_station,
            to_station=self.to_station,
            journey_date=date(2025, 9, 8),
            status="confirmed"
        )
    
    def test_create_trains_post(self):
        data = {
            "train_name":"new train",
            "train_number":12039,
            "schedule_days":'["monday","wednesday","friday"]'
        }
        request = self.factory.post('users/trains',data)
        force_authenticate(request,user=self.user)
        view = TrainDetailsViewset.as_view({'post':'create'})
        response = view(request)

        self.assertIn("Successfully added train",response.data['message'])
        self.assertEqual(response.status_code,status.HTTP_201_CREATED)
    
    def test_deactivate_train_post(self):
        request = self.factory.post(f'users/trains/{self.train.id}/deactivate',data = {'date':"2025-09-08"})
        force_authenticate(request,user=self.user)
        view = TrainDetailsViewset.as_view({'post':'deactivate'})
        response = view(request,pk=self.train.id)
        
        self.assertEqual(response.status_code,status.HTTP_200_OK)

        self.assertIn("Successfully cancelled the train",response.data['message'])

    def test_delay_train_post(self):
        data = {
            "delay":30,
            "station_id":self.from_station.id,
            "date":"2025-09-01"
        }
        request = self.factory.post(f'users/trains/{self.train.id}/delay',data)
        force_authenticate(request,user=self.user)
        view = TrainDetailsViewset.as_view({'post':'delay'})
        response = view(request,pk=self.train.id)

        self.assertIn("Successfully applied delay",response.data['message'])
        self.assertEqual(response.status_code,status.HTTP_200_OK)

    def test_reroute_train_post(self):
        data = {
            "date":"2025-09-29",
            "stations":[1]
        }
        request = self.factory.post(f'users/trains/{self.train.id}/reroute/',data=data)
        force_authenticate(request,user=self.user)
        view = TrainDetailsViewset.as_view({'post':'reroute'})
        response = view(request,pk=self.booking.id)

        print(response.data)
        self.assertEqual(response.data,{'message': 'Successfully sent rerouting mails'})

class UserViewsetTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def test_add_user_post(self):
        data = {
            "email":'testuser@example.com',
            "password":'password123', 
            "username":"testuser",
            "phone_number":"9074891490",
            "first_name":"user",
            "last_name":"name",
            "role":"0"
        }

        request = self.factory.post('users/users',data)
        view = UserViewset.as_view({'post':'create'})
        response = view(request)

        self.assertIn('User created successfully. Please verify your email for further proceedings.',response.data['message'])
        self.assertEqual(response.status_code,status.HTTP_201_CREATED)

class ForgotPasswordOTPViewTest(TestCase):
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
            is_email_verified = 1
        )

    def test_forgot_pass_post(self):    

        data = {
            "email":self.user.email
        }

        request = self.factory.post('forgot-password/',data)
        view = ForgotPasswordOTPView.as_view()
        response = view(request)

        self.assertEqual(response.status_code,status.HTTP_200_OK)
        self.assertIn("OTP has been sent to your mail",response.data['message'])
    
    def test_user_not_exist_post(self):

        data = {
            "email":"abc@gmail.com"
        }
        request = self.factory.post('forgot-password/',data)
        view = ForgotPasswordOTPView.as_view()
        response = view(request)

        self.assertEqual(response.status_code,status.HTTP_401_UNAUTHORIZED)
        self.assertIn("User with that email does not exist",response.data['error'])

class ValidateNameTest(TestCase):
    def test_validate_name_fail(self):
        with self.assertRaises(serializers.ValidationError) as e:
            validate_name("v")
        self.assertIn("more than 2 characters",str(e.exception))

class AdminDashboardviewsetTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

        self.user = self.user = User.objects.create_user(
            email='testuser@example.com',
            password='password123',
            role=1, 
            username="testuser",
            first_name="Test",
            last_name="User",
            phone_number="1234567890",
            is_email_verified = 1
        )

        self.train = Train.objects.create(
            train_name="Mangala Lakshwadeep",
            train_number=12625,
            schedule_days=["monday","tuesday", "saturday"]
        )
        self.train1 = Train.objects.create(
            train_name="Mangaldweep",
            train_number=12624,
            schedule_days=["monday","friday", "saturday"]
        )

        self.from_station = Station.objects.create(
            station_name="Aluva",
            station_code="ALV"
        )
        self.to_station = Station.objects.create(
            station_name="Thrissur",
            station_code="TCR"
        )
        Trainroute.objects.create(train=self.train, stop_order=1, day_offset=0,arrival_time='8:30',departure_time='8:45',station_id=self.from_station.id)

        self.booking = Booking.objects.create(
            user=self.user,
            train=self.train,
            from_station=self.from_station,
            to_station=self.to_station,
            journey_date=date(2025, 9, 8),
            status="confirmed"
        )

        self.cancellation1 = TrainCancellation.objects.create(
            train=self.train1,
            cancellation_date=date(2025,9,5)
        )

    def test_statistics_get(self):
        
        request = self.factory.get('users/admin-dashboard/statistics')
        force_authenticate(request,user=self.user)

        view = AdminDashboardviewset.as_view({'get':'statistics'})
        response = view(request)
        self.assertEqual(response.status_code,status.HTTP_200_OK)
        self.assertEqual(response.data['Total Bookings'],1)
    
    def test_daily_reports_get(self):
        request = self.factory.get('users/admin-dashboard/daily_reports')
        force_authenticate(request,user=self.user)

        view = AdminDashboardviewset.as_view({'get':'daily_reports'})
        response = view(request)
        self.assertEqual(response.status_code,status.HTTP_200_OK)
        self.assertEqual(0.0,response.data["Today's cancellation ratio"])

    def test_running_trains_success_get(self):
        request = self.factory.get('users/admin-dashboard/running_trains')
        force_authenticate(request,user=self.user)

        view = AdminDashboardviewset.as_view({'get':'running_trains'})
        response = view(request)
        self.assertEqual(response.status_code,status.HTTP_200_OK)
        self.assertEqual(self.train.train_name,response.data['results'][0]['train name'])
    
class VerifyEmailViewTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

        self.user = self.user = User.objects.create_user(
            email='testuser@example.com',
            password='password123',
            role=1, 
            username="testuser",
            first_name="Test",
            last_name="User",
            phone_number="1234567890",
            is_email_verified = 1
        )
    
    def test_verify_email_success_get(self):
        token = default_token_generator.make_token(self.user)
        uid = self.user.id

        request = self.factory.get(f'verify-email/?uid={uid}&token={token}')
        view = VerifyEmailView.as_view()
        response = view(request)

        self.assertEqual(response.data['message'],'Email verified successfully!')
        self.assertEqual(response.status_code,status.HTTP_200_OK)
    
    def test_verify_email_uid_fail_get(self):
        token = default_token_generator.make_token(self.user)
        uid = 100

        request = self.factory.get(f'verify-email/?uid={uid}&token={token}')
        view = VerifyEmailView.as_view()
        response = view(request)

        self.assertEqual(response.data,{'error': 'Invalid UID'})
        self.assertEqual(response.status_code,status.HTTP_400_BAD_REQUEST)
    
    def test_verify_email_uid_absent_get(self):
        token = default_token_generator.make_token(self.user)
        request = self.factory.get(f'verify-email/?token={token}')
        view = VerifyEmailView.as_view()
        response = view(request)

        self.assertEqual(response.data,{'error': "UID and token are required"})
        self.assertEqual(response.status_code,status.HTTP_404_NOT_FOUND)

class UserStatusChangeTest(TestCase):

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
            is_email_verified = 1
        )

        self.user1 = User.objects.create_user(
            email='estuser@example.com',
            password='password123',
            role=0, 
            is_active=1,
            username="estuser",
            first_name="Test",
            last_name="User",
            phone_number="1334567890",
            is_email_verified = 1
        )
    
    def test_change_user_status_success_post(self):

        request = self.factory.post(f'users/users/{self.user.id}/status',data={"is_active":0})

        view = UserViewset.as_view({'post': 'status'})
        response = view(request,pk=self.user.id)

        self.assertEqual(response.data,{"message":"successfully changed the status"})
        self.assertEqual(response.status_code,status.HTTP_200_OK)

    def test_change_user_status_1_post(self):

        request = self.factory.post(f'users/users/{self.user.id}/status', data={"is_active":1})

        view = UserViewset.as_view({'post':'status'})
        response = view(request,pk=self.user.id)

        self.assertEqual(response.data,{"message":"successfully changed the status"})
        self.assertEqual(response.status_code,status.HTTP_200_OK)

class AvailabilityViewTest(TestCase):
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

        self.seat1 = Seat.objects.create(
            coach=self.coach,
            berth_type="upper",
            seat_number=2
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

        self.booking = Booking.objects.create(
            user=self.user,
            train=self.train,
            from_station=self.from_station,
            to_station=self.to_station,
            journey_date=date(2025, 9, 29),
            status="confirmed"
        )

        self.passenger = Passenger.objects.create(
            booking=self.booking,
            seat=self.seat,
            passenger_name="Midhun",
            passenger_age=23,
            passenger_gender="male"
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

    def test_availability_get(self):
        data = {
            "train_number":self.train.train_number,
            "from":self.from_station.id,
            "to":self.to_station.id,
            "date":"2025-09-29",
            "coach":"sleeper"
        }

        request = self.factory.get('users/availability',data=data)

        view = AvailabilityView.as_view()

        response = view(request)

        self.assertEqual({"message":f"There are 1 seats available for booking"},response.data)
