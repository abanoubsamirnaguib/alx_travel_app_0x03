from django.contrib import admin
from .models import Listing, Booking, Review, Payment


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ['title', 'location', 'price_per_night', 'max_guests', 'is_available', 'host', 'created_at']
    list_filter = ['is_available', 'created_at', 'location']
    search_fields = ['title', 'location', 'description']
    list_editable = ['is_available']


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['id', 'listing', 'user', 'check_in', 'check_out', 'guests', 'total_price', 'status', 'created_at']
    list_filter = ['status', 'created_at', 'check_in']
    search_fields = ['listing__title', 'user__username', 'user__email']
    list_editable = ['status']
    date_hierarchy = 'check_in'


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['listing', 'user', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['listing__title', 'user__username', 'comment']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['payment_reference', 'booking', 'amount', 'currency', 'status', 'transaction_id', 'created_at']
    list_filter = ['status', 'currency', 'created_at']
    search_fields = ['payment_reference', 'transaction_id', 'chapa_reference', 'booking__user__email']
    readonly_fields = ['payment_reference', 'transaction_id', 'chapa_reference', 'chapa_data', 'created_at', 'updated_at']
    list_editable = ['status']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('booking', 'amount', 'currency', 'status')
        }),
        ('Payment Details', {
            'fields': ('payment_reference', 'transaction_id', 'chapa_reference', 'checkout_url')
        }),
        ('Chapa Data', {
            'fields': ('chapa_data',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
