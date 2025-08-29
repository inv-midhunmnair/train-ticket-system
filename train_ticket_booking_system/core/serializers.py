from .models import User, Train, Station, Trainroute
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
        fields = '__all__'
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
        exclude = ['password','email']

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
    
            
            
