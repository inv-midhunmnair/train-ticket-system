from django.contrib import admin
from django.urls import path, include

from core.views import ForgotPasswordOTPView, LoginView, ResetPasswordView, VerifyOTPView,LoginOTPView, VerifyPasswordOTPView


urlpatterns = [
    path('admin/', admin.site.urls),
    # path('payment/',include('payment.urls')),
    path('users/', include('core.urls')),
    path('login/',LoginOTPView.as_view()),
    path('verify-otp/',VerifyOTPView.as_view()),
    path('easy-login/', LoginView.as_view()),
    path('forgot-password/',ForgotPasswordOTPView.as_view()),
    path('verify-password-otp/', VerifyPasswordOTPView.as_view(),name='link-generation'),
    path('reset-password/',ResetPasswordView.as_view(),name='reset-password')
]
