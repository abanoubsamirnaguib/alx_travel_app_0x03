#!/usr/bin/env python
"""
Chapa Payment Integration Demo for ALX Travel App

This script demonstrates the complete payment workflow using actual Chapa test credentials:
- Test Public Key: CHAPUBK_TEST-u93vw9MHQYaPhtA4Fa89JQi5qsCxoyBt
- Test Secret Key: CHASECK_TEST-TkpRkSUsdv9x3o2A5PRx6hlWE62bvRoI
- Encryption Key: kimUiM6latpe3r1QhR7LEzht

The demo includes:
1. Payment initiation
2. Payment verification  
3. Webhook handling simulation
4. Email notification testing

Before running this script:
1. Ensure .env file has the correct test credentials
2. Ensure Django server is running
3. Have a valid booking in your database

Usage:
    python payment_demo.py
"""

import os
import sys
import django
from decimal import Decimal
import uuid
from datetime import datetime, timedelta

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alx_travel_app.settings')
django.setup()

from django.contrib.auth import get_user_model
from listings.models import Listing, Booking, Payment
from listings.services import ChapaPaymentService
from listings.tasks import send_payment_confirmation_email

User = get_user_model()


class PaymentDemo:
    def __init__(self):
        self.chapa_service = ChapaPaymentService()
        self.demo_data = {}
    
    def create_demo_user(self):
        """Create a demo user for testing"""
        try:
            user, created = User.objects.get_or_create(
                username='demo_user',
                defaults={
                    'email': 'demo@alxtravel.com',
                    'first_name': 'Demo',
                    'last_name': 'User'
                }
            )
            self.demo_data['user'] = user
            print(f"✓ Demo user {'created' if created else 'exists'}: {user.username}")
            return user
        except Exception as e:
            print(f"✗ Error creating demo user: {str(e)}")
            return None
    
    def create_demo_listing(self):
        """Create a demo listing for testing"""
        try:
            user = self.demo_data['user']
            listing, created = Listing.objects.get_or_create(
                title='Demo Beach Resort - Payment Test',
                defaults={
                    'description': 'Beautiful beachfront resort for payment integration testing',
                    'location': 'Bahir Dar, Ethiopia',
                    'price_per_night': Decimal('2500.00'),
                    'max_guests': 4,
                    'is_available': True,
                    'image_url': 'https://example.com/beach-resort.jpg',
                    'host': user
                }
            )
            self.demo_data['listing'] = listing
            print(f"✓ Demo listing {'created' if created else 'exists'}: {listing.title}")
            return listing
        except Exception as e:
            print(f"✗ Error creating demo listing: {str(e)}")
            return None
    
    def create_demo_booking(self):
        """Create a demo booking for payment testing"""
        try:
            user = self.demo_data['user']
            listing = self.demo_data['listing']
            
            # Calculate dates for next week
            check_in = datetime.now().date() + timedelta(days=7)
            check_out = check_in + timedelta(days=2)  # 2 nights
            total_price = listing.price_per_night * 2  # 2 nights
            
            booking = Booking.objects.create(
                listing=listing,
                user=user,
                check_in=check_in,
                check_out=check_out,
                guests=2,
                total_price=total_price,
                status=Booking.STATUS_PENDING
            )
            
            self.demo_data['booking'] = booking
            print(f"✓ Demo booking created: ID {booking.id}, Total: {booking.total_price} ETB")
            return booking
        except Exception as e:
            print(f"✗ Error creating demo booking: {str(e)}")
            return None
    
    def demo_payment_initiation(self):
        """Demonstrate payment initiation"""
        print("\n=== Payment Initiation Demo ===")
        
        booking = self.demo_data['booking']
        return_url = "http://localhost:3000/payment/success"
        callback_url = "http://localhost:8000/api/chapa/webhook/"
        
        try:
            result = self.chapa_service.initiate_payment(
                booking=booking,
                return_url=return_url,
                callback_url=callback_url
            )
            
            if result['status'] == 'success':
                print(f"✓ Payment initiated successfully!")
                print(f"  Payment Reference: {result['payment_reference']}")
                print(f"  Checkout URL: {result['checkout_url']}")
                print(f"  Amount: {booking.total_price} ETB")
                
                # Store for verification demo
                self.demo_data['payment_reference'] = result['payment_reference']
                self.demo_data['checkout_url'] = result['checkout_url']
                
                return True
            else:
                print(f"✗ Payment initiation failed: {result.get('message', 'Unknown error')}")
                return False
        except Exception as e:
            print(f"✗ Error during payment initiation: {str(e)}")
            return False
    
    def demo_payment_verification(self):
        """Demonstrate payment verification"""
        print("\n=== Payment Verification Demo ===")
        
        payment_reference = self.demo_data.get('payment_reference')
        if not payment_reference:
            print("✗ No payment reference available for verification")
            return False
        
        try:
            result = self.chapa_service.verify_payment(payment_reference)
            
            if result['status'] == 'success':
                print(f"✓ Payment verification completed!")
                print(f"  Payment Status: {result['payment_status']}")
                
                # Get the actual payment object
                payment = Payment.objects.get(payment_reference=payment_reference)
                print(f"  Transaction ID: {payment.transaction_id or 'Pending'}")
                print(f"  Chapa Reference: {payment.chapa_reference or 'Pending'}")
                print(f"  Booking Status: {payment.booking.status}")
                
                return True
            else:
                print(f"✗ Payment verification failed: {result.get('message', 'Unknown error')}")
                return False
        except Exception as e:
            print(f"✗ Error during payment verification: {str(e)}")
            return False
    
    def demo_webhook_handling(self):
        """Demonstrate webhook handling"""
        print("\n=== Webhook Handling Demo ===")
        
        payment_reference = self.demo_data.get('payment_reference')
        if not payment_reference:
            print("✗ No payment reference available for webhook demo")
            return False
        
        # Simulate webhook data from Chapa
        webhook_data = {
            "tx_ref": payment_reference,
            "status": "success",
            "currency": "ETB",
            "amount": str(self.demo_data['booking'].total_price),
            "charge": "75.00",
            "mode": "test",
            "method": "telebirr",
            "type": "transaction.success"
        }
        
        try:
            result = self.chapa_service.handle_webhook(webhook_data)
            
            if result['status'] == 'success':
                print(f"✓ Webhook processed successfully!")
                print(f"  Webhook Type: transaction.success")
                print(f"  Payment Method: telebirr")
                return True
            else:
                print(f"✗ Webhook processing failed: {result.get('message', 'Unknown error')}")
                return False
        except Exception as e:
            print(f"✗ Error processing webhook: {str(e)}")
            return False
    
    def demo_email_notification(self):
        """Demonstrate email notification"""
        print("\n=== Email Notification Demo ===")
        
        booking = self.demo_data.get('booking')
        if not booking:
            print("✗ No booking available for email demo")
            return False
        
        try:
            # Get the payment object
            payment = Payment.objects.get(booking=booking)
            
            # In a real scenario, this would be called by Celery
            # For demo purposes, we'll simulate the email sending
            print(f"✓ Email notification would be sent to: {booking.user.email}")
            print(f"  Subject: Booking Confirmation - {booking.listing.title}")
            print(f"  Payment Reference: {payment.payment_reference}")
            print(f"  Amount: {payment.amount} {payment.currency}")
            
            # Uncomment the line below to actually send the email
            # send_payment_confirmation_email.delay(booking.id, payment.id)
            
            return True
        except Exception as e:
            print(f"✗ Error with email notification: {str(e)}")
            return False
    
    def display_integration_summary(self):
        """Display summary of the integration"""
        print("\n" + "="*60)
        print("🎉 CHAPA PAYMENT INTEGRATION SUMMARY")
        print("="*60)
        
        print("\n📋 What was implemented:")
        print("  ✓ Payment model for tracking transactions")
        print("  ✓ Chapa API service for payment operations")
        print("  ✓ Payment initiation endpoint")
        print("  ✓ Payment verification endpoint")
        print("  ✓ Webhook handling for real-time updates")
        print("  ✓ Email notifications for payment status")
        print("  ✓ Celery integration for background tasks")
        print("  ✓ Django admin interface for payment management")
        
        print("\n🔗 API Endpoints:")
        print("  • POST /api/payments/initiate/ - Initiate payment")
        print("  • POST /api/payments/verify/ - Verify payment status")
        print("  • GET  /api/payments/ - List user payments")
        print("  • POST /api/chapa/webhook/ - Chapa webhook handler")
        
        print("\n🔑 Next Steps for Production:")
        print("  1. Set up Chapa production API keys")
        print("  2. Configure production email service")
        print("  3. Set up Celery with Redis/RabbitMQ")
        print("  4. Implement proper webhook signature verification")
        print("  5. Add comprehensive error handling and logging")
        print("  6. Set up monitoring and alerting")
        
        print("\n💡 Testing:")
        print("  • Use Chapa sandbox environment for testing")
        print("  • Test with different payment methods")
        print("  • Verify webhook delivery")
        print("  • Test email notifications")
        
        # Display demo data
        if self.demo_data.get('checkout_url'):
            print(f"\n🛒 Demo Checkout URL:")
            print(f"  {self.demo_data['checkout_url']}")
            print("  (Visit this URL to complete payment in Chapa sandbox)")
    
    def run_demo(self):
        """Run the complete payment integration demo"""
        print("🚀 Starting Chapa Payment Integration Demo")
        print("="*50)
        
        # Step 1: Create demo data
        print("\n📦 Setting up demo data...")
        if not self.create_demo_user():
            return
        
        if not self.create_demo_listing():
            return
        
        if not self.create_demo_booking():
            return
        
        # Step 2: Demo payment workflow
        print("\n💳 Demonstrating payment workflow...")
        
        if not self.demo_payment_initiation():
            return
        
        # For verification demo, we'll simulate a successful payment
        # In real scenario, user would complete payment first
        print("\n⏳ Simulating payment completion...")
        payment = Payment.objects.get(booking=self.demo_data['booking'])
        payment.status = Payment.STATUS_COMPLETED
        payment.transaction_id = f"ch_test_{uuid.uuid4().hex[:12]}"
        payment.chapa_reference = f"ref_{uuid.uuid4().hex[:8]}"
        payment.booking.status = Booking.STATUS_CONFIRMED
        payment.booking.save()
        payment.save()
        print("✓ Payment status updated to COMPLETED (simulated)")
        
        self.demo_payment_verification()
        self.demo_webhook_handling()
        self.demo_email_notification()
        
        # Step 3: Display summary
        self.display_integration_summary()
        
        print("\n🎊 Demo completed successfully!")


if __name__ == "__main__":
    demo = PaymentDemo()
    demo.run_demo()