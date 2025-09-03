from urllib import response
from django.shortcuts import render
from django.urls import reverse
from django.conf import settings
from .models import Train, User,Station, Trainroute
from rest_framework.views import APIView
from rest_framework import viewsets, filters
from .serializers import TrainSearchSerializer, TrainSerializer, UserSerializer, UpdateSerializer,StationSerializer,GetUserSerializer, TrainrouteSerializer
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime, timedelta
from django.utils import timezone
import random
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .permissions import isAdmin, isUser
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.db.models import Q,F
from django.core.exceptions import ObjectDoesNotExist




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
            fail_silently=False
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
    # permission_classes = [IsAuthenticated, isAdmin]

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
        train.is_active = True
        train.save()

        return Response({"message":"Successfully unblocked the train"})
     
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
        train_name = request.GET.get("train_name")
        train_number = request.GET.get("train_number")

        queryset = Trainroute.objects.prefetch_related('train').prefetch_related('station').all()
        if train_name:
            queryset = Trainroute.objects.filter(train__train_name__icontains=train_name)
        if train_number:
            queryset = Trainroute.objects.filter(train__train_number=train_number)
        
        if source_from or destination_to or date:
            from_queryset = Trainroute.objects.filter(station__station_name__iexact = source_from).values('train_id','stop_order','day_offset','train__schedule_days')
            to_queryset = Trainroute.objects.filter(station__station_name__iexact=destination_to).values('train_id','stop_order','day_offset','train__schedule_days')

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

                queryset = Trainroute.objects.filter(train_id__in = valid_train_ids, train__schedule_days__icontains = day_name)

            elif date:
                date = datetime.strptime(date,"%Y-%m-%d")
                print(date)

                day_name = date.strftime("%A")
                print(day_name)

                queryset = Trainroute.objects.filter(train__schedule_days__icontains = day_name)
            elif source_from and destination_to:
                queryset = Trainroute.objects.filter(train_id__in=matching_train_id)

        serializer = TrainSearchSerializer(queryset, many=True)
        return Response(serializer.data)
