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
    forgot_password_otp = models.IntegerField(blank=True, null=True)
    forgot_password_otp_expiry = models.DateTimeField(blank=True, null=True)

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
    station = models.ForeignKey(Station, on_delete=models.CASCADE, related_name='train_routes')
    stop_order = models.PositiveIntegerField()
    arrival_time = models.TimeField()
    departure_time = models.TimeField()
    day_offset = models.PositiveIntegerField()
    distance = models.IntegerField(null=True) 

    REQUIRED_FIELDS = ['train_id','station_id','stop_order','arrival_time','departure_time','day_offset']

class TrainCoach(models.Model):
    train = models.ForeignKey(Train, on_delete=models.CASCADE)
    capacity = models.IntegerField()
    coach_type = models.CharField(max_length=50)
    coach_number = models.CharField(max_length=10)
    base_price = models.IntegerField(null=True)
    fare_per_km = models.IntegerField(null=True)

    def __str__(self):
        return f"{self.coach_number}"

class Seat(models.Model):
    coach = models.ForeignKey(TrainCoach,on_delete=models.CASCADE)
    berth_type = models.CharField(max_length=50)
    seat_number = models.IntegerField()

    def __str__(self):
        return f"{self.seat_number} and {self.berth_type} from {self.coach.coach_number}"

class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    train = models.ForeignKey(Train, on_delete=models.CASCADE)
    from_station = models.ForeignKey(Station, on_delete=models.CASCADE,related_name="from_bookings")
    to_station = models.ForeignKey(Station, on_delete=models.CASCADE,related_name="to_bookings")
    journey_date = models.DateField()
    status = models.CharField(max_length=20)

class Passenger(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='passengers')
    seat = models.ForeignKey(Seat, on_delete=models.CASCADE)
    passenger_name = models.CharField(max_length=100)
    passenger_age = models.IntegerField()
    passenger_gender = models.CharField(max_length=15)

    def __str__(self):
        return f"{self.seat.coach}"