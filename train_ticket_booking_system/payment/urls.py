from django.urls import path, include
from .views import PaymentInitiateView,VerifyPaymentView, RefundView

urlpatterns = [
    path('initiate/',PaymentInitiateView.as_view()),
    path('verify-payment/', VerifyPaymentView.as_view()),
    path('refund/',RefundView.as_view())
]