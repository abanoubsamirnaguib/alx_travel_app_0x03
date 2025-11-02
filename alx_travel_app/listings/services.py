import requests
import logging
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from typing import Dict, Any, Optional
from .models import Payment, Booking

logger = logging.getLogger(__name__)


class ChapaPaymentService:
    """Service class to handle Chapa payment integration"""
    
    def __init__(self):
        self.secret_key = settings.CHAPA_SECRET_KEY
        self.base_url = settings.CHAPA_BASE_URL
        
        if not self.secret_key:
            raise ImproperlyConfigured("CHAPA_SECRET_KEY is not configured")
    
    def get_headers(self) -> Dict[str, str]:
        """Get headers for Chapa API requests"""
        return {
            'Authorization': f'Bearer {self.secret_key}',
            'Content-Type': 'application/json',
        }
    
    def initiate_payment(self, booking: Booking, return_url: str, callback_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Initiate payment with Chapa API
        
        Args:
            booking: Booking instance
            return_url: URL to redirect user after payment
            callback_url: Optional webhook URL for payment notifications
            
        Returns:
            Dict containing payment initiation response
        """
        try:
            # Create or get payment record
            payment, created = Payment.objects.get_or_create(
                booking=booking,
                defaults={
                    'amount': booking.total_price,
                    'currency': 'ETB',
                }
            )
            
            # Prepare payment data
            payment_data = {
                'amount': str(payment.amount),
                'currency': payment.currency,
                'email': booking.user.email,
                'first_name': booking.user.first_name or booking.user.username,
                'last_name': booking.user.last_name or '',
                'phone_number': getattr(booking.user, 'phone_number', ''),
                'tx_ref': str(payment.payment_reference),
                'return_url': return_url,
                'description': f'Payment for booking {booking.id} - {booking.listing.title}',
                'meta': {
                    'booking_id': booking.id,
                    'listing_title': booking.listing.title,
                },
            }
            
            if callback_url:
                payment_data['callback_url'] = callback_url
            
            # Make API request to Chapa
            response = requests.post(
                f'{self.base_url}/transaction/initialize',
                json=payment_data,
                headers=self.get_headers(),
                timeout=30
            )
            
            response_data = response.json()
            
            if response.status_code == 200 and response_data.get('status') == 'success':
                # Update payment record with Chapa response
                payment.checkout_url = response_data['data']['checkout_url']
                payment.chapa_data = response_data
                payment.save()
                
                logger.info(f"Payment initiated successfully for booking {booking.id}")
                
                return {
                    'status': 'success',
                    'payment_reference': str(payment.payment_reference),
                    'checkout_url': payment.checkout_url,
                    'data': response_data
                }
            else:
                logger.error(f"Payment initiation failed: {response_data}")
                payment.status = Payment.STATUS_FAILED
                payment.chapa_data = response_data
                payment.save()
                
                return {
                    'status': 'error',
                    'message': response_data.get('message', 'Payment initiation failed'),
                    'data': response_data
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error during payment initiation: {str(e)}")
            return {
                'status': 'error',
                'message': 'Network error occurred. Please try again.',
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error during payment initiation: {str(e)}")
            return {
                'status': 'error',
                'message': 'An unexpected error occurred. Please try again.',
                'error': str(e)
            }
    
    def verify_payment(self, tx_ref: str) -> Dict[str, Any]:
        """
        Verify payment status with Chapa API
        
        Args:
            tx_ref: Transaction reference (payment_reference)
            
        Returns:
            Dict containing verification response
        """
        try:
            # Get payment record
            payment = Payment.objects.get(payment_reference=tx_ref)
            
            # Make verification request to Chapa
            response = requests.get(
                f'{self.base_url}/transaction/verify/{tx_ref}',
                headers=self.get_headers(),
                timeout=30
            )
            
            response_data = response.json()
            
            if response.status_code == 200 and response_data.get('status') == 'success':
                transaction_data = response_data['data']
                
                # Update payment status based on Chapa response
                chapa_status = transaction_data.get('status')
                
                if chapa_status == 'success':
                    payment.status = Payment.STATUS_COMPLETED
                    payment.transaction_id = transaction_data.get('reference')
                    payment.chapa_reference = transaction_data.get('trx_ref')
                    
                    # Update booking status
                    payment.booking.status = Booking.STATUS_CONFIRMED
                    payment.booking.save()
                    
                    logger.info(f"Payment verified successfully for booking {payment.booking.id}")
                    
                elif chapa_status == 'failed':
                    payment.status = Payment.STATUS_FAILED
                else:
                    payment.status = Payment.STATUS_PENDING
                
                # Store updated Chapa data
                payment.chapa_data = response_data
                payment.save()
                
                return {
                    'status': 'success',
                    'payment_status': payment.status,
                    'data': response_data
                }
            else:
                logger.error(f"Payment verification failed: {response_data}")
                return {
                    'status': 'error',
                    'message': response_data.get('message', 'Payment verification failed'),
                    'data': response_data
                }
                
        except Payment.DoesNotExist:
            logger.error(f"Payment not found for tx_ref: {tx_ref}")
            return {
                'status': 'error',
                'message': 'Payment record not found',
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error during payment verification: {str(e)}")
            return {
                'status': 'error',
                'message': 'Network error occurred. Please try again.',
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error during payment verification: {str(e)}")
            return {
                'status': 'error',
                'message': 'An unexpected error occurred. Please try again.',
                'error': str(e)
            }
    
    def handle_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle webhook notifications from Chapa
        
        Args:
            webhook_data: Webhook payload from Chapa
            
        Returns:
            Dict containing webhook processing result
        """
        try:
            tx_ref = webhook_data.get('tx_ref')
            
            if not tx_ref:
                return {
                    'status': 'error',
                    'message': 'Missing tx_ref in webhook data'
                }
            
            # Verify the payment using the tx_ref
            verification_result = self.verify_payment(tx_ref)
            
            if verification_result['status'] == 'success':
                logger.info(f"Webhook processed successfully for tx_ref: {tx_ref}")
                return {
                    'status': 'success',
                    'message': 'Webhook processed successfully'
                }
            else:
                logger.error(f"Webhook processing failed for tx_ref: {tx_ref}")
                return verification_result
                
        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}")
            return {
                'status': 'error',
                'message': 'Error processing webhook',
                'error': str(e)
            }