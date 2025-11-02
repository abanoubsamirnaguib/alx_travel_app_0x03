from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse
import json
import logging

from .models import Listing, Booking, Payment
from .serializers import ListingSerializer, BookingSerializer, PaymentSerializer, PaymentInitiateSerializer
from .services import ChapaPaymentService
from .tasks import send_payment_confirmation_email, send_payment_failed_email, send_booking_confirmation_email

logger = logging.getLogger(__name__)


class ListingViewSet(viewsets.ModelViewSet):
	"""Simple CRUD for Listing.

	Anyone can list and retrieve. Auth required to create/update/delete.
	Host is set automatically from the logged in user on create.
	"""

	queryset = Listing.objects.all()
	serializer_class = ListingSerializer
	permission_classes = [IsAuthenticatedOrReadOnly]

	def perform_create(self, serializer):  # set host automatically
		serializer.save(host=self.request.user)


class BookingViewSet(viewsets.ModelViewSet):
	"""Simple CRUD for Booking.

	Basic permissions: read for everyone, write requires auth.
	In a real app we'd restrict updates/cancels to owner or host.
	"""

	queryset = Booking.objects.all()
	serializer_class = BookingSerializer
	permission_classes = [IsAuthenticatedOrReadOnly]

	def perform_create(self, serializer):  # set user automatically if not provided
		# If client doesn't send user, fall back to request.user
		user = serializer.validated_data.get("user") or self.request.user
		booking = serializer.save(user=user)
		
		# Send booking confirmation email asynchronously
		send_booking_confirmation_email.delay(booking.id)


class PaymentViewSet(viewsets.ModelViewSet):
	"""ViewSet for handling payment operations"""
	
	queryset = Payment.objects.all()
	serializer_class = PaymentSerializer
	permission_classes = [IsAuthenticated]
	
	def get_queryset(self):
		# Users can only see their own payments
		if self.request.user.is_staff:
			return Payment.objects.all()
		return Payment.objects.filter(booking__user=self.request.user)
	
	@action(detail=False, methods=['post'], url_path='initiate')
	def initiate_payment(self, request):
		"""
		Initiate payment for a booking
		POST /api/payments/initiate/
		"""
		serializer = PaymentInitiateSerializer(data=request.data)
		
		if not serializer.is_valid():
			return Response(
				{'error': 'Invalid data', 'details': serializer.errors},
				status=status.HTTP_400_BAD_REQUEST
			)
		
		booking_id = serializer.validated_data['booking_id']
		return_url = serializer.validated_data['return_url']
		callback_url = serializer.validated_data.get('callback_url')
		
		try:
			booking = get_object_or_404(Booking, id=booking_id)
			
			# Check if user owns the booking
			if booking.user != request.user and not request.user.is_staff:
				return Response(
					{'error': 'Permission denied'},
					status=status.HTTP_403_FORBIDDEN
				)
			
			# Check if booking is in valid state for payment
			if booking.status != Booking.STATUS_PENDING:
				return Response(
					{'error': 'Booking is not in a valid state for payment'},
					status=status.HTTP_400_BAD_REQUEST
				)
			
			# Initialize Chapa payment service
			chapa_service = ChapaPaymentService()
			
			# Initiate payment
			result = chapa_service.initiate_payment(
				booking=booking,
				return_url=return_url,
				callback_url=callback_url
			)
			
			if result['status'] == 'success':
				return Response({
					'message': 'Payment initiated successfully',
					'payment_reference': result['payment_reference'],
					'checkout_url': result['checkout_url'],
				}, status=status.HTTP_201_CREATED)
			else:
				return Response({
					'error': 'Payment initiation failed',
					'message': result.get('message', 'Unknown error')
				}, status=status.HTTP_400_BAD_REQUEST)
				
		except Exception as e:
			logger.error(f"Error initiating payment: {str(e)}")
			return Response(
				{'error': 'Internal server error'},
				status=status.HTTP_500_INTERNAL_SERVER_ERROR
			)
	
	@action(detail=False, methods=['post'], url_path='verify')
	def verify_payment(self, request):
		"""
		Verify payment status
		POST /api/payments/verify/
		"""
		tx_ref = request.data.get('tx_ref')
		
		if not tx_ref:
			return Response(
				{'error': 'tx_ref is required'},
				status=status.HTTP_400_BAD_REQUEST
			)
		
		try:
			# Initialize Chapa payment service
			chapa_service = ChapaPaymentService()
			
			# Verify payment
			result = chapa_service.verify_payment(tx_ref)
			
			if result['status'] == 'success':
				# Get payment record
				payment = Payment.objects.get(payment_reference=tx_ref)
				
				# Send appropriate email based on payment status
				if payment.status == Payment.STATUS_COMPLETED:
					send_payment_confirmation_email.delay(
						payment.booking.id, 
						payment.id
					)
				elif payment.status == Payment.STATUS_FAILED:
					send_payment_failed_email.delay(
						payment.booking.id, 
						payment.id
					)
				
				return Response({
					'message': 'Payment verification completed',
					'payment_status': payment.status,
					'booking_status': payment.booking.status,
				}, status=status.HTTP_200_OK)
			else:
				return Response({
					'error': 'Payment verification failed',
					'message': result.get('message', 'Unknown error')
				}, status=status.HTTP_400_BAD_REQUEST)
				
		except Payment.DoesNotExist:
			return Response(
				{'error': 'Payment not found'},
				status=status.HTTP_404_NOT_FOUND
			)
		except Exception as e:
			logger.error(f"Error verifying payment: {str(e)}")
			return Response(
				{'error': 'Internal server error'},
				status=status.HTTP_500_INTERNAL_SERVER_ERROR
			)


@method_decorator(csrf_exempt, name='dispatch')
def chapa_webhook(request):
	"""
	Handle Chapa webhook notifications
	POST /api/chapa/webhook/
	"""
	if request.method != 'POST':
		return JsonResponse({'error': 'Method not allowed'}, status=405)
	
	try:
		# Parse webhook data
		webhook_data = json.loads(request.body)
		
		# Initialize Chapa payment service
		chapa_service = ChapaPaymentService()
		
		# Handle webhook
		result = chapa_service.handle_webhook(webhook_data)
		
		if result['status'] == 'success':
			# Get payment and send appropriate email
			tx_ref = webhook_data.get('tx_ref')
			payment = Payment.objects.get(payment_reference=tx_ref)
			
			if payment.status == Payment.STATUS_COMPLETED:
				send_payment_confirmation_email.delay(
					payment.booking.id, 
					payment.id
				)
			elif payment.status == Payment.STATUS_FAILED:
				send_payment_failed_email.delay(
					payment.booking.id, 
					payment.id
				)
			
			return JsonResponse({'message': 'Webhook processed successfully'})
		else:
			logger.error(f"Webhook processing failed: {result}")
			return JsonResponse(
				{'error': 'Webhook processing failed'}, 
				status=400
			)
			
	except json.JSONDecodeError:
		return JsonResponse({'error': 'Invalid JSON'}, status=400)
	except Exception as e:
		logger.error(f"Error processing webhook: {str(e)}")
		return JsonResponse({'error': 'Internal server error'}, status=500)

