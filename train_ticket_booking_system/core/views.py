from itertools import groupby
from django.urls import reverse
from django.db.models import Sum, Avg, Max, Case, When, Value, CharField,Count
from django.db.models.functions import Round
from django.conf import settings
from rest_framework.pagination import PageNumberPagination
from .models import Train, TrainCoach, User,Station, Trainroute, Seat, Booking, Passenger,TrainCancellation
from django.db.models import Count, Q, F, FloatField, ExpressionWrapper
from rest_framework.views import APIView
from rest_framework import viewsets
from .serializers import RunningTrainSerializer,DailyBookingSerializer,OTPVerifySerializer, TrainSearchSerializer,LoginSerializer,BookingSerializer,NewbookingSerializer, TrainSerializer, UserSerializer, UpdateSerializer,StationSerializer,GetUserSerializer, TrainrouteSerializer
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from rest_framework.response import Response
from django.db.models.functions import ExtractMonth
from rest_framework import status
from datetime import datetime, time, timedelta
from django.utils import timezone
import random
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .permissions import isAdmin
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.core.exceptions import ObjectDoesNotExist
from utils.send_ticket_mail import send_booking_email
from django.core.exceptions import ObjectDoesNotExist
from utils.send_cancel_mail import send_cancel_mail
# Create your views here.

class UserViewset(viewsets.ModelViewSet):
    queryset = User.objects.all()   
    permission_classes = [AllowAny]
    
    def get_serializer_class(self):
        if self.action in ['update','partial_update']:
            return UpdateSerializer
        else:
            return UserSerializer

    def perform_create(self, serializer):
        user = serializer.save()

        token = default_token_generator.make_token(user)
        verify_url = self.request.build_absolute_uri(
            reverse('verify-email')+ f"?uid={user.pk}&token={token}"
        )

        send_mail(
            'You need to verify your mail before being registered',
            f'Hey {user.first_name} {user.last_name} before activating your account you need to verify your email first click on this {verify_url} for verifying the mail',
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=True
        )

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
        
        elif request.data.get('is_active') == 1:
            user = self.get_object()
            user.is_active = 1
            user.save()

            return Response({"message":"successfully changed the status"})
        
        else:
            return Response({"error":"Invalid Input"})

class VerifyEmailView(APIView):
    
    def get(self,request, *args, **kwargs):
        uid = request.GET.get("uid")
        token = request.GET.get("token")

        if not uid or not token:
            return Response({"error":"UID and token are required"}, status = status.HTTP_404_NOT_FOUND)
        
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
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        user = authenticate(request, username=validated_data['email'],password=password)

        # print(user)
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

        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        try:
            user = User.objects.get(email=validated_data['email'])
        except User.DoesNotExist:
            return Response({"error":"User with that email does not exist"},status=status.HTTP_401_UNAUTHORIZED) 

        original_otp = user.otp

        if str(original_otp) != str(otp):
            return Response({"error":"Wrong OTP"}, status=status.HTTP_400_BAD_REQUEST)
        
        if timezone.now()>user.otp_expires_at:
            return Response({"error":"The otp is expired"},status=status.HTTP_400_BAD_REQUEST)
        
        if user.is_active and user.is_email_verified:
            user.otp = None
            user.otp_expires_at = None
            user.save()
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
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        try:
            user = User.objects.get(email=validated_data['email'])
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

        serializer = OTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        entered_otp = validated_data['otp']
        try:
            user = User.objects.get(email=validated_data['email'])
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
        user.forgot_password_otp = None
        user.forgot_password_otp_expiry = None
        user.save()
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
                return Response({"error":"Passwords don't match"},status=status.HTTP_400_BAD_REQUEST)

class GetUserViewset(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = GetUserSerializer
    pagination_class = None 
    
    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id)
    
