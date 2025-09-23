from django.db import models
from core.models import Booking
# Create your models here.

class Payment(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)
    payment_status = models.CharField(max_length=20)
    payment_id = models.CharField(max_length=100, null=True, blank=True)
    order_id = models.CharField(max_length=100,null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Refund(models.Model):
    booking = models.ForeignKey(Booking,on_delete=models.CASCADE)
    status = models.CharField()
    payment = models.ForeignKey(Payment,on_delete=models.CASCADE)
    refund_amount = models.FloatField(default=0)
    refund_id = models.CharField()
    requested_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)