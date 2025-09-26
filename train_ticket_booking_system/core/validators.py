from rest_framework import serializers
import re
from .models import Station, Train, User
from datetime import datetime

def validate_name(name):
    if len(name)>=2 and isinstance(name,str):
        return name
    else:
        raise serializers.ValidationError("Name must be string and should be more than 2 characters")

def validate_phone_number(number):
    if len(number)>=10 and re.match("^(?:(?:\+|0{0,2})91(\s*[\-]\s*)?|[0]?)?[6789]\d{9}$", number):
        return number
    else:
        raise serializers.ValidationError("Incorrect phone number format")

def validate_email(email):
    if User.objects.filter(email=email).exists():
        raise serializers.ValidationError("Email already exists")

def validate_username(username):
    if len(username)<2 or not(re.match(r'^[a-zA-Z0-9_]{3,30}$',username)):
        raise serializers.ValidationError("Please enter a valid username")
    if User.objects.filter(username=username).exists():
        raise serializers.ValidationError("Username already exists")

def validate_password(password):
    if len(password)<6:
        raise serializers.ValidationError("Password should be a minimum of six characters")
    if not(re.match(r'^\S+$',password)):
        raise serializers.ValidationError("No spaces in between")

def validate_train_name(train_name):
     if not re.match(r'^[A-Za-z ]+$', train_name):
            raise serializers.ValidationError("Train name must contain only letters and spaces.")
     if Train.objects.filter(train_name=train_name):
         raise serializers.ValidationError("Train with this name already exists")
     return train_name

def validate_train_number(train_number):
    if Train.objects.filter(train_number=train_number):
        raise serializers.ValidationError("Train number already exists")
    if train_number<5:
        raise serializers.ValidationError("Train number must be more than 5 characters")
def validate_train_time(validated_data):
    if validated_data['arrival_time']>=validated_data['departure_time']:
        raise serializers.ValidationError("Arrival time cannot be late than departure time")

def validate_station_name(station_name):
    if len(station_name)<3:
        raise serializers.ValidationError("Please entere valid station name more than 3 characters")
    if Station.objects.filter(station_name=station_name):
        raise serializers.ValidationError("Station Name already exists")

def validate_station_code(station_code):
    if len(station_code)<2:
        raise serializers.ValidationError("Please enter station code greater than 2 characters")
    if Station.objects.filter(station_code=station_code):
        raise serializers.ValidationError("Station code already exists")
