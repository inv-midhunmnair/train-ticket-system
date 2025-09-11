from .models import Booking, Passenger, Seat, TrainCoach, User, Train, Station, Trainroute
from rest_framework import serializers
from .validators import *

class UserSerializer(serializers.ModelSerializer):

    role_display = serializers.SerializerMethodField()

    def get_role_display(self, obj):
        if obj.role == 0:
            return "user"
        else:
            return "admin"

    phone_number = serializers.CharField(validators = [validate_phone_number])
    first_name = serializers.CharField(validators = [validate_name])
    last_name = serializers.CharField(validators = [validate_name])
    email = serializers.EmailField(validators = [validate_email])
    username = serializers.CharField(validators = [validate_username])

    class Meta:
        model = User
        fields = ['id','email','phone_number','first_name','last_name','username','role_display']
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()

        return user

class UpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','username','first_name','last_name','phone_number']

class GetUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username','first_name', 'last_name', 'email', 'phone_number']

class StationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Station 
        fields = '__all__'

class TrainrouteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Trainroute
        fields = '__all__'
    
    def create(self, validated_data):
        route,created_bool = Trainroute.objects.get_or_create(**validated_data)
        if not created_bool:
            raise serializers.ValidationError({"error":"row already exists"})
        return route

class TrainSerializer(serializers.ModelSerializer):

    class Meta:
        model = Train
        fields = '__all__'

class TrainSearchSerializer(serializers.ModelSerializer):

    train = TrainSerializer(read_only=True)
    station = StationSerializer(read_only=True)

    class Meta:
        model = Trainroute
        fields = '__all__'

class CoachSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainCoach
        fields = ['coach_type','coach_number']

class SeatSerializer(serializers.ModelSerializer):
    coach = CoachSerializer()
    class Meta:
        model = Seat
        fields = ['seat_number','berth_type','coach']

class PassengerSerializer(serializers.ModelSerializer):
    seat = SeatSerializer()
    class Meta:
        model = Passenger
        fields = ['passenger_name','passenger_age','passenger_gender','seat']

class BookingStationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Station
        fields = ['station_name']

class BookingTrainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Train
        fields = ['train_name','train_number']

class BookingSerializer(serializers.ModelSerializer):

    train = BookingTrainSerializer()
    from_station = BookingStationSerializer()
    to_station = BookingStationSerializer()
    passengers = PassengerSerializer(many=True)

    from_arrival_time = serializers.SerializerMethodField()
    to_arrival_time = serializers.SerializerMethodField()
    class Meta:
        model = Booking
        fields = ['id','journey_date','status','train','from_station','to_station','passengers','from_arrival_time','to_arrival_time'] 

    def get_from_arrival_time(self,obj):
        route = obj.train.train_route.filter(station=obj.from_station).first()
        return route.arrival_time
    
    def get_to_arrival_time(self,obj):
        route = obj.train.train_route.filter(station=obj.to_station).first()
        return route.arrival_time

class InputPassengerSerializer(serializers.Serializer):
    name = serializers.CharField()
    age =serializers.IntegerField()
    gender = serializers.CharField()

class NewbookingSerializer(serializers.Serializer):

    train_number = serializers.IntegerField()
    from_id = serializers.IntegerField()
    to_id = serializers.IntegerField()
    date = serializers.DateField()
    coach_type = serializers.CharField()
    passengers = InputPassengerSerializer(many=True)
    