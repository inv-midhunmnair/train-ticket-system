from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import StationViewset, TrainDetailsViewset, TrainroutesViewset, UserViewset,VerifyEmailView,GetUserViewset,SearchResultsview

router = DefaultRouter()

router.register(r'users', UserViewset, basename='users')
router.register(r'profile', GetUserViewset, basename='profile')
router.register(r'trains', TrainDetailsViewset)
router.register(r'train-routes',TrainroutesViewset)
router.register(r'stations', StationViewset)
urlpatterns = [
    path('', include(router.urls)),
    path('verify-email', VerifyEmailView.as_view(), name='verify-email'),
    path('search/', SearchResultsview.as_view())
]