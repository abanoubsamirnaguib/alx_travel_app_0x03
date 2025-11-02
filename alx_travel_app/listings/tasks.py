from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)


@shared_task
def send_payment_confirmation_email(booking_id: int, payment_id: int):
    """
    Send payment confirmation email to user
    
    Args:
        booking_id: ID of the booking
        payment_id: ID of the payment
    """
    try:
        from .models import Booking, Payment
        
        booking = Booking.objects.select_related('listing', 'user').get(id=booking_id)
        payment = Payment.objects.get(id=payment_id)
        
        # Email context
        context = {
            'user': booking.user,
            'booking': booking,
            'payment': payment,
            'listing': booking.listing,
        }
        
        # Create email content (you can create HTML templates later)
        subject = f'Booking Confirmation - {booking.listing.title}'
        
        html_message = f"""
        <h2>Booking Confirmation</h2>
        <p>Dear {booking.user.first_name or booking.user.username},</p>
        
        <p>Your payment has been successfully processed! Here are your booking details:</p>
        
        <div style="border: 1px solid #ddd; padding: 15px; margin: 10px 0;">
            <h3>Booking Details</h3>
            <p><strong>Property:</strong> {booking.listing.title}</p>
            <p><strong>Location:</strong> {booking.listing.location}</p>
            <p><strong>Check-in:</strong> {booking.check_in}</p>
            <p><strong>Check-out:</strong> {booking.check_out}</p>
            <p><strong>Guests:</strong> {booking.guests}</p>
            <p><strong>Total Amount:</strong> {payment.amount} {payment.currency}</p>
            <p><strong>Payment Reference:</strong> {payment.payment_reference}</p>
            <p><strong>Booking Status:</strong> {booking.get_status_display()}</p>
        </div>
        
        <p>Thank you for choosing ALX Travel App!</p>
        
        <p>Best regards,<br>The ALX Travel Team</p>
        """
        
        plain_message = strip_tags(html_message)
        
        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[booking.user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Payment confirmation email sent to {booking.user.email} for booking {booking_id}")
        
    except Exception as e:
        logger.error(f"Failed to send payment confirmation email for booking {booking_id}: {str(e)}")
        raise


@shared_task
def send_payment_failed_email(booking_id: int, payment_id: int):
    """
    Send payment failure notification email to user
    
    Args:
        booking_id: ID of the booking
        payment_id: ID of the payment
    """
    try:
        from .models import Booking, Payment
        
        booking = Booking.objects.select_related('listing', 'user').get(id=booking_id)
        payment = Payment.objects.get(id=payment_id)
        
        # Email context
        subject = f'Payment Failed - {booking.listing.title}'
        
        html_message = f"""
        <h2>Payment Failed</h2>
        <p>Dear {booking.user.first_name or booking.user.username},</p>
        
        <p>Unfortunately, your payment for the following booking could not be processed:</p>
        
        <div style="border: 1px solid #ddd; padding: 15px; margin: 10px 0;">
            <h3>Booking Details</h3>
            <p><strong>Property:</strong> {booking.listing.title}</p>
            <p><strong>Location:</strong> {booking.listing.location}</p>
            <p><strong>Check-in:</strong> {booking.check_in}</p>
            <p><strong>Check-out:</strong> {booking.check_out}</p>
            <p><strong>Guests:</strong> {booking.guests}</p>
            <p><strong>Total Amount:</strong> {payment.amount} {payment.currency}</p>
            <p><strong>Payment Reference:</strong> {payment.payment_reference}</p>
        </div>
        
        <p>Please try again or contact our support team if you continue to experience issues.</p>
        
        <p>Best regards,<br>The ALX Travel Team</p>
        """
        
        plain_message = strip_tags(html_message)
        
        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[booking.user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Payment failed email sent to {booking.user.email} for booking {booking_id}")
        
    except Exception as e:
        logger.error(f"Failed to send payment failed email for booking {booking_id}: {str(e)}")
        raise