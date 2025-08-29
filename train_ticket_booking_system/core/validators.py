from rest_framework import serializers
import re
from .models import User

def validate_name(name):
    if len(name)>=2 and isinstance(name,str):
        return name
    else:
        raise serializers.ValidationError("Name must be string and should be more than 2 characters")

def validate_phone_number(number):
    if len(number)>=10 and re.match("^(?:(?:\+|0{0,2})91(\s*[\-]\s*)?|[0]?)?[789]\d{9}$", number):
        return number
    else:
        raise serializers.ValidationError("Incorrect phone number format")

def validate_email(email):
    if User.objects.filter(email=email).exists():
        raise serializers.ValidationError("Email already exists")

def validate_username(username):
    if User.objects.filter(username=username).exists():
        raise serializers.ValidationError("Username already exists")