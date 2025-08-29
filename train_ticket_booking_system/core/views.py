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

        if user is None:
            return response({"error":"Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        
        minutes = 10
        otp = random.randint(100000,999999)
        expiry = timezone.now() .now()+ timedelta(minutes=minutes)

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
            return Response({"error":"You are either blocked or email isn't verified"})
        
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
        if source_from:
            # day_name = datetime.strptime(date, "%Y-%m-%d").strftime("%A")
            # queryset = Trainroute.objects.filter(train__schedule_days__icontains = day_name)

            from_queryset = Trainroute.objects.filter(station__station_name__iexact = source_from).values('stop_order','train_id')
            to_queryset = Trainroute.objects.filter(station__station_name__iexact = destination_to).values('stop_order','train_id')

            print(from_queryset)
            print(to_queryset)

            to_dict = {item['train_id']: item['stop_order'] for item in to_queryset}

            valid_train_ids = [
                item['train_id'] 
                for item in from_queryset
                if item['train_id'] in to_dict and item['stop_order'] < to_dict[item['train_id']]
            ]

            queryset = Trainroute.objects.filter(train_id__in=valid_train_ids)
        
        serializer = TrainSearchSerializer(queryset, many=True)
        return Response(serializer.data)
