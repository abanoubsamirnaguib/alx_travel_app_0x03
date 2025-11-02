from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Listing, Booking, Payment


User = get_user_model()


class HostSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]


class ListingSerializer(serializers.ModelSerializer):
    host = HostSerializer(read_only=True)

    class Meta:
        model = Listing
        fields = [
            "id",
            "title",
            "description",
            "location",
            "price_per_night",
            "max_guests",
            "is_available",
            "image_url",
            "host",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class BookingSerializer(serializers.ModelSerializer):
    listing = serializers.PrimaryKeyRelatedField(queryset=Listing.objects.all())
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Booking
        fields = [
            "id",
            "listing",
            "user",
            "check_in",
            "check_out",
            "guests",
            "total_price",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        check_in = attrs.get("check_in")
        check_out = attrs.get("check_out")
        if check_in and check_out and check_in >= check_out:
            raise serializers.ValidationError("check_in must be before check_out")
        return attrs


class PaymentSerializer(serializers.ModelSerializer):
    booking = serializers.PrimaryKeyRelatedField(queryset=Booking.objects.all())
    
    class Meta:
        model = Payment
        fields = [
            "id",
            "booking",
            "transaction_id",
            "chapa_reference",
            "payment_reference",
            "amount",
            "currency",
            "status",
            "checkout_url",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "transaction_id", "chapa_reference", "payment_reference", "checkout_url", "created_at", "updated_at"]


class PaymentInitiateSerializer(serializers.Serializer):
    booking_id = serializers.IntegerField()
    return_url = serializers.URLField()
    callback_url = serializers.URLField(required=False)
    
    def validate_booking_id(self, value):
        try:
            booking = Booking.objects.get(id=value)
            # Check if payment already exists for this booking
            if hasattr(booking, 'payment'):
                raise serializers.ValidationError("Payment already exists for this booking")
            return value
        except Booking.DoesNotExist:
            raise serializers.ValidationError("Booking not found")