class TrainDetailsViewset(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, isAdmin]

    queryset = Train.objects.all()
    serializer_class = TrainSerializer

    def create(self,request,*args,**kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        train = serializer.instance

        return Response({"message":f"Successfully added train {train.train_name}"},status=status.HTTP_201_CREATED)
    
    def destroy(self, request, *args, **kwargs):
        train = self.get_object()
        train.is_active = False
        train.save()

        return Response({"message":f"{train.train_name} deleted successfully"},status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['post'])
    def deactivate(self,request,pk=None):
        train = self.get_object()
        date = request.data.get("date")
        
        train_start_date = datetime.strptime(date, "%Y-%m-%d")
        dates = []
        routes = Trainroute.objects.filter(train=train).order_by('day_offset')
        last_offset = routes.last().day_offset
        
        TrainCancellation.objects.get_or_create(train=train,cancellation_date=date)

        for i in range(last_offset+1):
            dates.append(train_start_date+timedelta(days=i))
        
        Booking.objects.filter(train=train,status='confirmed', journey_date__in = dates).update(status="train cancelled", email_sent=False)
    
        return Response({"message":"Successfully cancelled the train"})
    
    @action(detail=True,methods=['post'])
    def delay(self,request,pk=None):
        train = self.get_object()
        delay = request.data.get("delay")
        delay = int(delay)
        station_id = request.data.get("station_id")
        starting_date = request.data.get("date")

        if not delay or not station_id or not starting_date:
            return Response({"error":"need to enter delay and the station and the date"},status=status.HTTP_400_BAD_REQUEST)
        
        try:
            train_route = Trainroute.objects.get(train=train, station=station_id)
        except Trainroute.DoesNotExist:
            return Response({{"error":"Train does not go through this station"}})
        
        total_routes = Trainroute.objects.filter(train=train)
        delay_stop_order = train_route.stop_order
        from_routes = Trainroute.objects.filter(train=train,stop_order__lte=delay_stop_order).values_list('station', flat=True)
        to_routes = Trainroute.objects.filter(train=train,stop_order__gte=delay_stop_order).values_list('station', flat=True)

        train_start_date = datetime.strptime(starting_date,"%Y-%m-%d")
        last_route = total_routes.last()
        last_offset = last_route.day_offset
        for i in range(last_offset+1):
            dates = [train_start_date+timedelta(days=i)]
        
        Booking.objects.filter(
            train=train,
            status='confirmed',
            from_station__in = from_routes,
            to_station__in = to_routes,
            journey_date__in = dates
        ).update(delay_minutes=delay, delay_email_sent=False,delay_station=station_id)

        return Response({"message":"Successfully applied delay"})
    
    @action(detail=True, methods=['post'])
    def reroute(self, request, pk=None):
        train = self.get_object()
        train_start_date = request.data.get("date")
        stations = request.data.get("stations")

        if not train_start_date or not stations:
            return Response({"error": "need to enter date and stations"}, status=status.HTTP_400_BAD_REQUEST)

        train_start_date = datetime.strptime(train_start_date, "%Y-%m-%d")
        train_start_day = train_start_date.strftime("%A").lower()

        if train_start_day not in train.schedule_days:
            return Response({"error":"Train doesen't run on this day"},status=status.HTTP_400_BAD_REQUEST)
        
        reroute_stations = Station.objects.filter(id__in=stations)

        if not reroute_stations:
            return Response({"error":"Invalid Station Entered"},status=status.HTTP_404_NOT_FOUND)
        
        routes = Trainroute.objects.filter(train=train, station__in=reroute_stations)

        if not routes:
            return Response({"error":"Station not in the train's route"},status=status.HTTP_400_BAD_REQUEST)

        if not routes.exists():
            return Response({"error": "No such stations in this train route"}, status=status.HTTP_400_BAD_REQUEST)

        last_offset = Trainroute.objects.filter(train=train).last().day_offset
        dates = [train_start_date + timedelta(days=i) for i in range(last_offset + 1)]
 
        total_train_stations = list(
            Trainroute.objects.filter(train=train)
            .order_by("stop_order")
            .values_list("station__station_name", flat=True)
        )

        for reroute_station in reroute_stations:
            station_stop_order = routes.get(station=reroute_station).stop_order
            from_routes = Trainroute.objects.filter(train=train, stop_order__lte=station_stop_order).values('station')
            to_routes = Trainroute.objects.filter(train=train, stop_order__gte=station_stop_order).values('station')

            bookings = Booking.objects.filter(
                train=train,
                journey_date__in=dates,
                from_station__in=from_routes,
                to_station__in=to_routes,
                status='confirmed'
            )

            for booking in bookings:
                from_idx = total_train_stations.index(booking.from_station.station_name)
                to_idx = total_train_stations.index(booking.to_station.station_name)

                boarding = None
                for i in range(from_idx, -1, -1):
                    if total_train_stations[i] not in [s.station_name for s in reroute_stations]:
                        boarding = Station.objects.get(station_name=total_train_stations[i])
                        break

                get_off_station = None
                for i in range(to_idx, len(total_train_stations)):
                    if total_train_stations[i] not in [s.station_name for s in reroute_stations]:
                        get_off_station = Station.objects.get(station_name=total_train_stations[i])
                        break

                booking.boarding_station = boarding  
                booking.get_off_station = get_off_station  
                booking.train_rerouted = True
                booking.rerouted_station = reroute_station
                booking.save()

        return Response({"message": "Successfully sent rerouting mails"})

class StationViewset(viewsets.ModelViewSet):    
    permission_classes = [IsAuthenticated, isAdmin]

    queryset = Station.objects.all()
    serializer_class = StationSerializer

class TrainroutesViewset(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, isAdmin]

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
        min_price = request.GET.get("min")
        max_price = request.GET.get("max")

        queryset = Trainroute.objects.prefetch_related('train').prefetch_related('station').all()

        if coach_type:
            queryset = queryset.filter(train__traincoach__coach_type__iexact = coach_type).distinct()
     
        if train_name:
            queryset = queryset.filter(train__train_name__icontains=train_name)
        if train_number:
            queryset = queryset.filter(train__train_number=train_number)
       
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
                # print(from_queryset)
                # print(to_dict)
                for valid_id in from_queryset:
                    if valid_id['train_id'] in to_dict and valid_id['stop_order']<to_dict[valid_id['train_id']]['stop_order']:
                        checking_date = date-timedelta(days=valid_id['day_offset'])
                        # print(checking_date)
                        day_name = checking_date.strftime("%A")
                        # print(day_name)
                        if day_name.lower() in valid_id['train__schedule_days']:    
                            valid_train_ids.append(valid_id['train_id'])

                    # print(valid_train_ids)

                queryset = queryset.filter(train_id__in = valid_train_ids, train__schedule_days__icontains = day_name)

            elif source_from and destination_to:
                queryset = queryset.filter(train_id__in=matching_train_id)
   
        if min_price or max_price:
            min_price = float(min_price) 
            max_price = float(max_price) 

            filtered_train_ids = []

            for route in queryset:  
                train = route.train
                try:
                    from_route = Trainroute.objects.get(train=train, station__station_name__iexact=source_from)
                    to_route = Trainroute.objects.get(train=train, station__station_name__iexact=destination_to)
                except Trainroute.DoesNotExist:
                    continue
            distance = to_route.distance - from_route.distance

            coaches = TrainCoach.objects.filter(train=train,coach_type=coach_type)
            # print(coaches)
            for coach in coaches:
                total_price = coach.base_price + (distance * coach.fare_per_km)
                if min_price <= total_price <= max_price:
                    filtered_train_ids.append(train.id)
                    break  
            
            queryset = queryset.filter(train_id__in=filtered_train_ids)

        if arrival_train_time and minutes:
            start_time = datetime.strptime(arrival_train_time, "%H:%M").time()
            # print(start_time)
            end_time = (datetime.combine(datetime.today(), start_time)+timedelta(minutes=int(minutes))).time()
            # print(end_time)
            queryset = queryset.filter(arrival_time__gte = start_time,
                                                 arrival_time__lte = end_time)
    
        paginator = PageNumberPagination()
        paginator.page_size = 5

        paginated_queryset = paginator.paginate_queryset(queryset,request)
        
        paginated_queryset.sort(key=lambda x: x.train.id)

        grouped_result = []
        for train, train_routes in groupby(paginated_queryset, key=lambda x: x.train):
            grouped_result.append({
                "train_name": train.train_name,
                "train_number": train.train_number,
                "schedule_days": train.schedule_days,
                "is_active": train.is_active,
                "routes": [
                    {
                        "stop_order": r.stop_order,
                        "arrival_time": r.arrival_time,
                        "departure_time": r.departure_time,
                        "day_offset": r.day_offset,
                        "distance": r.distance,
                        "station": {
                            "id": r.station.id,
                            "station_code": r.station.station_code,
                            "station_name": r.station.station_name
                        }
                    }
                    for r in train_routes
                ]
            })

        return paginator.get_paginated_response(grouped_result)

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
        
        scheduled_days = train.schedule_days
        start_date = search_date
        while start_date.strftime("%A").lower() not in scheduled_days:
            start_date = start_date - timedelta(days=1)

        # print(start_date)
        routes = Trainroute.objects.filter(train=train).select_related("station").order_by("stop_order")

        now = datetime.combine(search_date, time(hour=8, minute=5))

        # now = datetime.now()
        for i, route in enumerate(routes):
            arrival_dt = datetime.combine(start_date, route.arrival_time) + timedelta(days=route.day_offset)
            departure_dt = datetime.combine(start_date, route.departure_time) + timedelta(days=route.day_offset)

            if now < arrival_dt:
                return Response({
                    "train_name": train.train_name,
                    "status": f"Train has not yet arrived at {route.station.station_name} ",
                    "arrival":f"Expected to reach {route.station.station_name} at {arrival_dt}"
                })

            if arrival_dt <= now <= departure_dt-timedelta(minutes=1):
                return Response({
                    "train_name": train.train_name,
                    "status": f"Train is currently at {route.station.station_name} "
                              f"(Departure at {departure_dt})"
                })

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

        last_route = routes.last()
        last_arrival_dt = datetime.combine(start_date, last_route.arrival_time) + timedelta(days=last_route.day_offset)
        last_station = last_route.station.station_name
        return Response({
            "train_name": train.train_name,
            "status": f"Train has completed its journey. Last stop: {last_station} on {last_arrival_dt}"
        })

class BookingView(APIView):

    permission_classes = [IsAuthenticated]
    def get(self,request):
        
        booking = Booking.objects.filter(user=request.user)
        
        if not booking:
            return Response({"error":"no associated bookings"},status=status.HTTP_400_BAD_REQUEST)
        serializer = BookingSerializer(booking, many=True)

        return Response(serializer.data)

    def post(self, request):

        serializer = NewbookingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        train_no = validated_data["train_number"]
        from_station_id = validated_data["from_id"]
        to_station_id = validated_data["to_id"]
        journey_date = validated_data["date"]
        coach_type = validated_data["coach_type"]
        passengers = validated_data["passengers"]
        no_of_tickets = len(passengers)

        if from_station_id == to_station_id:
            return Response({"error":"source and destination can't be the same"},status=status.HTTP_400_BAD_REQUEST)
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

        if not from_route:
            return Response({"error":f"This train doesen't go through {from_station.station_name}"},status=status.HTTP_400_BAD_REQUEST)
        if not to_route:
            return Response({"error":f"This train doesen't go through {to_station.station_name}"},status=status.HTTP_400_BAD_REQUEST)
        
        from_order = from_route.stop_order
        to_order = to_route.stop_order

        if from_route.stop_order>to_route.stop_order:
            return Response({"error":"Train doesen't go this order"},status=status.HTTP_400_BAD_REQUEST)
        
        train_start_date = journey_date - timedelta(days=from_route.day_offset)

        to_date = train_start_date+timedelta(days=to_route.day_offset)

        day_name = train_start_date.strftime("%A").lower()

        train_schedule_days = train.schedule_days

        if day_name not in train_schedule_days:
            return Response({"error":"Train doesen't run on this day"},status=status.HTTP_400_BAD_REQUEST)
        
        stations_before_to = Trainroute.objects.filter(train=train, stop_order__lt=to_order).values("station")
        stations_after_from = Trainroute.objects.filter(train=train,stop_order__gt=from_order).values("station")
        
        booked = Passenger.objects.filter(
            booking__train=train,
            booking__journey_date = journey_date,
            booking__from_station__in = stations_before_to,
            booking__to_station__in = stations_after_from,
            booking__status__in = ["confirmed","train cancelled"],
            seat__coach__coach_type = coach_type 
        ).values_list("seat_id",flat=True)
        # print(f"No:of seats booked:{len(booked)}")
        # print(f"Total no of seats:{len(seats)}")

        available_seats = seats.exclude(id__in = booked)

        if no_of_tickets>len(available_seats):
            return Response({"error":"Requested Number of tickets is not available"},status=status.HTTP_400_BAD_REQUEST)
        
        from_single_route = Trainroute.objects.get(train=train,station = from_station.id)
        to__single_route = Trainroute.objects.get(train=train,station = to_station.id)

        distance = to__single_route.distance - from_single_route.distance
        train_coach = TrainCoach.objects.filter(train=train,coach_type=coach_type).first()
        total_fare = len(passengers)*(train_coach.base_price + distance*train_coach.fare_per_km)
        booking = Booking.objects.create(
            user = request.user,
            train = train,
            from_station_id = from_station.id,
            to_station_id = to_station.id,
            status = "pending",
            journey_date = journey_date,
            total_fare = total_fare
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
            
        return Response({"message":"Successfully entered details now confirm the payment for booking the tickets"})
    
    def delete(self,request,booking_id):

        now = datetime.today()

        booking = Booking.objects.get(id=booking_id, user=request.user)
        from_route = Trainroute.objects.get(train=booking.train,station = booking.from_station)
        
        first_route = Trainroute.objects.filter(train=booking.train).order_by('stop_order').first()
        train_start_time = first_route.arrival_time
        start_date = booking.journey_date - timedelta(days=from_route.day_offset)

        train_start_date = datetime.combine(start_date,train_start_time)
        
        print(train_start_date)
        print(now)
        booking.status = "cancelled"
        
        time_difference = ((train_start_date - now).total_seconds())/3600

        if time_difference<0:
            return Response({"error":"Train already started cancellation unavailable"})

        if time_difference>48:
            booking.cancellation_percentage = 100

        elif 48>=time_difference>24:
            booking.cancellation_percentage = 50

        else:
            booking.cancellation_percentage = 0
        
        print(time_difference)
        booking.save()

        send_cancel_mail(booking)
        return Response({"message":f"Your booking with booking id {booking.id} has been cancelled successfully"})

    def put(self, request, booking_id):

        try:
            booking_row = Booking.objects.get(id=booking_id, user=request.user)
        except Booking.DoesNotExist:
            return Response({"error":"Booking with that id does not exist"})
        
        passengers = booking_row.passengers.all()
        new_journey_date = request.data.get("new_journey_date")

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
        train_schedule_days = booking_row.train.schedule_days

        if day_name not in train_schedule_days:
            return Response({"error": "Train doesen't run on this day"}, status=status.HTTP_400_BAD_REQUEST)

        if new_journey_date:
            coaches = TrainCoach.objects.filter(
                train=booking_row.train,
                coach_type=passengers[0].seat.coach.coach_type
            )
            # print(coaches)
            # available_seats = []
            total_seats = Seat.objects.filter(coach__in = coaches)

            booked = Passenger.objects.filter(
                booking__train=booking_row.train,
                booking__journey_date=new_journey_date,
                booking__status__in=['confirmed','train cancelled'],
                booking__from_station__in=stations_before_to,
                booking__to_station__in=stations_after_from,
                seat__coach__coach_type = passengers[0].seat.coach.coach_type
            ).values_list('seat_id', flat=True)

            # print(len(total_seats))
            available_seats = total_seats.exclude(id__in = booked).values_list('id',flat=True)
            # print(len(available_seats))
            # print(len(passengers))

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

            return Response(
                {
                    "message": "Date changed successfully",
                    "booking id":booking_row.id,
                    "seat number":new_seat.seat_number,
                    "berth":new_seat.berth_type,
                    "coach number":new_seat.coach.coach_number,
                    "date":new_journey_date
            })
 
class SingleBookingView(APIView):

    permission_classes = [IsAuthenticated]
 
    def get(self,request,booking_id):
        try:
            booking = Booking.objects.get(id=booking_id)
        except Booking.DoesNotExist:
            return Response({"error":"Booking not found"},status=status.HTTP_400_BAD_REQUEST)

        serializer = BookingSerializer(booking)

        return Response(serializer.data)

class AvailabilityView(APIView):

    def get(self,request):
        train_number = request.GET.get("train_number")
        source_from = request.GET.get("from")
        destination_to = request.GET.get("to")
        date = request.GET.get("date")
        coach_type = request.GET.get("coach")

        train = Train.objects.get(train_number=train_number)
        coaches = TrainCoach.objects.filter(train=train,coach_type=coach_type)

        total_seats = Seat.objects.filter(coach__in = coaches)
        from_order = Trainroute.objects.get(train=train,station=source_from).stop_order
        to_order = Trainroute.objects.get(train=train,station=destination_to).stop_order
        stations_before_to = Trainroute.objects.filter(train=train,stop_order__lt=to_order).values_list('station_id',flat=True)
        stations_after_from = Trainroute.objects.filter(train=train,stop_order__gt=from_order).values_list('station_id',flat=True)
        
        booked = Passenger.objects.filter(
            booking__train = train,
            booking__from_station__in = stations_before_to,
            booking__to_station__in = stations_after_from,
            booking__journey_date = date,
            booking__status__in = ['confirmed','train cancelled'] 
        ).values_list("seat_id",flat=True)

        # print(f"Total seats are:{len(total_seats)}")
        # print(f"Total booked seats are:{len(booked)}")

        # print(booked)
        # print(total_seats)
        available_seats = total_seats.exclude(id__in=booked)
        # print(len(available_seats))

        return Response({"message":f"There are {len(available_seats)} seats available for booking"})

class AdminDashboardviewset(viewsets.ModelViewSet):
    permission_classes = [isAdmin,IsAuthenticated]

    queryset = Booking.objects.all()
    serializer_class = BookingSerializer

    @action(detail=False,methods=['get'])
    def statistics(self,request):
        queryset = self.get_queryset()
        active_bookings = queryset.filter(status='confirmed').count()
        cancelled_bookings = queryset.filter(status='cancelled').count()
        train_cancelled_bookings = queryset.filter(status='train cancelled').count()
        total_bookings = queryset.count()
        cancellation_ratio = round((cancelled_bookings/total_bookings)*100,2)

        month_mapping = {1:'January', 2:'February', 3:'March', 4:'April', 5:'May', 6:'June',
                         7:'July', 8:'August', 9:'September', 10:'October', 11:'November', 12:'December'}
        
        month_wise_total_bookings = queryset.annotate(month=ExtractMonth('booking_date_time')).annotate(
            month_name=Case(
                *[When(month=i,then=Value(m)) for i,m in month_mapping.items()]
            )
        ).values('month_name').annotate(total=Count('id')).order_by('total')

        month_wise_active_bookings = queryset.filter(status='confirmed').annotate(month=ExtractMonth('booking_date_time')).annotate(month_name=Case(
            *[When(month=i, then=Value(m)) for i, m in month_mapping.items()],
            output_field=CharField()
        )).values('month_name').annotate(total=Count('id')).order_by('-total')

        month_wise_cancelled_bookings = queryset.filter(status='cancelled').annotate(month=ExtractMonth('booking_date_time')).annotate(month_name=Case(
            *[When(month=i, then=Value(m)) for i,m in month_mapping.items()],
            output_field=CharField())
        ).values('month_name').annotate(total=Count('id')).order_by('-total')

        month_wise_cancellation_ratio = queryset.annotate(month=ExtractMonth('booking_date_time')).annotate(month_name=Case(
            *[When(month=i,then=Value(m)) for i,m in month_mapping.items()],
            output_field=CharField()
        )).values('month_name').annotate(
            total_bookings=Count('id'),
            cancelled_bookings=Count('id',filter=Q(status='cancelled')),
            cancellation_ratio=Round(
                (F('cancelled_bookings') * 100.0) / F('total_bookings'),
                2,
                output_field=FloatField()
            )
        ).order_by('month_name')

        if not month_wise_cancelled_bookings:
            month_wise_cancelled_bookings = "No cancelled bookings"

        if not month_wise_active_bookings:
            month_wise_active_bookings = "No active bookings"
        
        expected_revenue = queryset.aggregate(total=Sum('total_fare'))['total']

        actual_revenue = queryset.filter(status='confirmed').aggregate(total=Sum('total_fare'))['total']

        trains_with_most_bookings = queryset.values('train__train_number','train__train_name').annotate(total=Count('id')).order_by('-total')[:5]
        monthly_actual_revenue = queryset.filter(status='confirmed').annotate(month=ExtractMonth('booking_date_time')).annotate(
            month_name=Case(
                *[When(month=i, then=Value(m)) for i,m in month_mapping.items()],
                output_field=CharField()
            )
        ).values('month_name').annotate(total=Sum('total_fare')).order_by('-total')

        monthly_expected_revenue = queryset.annotate(month=ExtractMonth('booking_date_time')).annotate(
            month_name=Case(
                *[When(month=i, then=Value(m)) for i,m in month_mapping.items()],
                output_field=CharField()
            )
        ).values('month_name').annotate(total=Sum('total_fare')).order_by('-total')

        return Response({"Total Bookings":total_bookings,
                         "Active Bookings":active_bookings,
                         "Cancelled Bookings":cancelled_bookings,
                         "Train Cancelled Bookings":train_cancelled_bookings,
                         "Month wise total bookings":month_wise_total_bookings,
                         "Month wise active bookings":month_wise_active_bookings,
                         "Month wise cancelled bookings":month_wise_cancelled_bookings,
                         "Expected Revenue in Total":expected_revenue,
                         "Actual Revenue":actual_revenue,
                         "Expected Monthly Revenue":monthly_expected_revenue,
                         "Actual Monthly Revenue":monthly_actual_revenue,
                         "Trains with most bookings":trains_with_most_bookings,
                         "Cancellation Ratio":f'{cancellation_ratio}%',
                         "Month wise cancellation ratio":month_wise_cancellation_ratio},status=status.HTTP_200_OK)

    @action(detail=False,methods=['get'])
    def daily_bookings(self,request):

        today_date = timezone.now().date()
        queryset = self.get_queryset()
        bookings = queryset.filter(booking_date_time__date=today_date,status='confirmed')
        if not bookings:
            return Response({"error":"No bookings done today"})
        serializer = DailyBookingSerializer(bookings,many=True)

        return Response(serializer.data)
    
    @action(detail=False,methods=['get'])
    def daily_reports(self,request):
        queryset = self.get_queryset()
        today_date = timezone.now().date()

        bookings = queryset.filter(booking_date_time__date=today_date).count()
        cancelled_bookings = queryset.filter(booking_date_time__date=today_date,status='cancelled').count()    
        try:
            today_cancel_ratio = round((cancelled_bookings/bookings)*100,2)
        except ZeroDivisionError:
            today_cancel_ratio = "No Cancelled Bookings today"

        yesterday_date = today_date - timedelta(days=1)
        yesterday_bookings = queryset.filter(booking_date_time__date=yesterday_date).count()
        yesterday_cancelled_bookings = queryset.filter(booking_date_time__date=yesterday_date,status='cancelled').count()

        today_confirmed_revenue = queryset.filter(booking_date_time__date=today_date,status='confirmed').aggregate(total=Sum('total_fare'))['total']
        yesterday_confirmed_revenue = queryset.filter(booking_date_time__date=yesterday_date,status='confirmed').aggregate(total=Sum('total_fare'))['total']

        if today_confirmed_revenue is None:
            today_confirmed_revenue = "No confirmed bookings today"
        if yesterday_confirmed_revenue is None:
            yesterday_confirmed_revenue = "No confirmed bookings yesterday"
        try:
            yesterday_cancel_ratio = (yesterday_cancelled_bookings/yesterday_bookings)*100
        except ZeroDivisionError:
            yesterday_cancel_ratio = "No bookings done yesterday"
        
        return Response({"Today's cancellation ratio":today_cancel_ratio,
                        "Yesterday's cancellation ratio":yesterday_cancel_ratio,
                        "Today's confirmed revenue":today_confirmed_revenue,
                        "Yesterday's confirmed revenue":yesterday_confirmed_revenue,})
    
    @action(detail=False,methods=['get'])
    def running_trains(self,request):
        today_date = timezone.now().date()
        # today_date = datetime(2025,9,11).date()

        cancelled_trains = TrainCancellation.objects.filter(cancellation_date=today_date).values_list('train_id')
        # print(cancelled_trains)

        trains_with_offset = Train.objects.exclude(id__in=cancelled_trains).annotate(max_day_offset=Max('train_route__day_offset')).values('id','max_day_offset','schedule_days')
        # print(trains_with_offset)

        trains_running_today = []

        for i in range(7):
            check_date = today_date - timedelta(days=i)
            check_day_name = check_date.strftime("%A").lower()

            record = trains_with_offset.filter(schedule_days__icontains=check_day_name,max_day_offset__gte=i).values_list('id',flat=True)

            if record.exists():
                trains_running_today.extend(j for j in record)
            
        trains = Train.objects.filter(id__in=trains_running_today)
        
        data =[]
        for train in trains:
            coach = TrainCoach.objects.filter(train=train)
            total_seats = Seat.objects.filter(coach__in=coach).count()
            booked_seats = Booking.objects.filter(
                train=train,
                journey_date=today_date,
                status='confirmed'
            ).count()

            available_seats = total_seats-booked_seats

            data.append({
                "train name":train.train_name,
                "train_number":train.train_number,
                "total seats":total_seats,
                "booked seats":booked_seats,
                "available seats":available_seats
            })

        if not trains:
            return Response({"message":"No trains are running today"},status=status.HTTP_200_OK)
        
        paginator = PageNumberPagination()
        paginator.page_size = 5

        paginator.paginate_queryset(data,request)
        return paginator.get_paginated_response(data)

 

        
































































































# class SampleView(APIView):
#     permission_classes = []

#     def get(self,request):
#         train = Train.objects.all()
#         serializer = SampleSerializer(train,many=True)
    
#         return Response(serializer.data)

#     def post(self,request):
#         serializer = SampleSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response({"created"})
    
#     def put(self,request,train_id):
#         train = Train.objects.get(id=train_id)
#         serializer = TrainSerializer(train, request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()

#         return Response("Updated",status=status.HTTP_200_OK)
    
#     def delete(self,request,train_id):
#         train = Train.objects.get(id=train_id)
#         # train.delete()
#         train.is_active = 0
#         train.save()
        
#         return Response("Deleted Successfully",status=status.HTTP_204_NO_CONTENT)