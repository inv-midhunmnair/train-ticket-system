from urllib import response
from django.shortcuts import render
from django.urls import reverse
from django.conf import settings
from .models import Train, TrainCoach, User,Station, Trainroute, Seat, Booking, Passenger
from rest_framework.views import APIView
from rest_framework import viewsets, filters
from .serializers import TrainSearchSerializer,BookingSerializer,NewbookingSerializer, TrainSerializer, UserSerializer, UpdateSerializer,StationSerializer,GetUserSerializer, TrainrouteSerializer
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime, time, timedelta
from django.utils import timezone
import random
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .permissions import isAdmin, isUser
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.db.models import Q,F
from django.core.exceptions import ObjectDoesNotExist
from utils.send_ticket_mail import send_booking_email
# Create your views here.

class UserViewset(viewsets.ModelViewSet):
    queryset = User.objects.all()   
    permission_classes = [IsAuthenticated, isAdmin]
    def get_serializer_class(self):
        if self.request.method in ['PUT','PATCH']:
            return UpdateSerializer 

        return UserSerializer

    def perform_create(self, serializer):
        user = serializer.save()

        token = default_token_generator.make_token(user)
        verify_url = self.request.build_absolute_uri(
            reverse('verify-email')+ f"?uid={user.pk}&token={token}"
        )

        send_mail(
            'You need to verify your mail before being regsitered',
            f'Hey {user.first_name} {user.last_name} before activating your account you need to verify your email first click on this {verify_url} for verifying the mail',
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=True
        )

        return user
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({"message": "User created successfully. Please verify your email for further proceedings."},
                        status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def status(self, request, pk=None):
        if request.data.get('is_active') == 0:
            user = self.get_object()
            user.is_active = 0
            user.save()

            return Response({"message":"successfully changed the status"})
        
        else:
            user = self.get_object()
            user.is_active = 1
            user.save()

            return Response({"message":"successfully changed the status"})

class VerifyEmailView(APIView):
    def get(self,request, *args, **kwargs):
        uid = request.GET.get("uid")
        token = request.GET.get("token")

        if not uid or not token:
            return Response({"error":"UID and token are required"}, status = status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(pk=uid)
        except User.DoesNotExist:
            return Response({"error":"Invalid UID"}, status = status.HTTP_400_BAD_REQUEST)
        
        if default_token_generator.check_token(user, token):
            user.is_active = True
            user.is_email_verified = True
            user.save()
            return Response({"message":"Email verified successfully!"},status = status.HTTP_200_OK)
        else:
            return Response({"error":"Token is invalid or expired"},status = status.HTTP_400_BAD_REQUEST)

class LoginOTPView(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        user = authenticate(request, username=email,password=password)

        print(user)
        if user is None:
            return Response({"error":"Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        db_data = User.objects.get(email=email)
        email_flag = db_data.is_email_verified

        if not email_flag:
            return Response({"error":"You're email is not verified"}, status=status.HTTP_401_UNAUTHORIZED)
        minutes = 10
        otp = random.randint(100000,999999)
        expiry = timezone.now()+ timedelta(minutes=minutes)

        user.otp = otp
        user.otp_expires_at = expiry
        user.save()

        send_mail(
            'This is your OTP for verifying your authenticity',
            f'Your OTP is {otp} and is valid for only {minutes} minutes',
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False
        )

        return Response({"message":"OTP sent to your mail. Please verify to continue"})
    
class VerifyOTPView(APIView):
    def post(self, request):
        email = request.data.get("email")
        otp = request.data.get("otp")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error":"Given email is invalid"}) 

        original_otp = user.otp

        if str(original_otp) != str(otp):
            return Response({"error":"Wrong OTP"}, status=status.HTTP_400_BAD_REQUEST)
        
        if timezone.now()>user.otp_expires_at:
            return Response({"error":"The otp is expired"})
        
        if user.is_active and user.is_email_verified:
            refresh = RefreshToken.for_user(user)
            return Response({
                "message":"Successfull Login!!",
                "refresh":str(refresh),
                "access":str(refresh.access_token)
            })
        else:
            return Response({"error":"You are either blocked or email isn't verified"}, status=status.HTTP_401_UNAUTHORIZED)
        
class ForgotPasswordOTPView(APIView):
    def post(self, request):
        email = request.data.get('email')
        try:
            user = User.objects.get(email=email)
        except ObjectDoesNotExist:
            return Response({"error":"User with that email does not exist"},status=status.HTTP_401_UNAUTHORIZED)

        if user:
            minutes = 10
            otp = random.randint(100000,999999)
            expiry = timezone.now()+timedelta(minutes=minutes)

            user.forgot_password_otp = otp
            user.forgot_password_otp_expiry = expiry
            user.save() 

            send_mail(
                "You're One time Password for resetting password",
                f'The OTP is {otp} and is only valid for {minutes} minutes',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False
            )
        
            return Response({"message":"OTP has been sent to your mail"})

class VerifyPasswordOTPView(APIView):
    def post(self,request):
        email = request.data.get('email')
        entered_otp = request.data.get('otp')

        try:
            user = User.objects.get(email=email)
        except ObjectDoesNotExist:
            return Response({"error":"User with that email does not exist"},status=status.HTTP_401_UNAUTHORIZED)
        
        db_otp = user.forgot_password_otp

        if not entered_otp == db_otp:
            return Response({"error":"The OTP you gave is not matching our records"},status=status.HTTP_400_BAD_REQUEST)
        
        if timezone.now()>user.forgot_password_otp_expiry:
            return Response({"error":"The OTP is expired"},status=status.HTTP_400_BAD_REQUEST)
        
        token = default_token_generator.make_token(user)

        reset_link = self.request.build_absolute_uri(
            reverse('reset-password')+f"?uid={user.id}&token={token}"
        )

        send_mail(
            'Password Reset Link',
            f'This is the link for resetting your password {reset_link}',
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False
        )

        return Response({"message":"Reset password email successfully sent to your email"})

class ResetPasswordView(APIView):

    def post(self,request,*args,**kwargs):
        id = request.GET.get('uid')
        token = request.GET.get('token')
        password = request.data.get('password')
        confirm_password = request.data.get('confirm-password')

        user = User.objects.get(id=id)

        if default_token_generator.check_token(user,token):
            if password==confirm_password:
                user.set_password(password)
                user.save()
                return Response({"message":"Successfully Changed the password"})
            else:
                return Response({"error":"Passwords don't match"})
        else:
            return Response({"Hi"})

class GetUserViewset(viewsets.ModelViewSet):
    # permission_classes = [IsAuthenticated,isUser]
    serializer_class = GetUserSerializer
    queryset = User.objects.all()
    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id)
    
class TrainDetailsViewset(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, isAdmin]

    queryset = Train.objects.all()
    serializer_class = TrainSerializer

    def destroy(self, request, *args, **kwargs):
        train = self.get_object()
        train.is_active = False
        train.save()

        return Response({"message":"Deleted successfully"})
    
    @action(detail=True, methods=['post'])
    def activate(self,request,pk=None):
        train = self.get_object()
        train.is_active = False
        train.save()

        bookings = Booking.objects.filter(train=train,status='confirmed')
        
        for booking in bookings:
            send_mail(
                'Notification about Train',
                f'Informing you that your train {booking.train.train_name}({booking.train.train_number}) has been cancelled,sorry for the inconvenience',
                settings.DEFAULT_FROM_EMAIL,
                [booking.user.email],
                fail_silently=False
            )

        return Response({"message":"Successfully cancelled the train"})
    
    @action(detail=True,methods=['post'])
    def delay(self,request,pk=None):
        train = self.get_object()
        delay = request.data.get("delay")
        station_id = request.data.get("station_id")
        
        station = Station.objects.get(id=station_id)

        if not delay or not station_id:
            return Response({"error":"need to enter delay and the station"},status=status.HTTP_400_BAD_REQUEST)
        train_route = Trainroute.objects.get(train=train, station=station_id)
        delay_stop_order = train_route.stop_order

        from_routes = Trainroute.objects.filter(train=train,stop_order__lte=delay_stop_order).values_list('station', flat=True)
        to_routes = Trainroute.objects.filter(train=train,stop_order__gte=delay_stop_order).values_list('station', flat=True)

        station
        bookings = Booking.objects.filter(
            train=train,
            status='confirmed',
            from_station__in = from_routes,
            to_station__in = to_routes
        )

        for booking in bookings:
            send_mail(
                'Notification about Train',
                f'Informing you that your train {booking.train.train_name}({booking.train.train_number}) is delayed at {station.station_name} by {delay} minutes sorry for the inconvenience',
                settings.DEFAULT_FROM_EMAIL,
                [booking.user.email],
                fail_silently=False
            )
        print(booking)
        return Response({"message":"Successfully applied delay"})
class StationViewset(viewsets.ModelViewSet):    
    # permission_classes = [IsAuthenticated, isAdmin]

    queryset = Station.objects.all()
    serializer_class = StationSerializer

class TrainroutesViewset(viewsets.ModelViewSet):
    # permission_classes = [IsAuthenticated, isAdmin]

    queryset = Trainroute.objects.all()
    serializer_class = TrainrouteSerializer

class LoginView(APIView):
    def post(self,request):
        user = authenticate(request, username=request.data.get('email'),password=request.data.get('password'))
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        return Response({"access":str(access)})
                                                    
class SearchResultsview(APIView):

    def get(self,request):

        source_from = request.GET.get("from_station")
        destination_to = request.GET.get("to_station")
        date = request.GET.get("date")
        minutes = request.GET.get("minutes")
        train_name = request.GET.get("train_name")
        train_number = request.GET.get("train_number")
        arrival_train_time = request.GET.get("time")
        coach_type = request.GET.get("type")
        availability_flag = request.GET.get("flag")
        min_price = request.GET.get("min")
        max_price = request.GET.get("max")

        queryset = Trainroute.objects.prefetch_related('train').prefetch_related('station').all()

        if coach_type:
            queryset = queryset.filter(train__traincoach__coach_type__iexact = coach_type)
        if availability_flag:
            availability_flag=int(availability_flag)
            if availability_flag==1:
                queryset = queryset.filter(train__traincoach__capacity__gt=1)
        if train_name:
            queryset = queryset.filter(train__train_name__icontains=train_name)
        if train_number:
            queryset = queryset.filter(train__train_number=train_number)
        if arrival_train_time and minutes:
            start_time = datetime.strptime(arrival_train_time, "%H:%M").time()
            print(start_time)
            end_time = (datetime.combine(datetime.today(), start_time)+timedelta(minutes=int(minutes))).time()
            print(end_time)
            queryset = queryset.filter(arrival_time__gte = start_time,
                                                 arrival_time__lte = end_time)
        if source_from or destination_to or date:
            from_queryset = queryset.filter(station__station_name__iexact = source_from).values('train_id','stop_order','day_offset','train__schedule_days')
            to_queryset = queryset.filter(station__station_name__iexact=destination_to).values('train_id','stop_order','day_offset','train__schedule_days')

            to_dict = {}
            for to_id in to_queryset:
                to_dict[to_id['train_id']] = {'stop_order':to_id['stop_order'],'day_offset':to_id['day_offset']}
            # print(to_dict)

            matching_train_id = []
            for from_id in from_queryset:
                if from_id['train_id'] in to_dict and from_id['stop_order']<to_dict[from_id['train_id']]['stop_order']:
                    matching_train_id.append(from_id['train_id'])
            # print(matching_train_id)

            if source_from and destination_to and date:
                date = datetime.strptime(date,"%Y-%m-%d")
                
                valid_train_ids = []
                print(from_queryset)
                print(to_dict)
                for valid_id in from_queryset:
                    if valid_id['train_id'] in to_dict and valid_id['stop_order']<to_dict[valid_id['train_id']]['stop_order']:
                        checking_date = date-timedelta(days=valid_id['day_offset'])
                        print(checking_date)
                        day_name = checking_date.strftime("%A")
                        print(day_name)
                        if day_name.lower() in valid_id['train__schedule_days']:    
                            valid_train_ids.append(valid_id['train_id'])

                    print(valid_train_ids)

                queryset = queryset.filter(train_id__in = valid_train_ids, train__schedule_days__icontains = day_name)

            elif date:
                date = datetime.strptime(date,"%Y-%m-%d")
                print(date)

                day_name = date.strftime("%A")
                print(day_name)

                queryset = queryset.filter(train__schedule_days__icontains = day_name)
            elif source_from and destination_to:
                queryset = queryset.filter(train_id__in=matching_train_id)
        if min_price or max_price:
            min_price = float(min_price)
            max_price = float(max_price)

            filtered_ids = []
            for routes in queryset:
                try:
                    train_coach = TrainCoach.objects.get(train=routes.train)
                    from_route = Trainroute.objects.get(train=routes.train,station__station_name__iexact = source_from)
                    to_route = Trainroute.objects.get(train=routes.train, station__station_name__iexact=destination_to)
                except TrainCoach.DoesNotExist:
                    continue
                distance = to_route.distance - from_route.distance
                total_price = train_coach.base_price+(distance*train_coach.fare_per_km)
                
                if min_price<total_price<max_price:
                    filtered_ids.append(routes.train)
            print(total_price)
            print(filtered_ids)
            queryset = queryset.filter(train_id__in=filtered_ids)
        serializer = TrainSearchSerializer(queryset, many=True)
        return Response(serializer.data)

class TrainTrackingView(APIView):
 
    def get(self, request):
        train_no = request.GET.get("train_number")
        date = request.GET.get("date")  

        if not train_no or not date:
            return Response({"error": "train_number and date are required"},
                            status=status.HTTP_400_BAD_REQUEST)
        
        search_date = datetime.strptime(date, "%Y-%m-%d").date()

        try:
            train = Train.objects.get(train_number=train_no)
        except Train.DoesNotExist:
            return Response({"error": "Train not found"}, status=status.HTTP_404_NOT_FOUND)
        
        scheduled_days = train.schedule_days.split(",")
        start_date = search_date
        while start_date.strftime("%A").lower() not in scheduled_days:
            start_date = start_date - timedelta(days=1)

        print(start_date)
        routes = Trainroute.objects.filter(train=train).select_related("station").order_by("stop_order")

        now = datetime.combine(search_date, time(hour=7, minute=32))

        for i, route in enumerate(routes):
            arrival_dt = datetime.combine(start_date, route.arrival_time) + timedelta(days=route.day_offset)
            departure_dt = datetime.combine(start_date, route.departure_time) + timedelta(days=route.day_offset)

            # Case A: Train has not yet reached this station
            if now < arrival_dt:
                return Response({
                    "train_name": train.train_name,
                    "status": f"Train has not yet arrived at {route.station.station_name} ",
                    "arrival":f"Expected to reach {route.station.station_name} at {arrival_dt}"
                })

            # Case B: Train is currently at this station
            if arrival_dt <= now <= departure_dt:
                return Response({
                    "train_name": train.train_name,
                    "status": f"Train is currently at {route.station.station_name} "
                              f"(Departure at {departure_dt})"
                })

            # Case C: Train is between this station and next station
            if i + 1 < len(routes):
                next_route = routes[i + 1]
                next_arrival_dt = datetime.combine(start_date, next_route.arrival_time) + timedelta(days=next_route.day_offset)
                if departure_dt < now < next_arrival_dt:
                    return Response({
                        "train_name": train.train_name,
                        "status": f"Train is running between {route.station.station_name} "
                                  f"and {next_route.station.station_name}",
                        "eta_next_station": next_arrival_dt
                    })

        # Case D: Train has completed its journey
        last_route = routes.last()
        last_arrival_dt = datetime.combine(start_date, last_route.arrival_time) + timedelta(days=last_route.day_offset)
        last_station = last_route.station.station_name
        return Response({
            "train_name": train.train_name,
            "status": f"Train has completed its journey. Last stop: {last_station} on {last_arrival_dt}"
        })

class BookingView(APIView):

    def get(self,request):
        
        booking = Booking.objects.filter(user=request.user)
        
        serializer = BookingSerializer(booking, many=True)

        return Response(serializer.data)

    def post(self, request):

        serializer = NewbookingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        train_no = validated_data("train_number")
        from_station_id = validated_data("from_id")
        to_station_id = validated_data("to_id")
        journey_date = validated_data("date")
        coach_type = validated_data("coach_type")
        passengers = validated_data("passengers")
        no_of_tickets = len(passengers)

        train = Train.objects.get(train_number=train_no)
        # print(train.train_name)
        from_station = Station.objects.get(id=from_station_id)
        # print(from_station.station_name)
        to_station = Station.objects.get(id=to_station_id)
        # print(to_station.station_name)
        coach = TrainCoach.objects.filter(train=train,coach_type=coach_type)
        if not coach:
            return Response({"error":"Available coach doesn't exist"},status=status.HTTP_400_BAD_REQUEST)
        # print(coach)
        seats = Seat.objects.filter(coach_id__in=coach)
        # print(seats)  
        
        train_routes = Trainroute.objects.filter(train=train).order_by('stop_order')

        from_route = train_routes.filter(station=from_station).first()
        to_route = train_routes.filter(station=to_station).first()

        from_arrival_time = from_route.arrival_time
        to_arrival_time = to_route.arrival_time

        if not from_route:
            return Response({"error":f"This train doesen't go through {from_station.station_name}"},status=status.HTTP_400_BAD_REQUEST)
        if not to_route:
            return Response({"error":f"This train doesen't go through {to_station.station_name}"},status=status.HTTP_400_BAD_REQUEST)
        
        from_order = from_route.stop_order
        to_order = to_route.stop_order

        if from_route.stop_order>to_route.stop_order:
            return Response({"error":"Train doesen't go this order"},status=status.HTTP_400_BAD_REQUEST)
        
        journey_date = datetime.strptime(journey_date, "%Y-%m-%d").date()
        train_start_date = journey_date - timedelta(days=from_route.day_offset)

        to_date = train_start_date+timedelta(days=to_route.day_offset)

        day_name = train_start_date.strftime("%A").lower()

        train_schedule_days = train.schedule_days.lower().split(",")

        if day_name not in train_schedule_days:
            return Response({"error":"Train doesen't run on this day"},status=status.HTTP_400_BAD_REQUEST)
        
        stations_before_to = Trainroute.objects.filter(train=train, stop_order__lt=to_order).values("station")
        stations_after_from = Trainroute.objects.filter(train=train,stop_order__gt=from_order).values("station")
        
        booked = Passenger.objects.filter(
            booking__train=train,
            booking__journey_date = journey_date,
            booking__from_station__in = stations_before_to,
            booking__to_station__in = stations_after_from,
            booking__status = "confirmed", 
        ).values_list("seat_id",flat=True)

        available_seats = []
        for seat in seats:
            if seat.id not in booked:
                available_seats.append(seat)
        # print(available_seats)
        if no_of_tickets>len(available_seats):
            return Response({"error":"Requested Number of tickets is not available"},status=status.HTTP_400_BAD_REQUEST)
        
        booking = Booking.objects.create(
            user = request.user,
            train = train,
            from_station_id = from_station.id,
            to_station_id = to_station.id,
            status = "confirmed",
            journey_date = journey_date
        )
        # print(booking)

        for i,passenger in enumerate(passengers):
            Passenger.objects.create(
                booking = booking,
                passenger_name = passenger['name'],
                passenger_age = passenger['age'],
                passenger_gender = passenger['gender'],
                seat = available_seats[i]
            )
        send_booking_email(booking,train_start_date,from_arrival_time,to_arrival_time,to_date)
        return Response({"message":f"Successfully booked {no_of_tickets} tickets,tickets have been sent to your mail"})
    
    def delete(self,request,booking_id):

        booking = Booking.objects.get(id=booking_id, user=request.user)

        booking.status = "cancelled"
        booking.save()

        return Response({"message":"Booking cancelled successfully"})

    def put(self, request, booking_id):

        booking_row = Booking.objects.get(id=booking_id, user=request.user)
        passengers = booking_row.passengers.all()
        new_journey_date = request.data.get("new_journey_date")
        new_seat = request.data.get("new_seat")

        train_routes = Trainroute.objects.filter(train=booking_row.train).order_by('stop_order')

        from_route = train_routes.filter(station=booking_row.from_station).first()
        to_route = train_routes.filter(station=booking_row.to_station).first()

        stations_before_to = Trainroute.objects.filter(
            train=booking_row.train,
            stop_order__lt=to_route.stop_order
        ).values("station")

        stations_after_from = Trainroute.objects.filter(
            train=booking_row.train,
            stop_order__gt=from_route.stop_order
        ).values("station")

        new_journey_date = datetime.strptime(new_journey_date, "%Y-%m-%d").date()
        train_start_date = new_journey_date - timedelta(days=from_route.day_offset)

        day_name = train_start_date.strftime("%A").lower()
        train_schedule_days = booking_row.train.schedule_days.lower().split(",")

        if day_name not in train_schedule_days:
            return Response({"error": "Train doesen't run on this day"}, status=status.HTTP_400_BAD_REQUEST)

        if new_journey_date:
            coaches = TrainCoach.objects.filter(
                train=booking_row.train,
                coach_type=passengers[0].seat.coach.coach_type
            )
            print(coaches)
            available_seats = []

            for coach in coaches:
                total_seats = Seat.objects.filter(coach=coach)
                print(total_seats)
                booked = Passenger.objects.filter(
                    booking__train=booking_row.train,
                    booking__journey_date=new_journey_date,
                    booking__status='confirmed',
                    booking__from_station__in=stations_before_to,
                    booking__to_station__in=stations_after_from,
                    seat__coach=coach
                ).values_list('seat_id', flat=True)

                for seat in total_seats:
                    if seat.id not in booked:
                        available_seats.append(seat.id)
                        print(available_seats)
                print(len(available_seats))
                print(len(passengers))

            if len(passengers) > len(available_seats):
                return Response(
                    {"error": "Requested Number of tickets is not available"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            for i,passenger in enumerate(passengers):
                new_seat = Seat.objects.get(id=available_seats[i])
                passenger.seat = new_seat
                passenger.save()

            to_update_obj = Booking.objects.get(id=booking_id)
            to_update_obj.journey_date = new_journey_date
            to_update_obj.save()

            return Response({"message": "Date changed successfully"})
 
class SingleBookingView(APIView):

    def get(self,request,booking_id):
        booking = Booking.objects.get(id=booking_id)

        serializer = BookingSerializer(booking)

        return Response(serializer.data)