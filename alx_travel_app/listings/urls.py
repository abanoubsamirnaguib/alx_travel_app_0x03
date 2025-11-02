from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import ListingViewSet, BookingViewSet, PaymentViewSet, chapa_webhook

app_name = "listings"

router = DefaultRouter()
router.register(r"listings", ListingViewSet, basename="listing")
router.register(r"bookings", BookingViewSet, basename="booking")
router.register(r"payments", PaymentViewSet, basename="payment")

urlpatterns = router.urls + [
    path('chapa/webhook/', chapa_webhook, name='chapa-webhook'),
]
