from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import AdminDashboardviewset, BookingView, SingleBookingView,AvailabilityView, StationViewset, TrainDetailsViewset, TrainTrackingView, TrainroutesViewset, UserViewset,VerifyEmailView,GetUserViewset,SearchResultsview

router = DefaultRouter()

router.register(r'users', UserViewset, basename='users')
router.register(r'profile', GetUserViewset, basename='profile')
router.register(r'trains', TrainDetailsViewset)
router.register(r'train-routes',TrainroutesViewset)
router.register(r'stations', StationViewset)
router.register(r'admin-dashboard', AdminDashboardviewset)
urlpatterns = [
    path('', include(router.urls)),
    path('verify-email', VerifyEmailView.as_view(), name='verify-email'),
    path('search/', SearchResultsview.as_view()),
    path('status/',TrainTrackingView.as_view()),
    path('booking/',BookingView.as_view()),
    path('booking/<int:booking_id>/',BookingView.as_view()),
    path('single-booking/<int:booking_id>/',SingleBookingView.as_view()),
    path('availability/',AvailabilityView.as_view()),
    # path('sample/',SampleView.as_view()),
    # path('sample/<int:train_id>/',SampleView.as_view())
]