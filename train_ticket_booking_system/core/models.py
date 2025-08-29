from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.
class User(AbstractUser):
    role = models.IntegerField(choices=[(0,'user'),(1,'admin')])
    is_email_verified = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=20)
    otp = models.IntegerField(blank=True, null=True)
    otp_expires_at = models.DateTimeField(blank=True, null=True)
    email = models.EmailField(unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username','role','first_name','last_name','phone_number','password']

class Train(models.Model):
    train_name = models.CharField(max_length=50)
    train_number = models.IntegerField(unique=True)
    schedule_days = models.CharField()
    is_active = models.BooleanField(default=True)

    REQUIRED_FIELDS = ['train_name','train_number','schedule_days']

class Station(models.Model):
    station_code = models.CharField(max_length=50, unique=True)
    station_name = models.CharField(max_length=50, unique=True)

    REQUIRED_FIELDS = ['station_code', 'station_name']

class Trainroute(models.Model):
    train = models.ForeignKey(Train, on_delete=models.CASCADE, related_name="train_route")
    station = models.ForeignKey(Station, on_delete=models.CASCADE)
    stop_order = models.PositiveIntegerField()
    arrival_time = models.TimeField()
    departure_time = models.TimeField()
    day_offset = models.PositiveIntegerField()

    REQUIRED_FIELDS = ['train_id','station_id','stop_order','arrival_time','departure_time','day_offset']
