#!/usr/bin/env python
"""
Chapa Payment Integration Test Script with Real API Credentials

This script tests the Chapa payment integration using the provided test credentials:
- Test Public Key: CHAPUBK_TEST-u93vw9MHQYaPhtA4Fa89JQi5qsCxoyBt
- Test Secret Key: CHASECK_TEST-TkpRkSUsdv9x3o2A5PRx6hlWE62bvRoI
- Encryption Key: kimUiM6latpe3r1QhR7LEzht

Before running:
1. Ensure Django server is running: python manage.py runserver
2. Make sure .env file has the correct test credentials
3. Have a valid booking in your database

Usage:
    python test_chapa_integration.py
"""

import os
import sys
import django
import requests
import json
from decimal import Decimal
import uuid
from datetime import datetime, timedelta

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alx_travel_app.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.conf import settings
from listings.models import Listing, Booking, Payment

User = get_user_model()


class ChapaTestRunner:
    def __init__(self):
        self.base_url = "http://localhost:8000"  # Django server URL
        self.chapa_base_url = settings.CHAPA_BASE_URL
        self.secret_key = settings.CHAPA_SECRET_KEY
        self.public_key = settings.CHAPA_PUBLIC_KEY
        self.webhook_hash = settings.CHAPA_WEBHOOK_HASH
        
        print(f"🔑 Using Chapa Test Credentials:")
        print(f"   Public Key: {self.public_key[:20]}...")
        print(f"   Secret Key: {self.secret_key[:20]}...")
        print(f"   Webhook Hash: {self.webhook_hash}")
        print(f"   Base URL: {self.chapa_base_url}")
        
    def create_test_data(self):
        """Create test user, listing, and booking"""
        print("\n📦 Creating test data...")
        
        # Create test user
        user, created = User.objects.get_or_create(
            username='chapa_test_user',
            defaults={
                'email': 'test@chapatest.com',
                'first_name': 'Chapa',
                'last_name': 'Tester'
            }
        )
        print(f"   ✓ Test user: {user.username}")
        
        # Create test listing
        listing, created = Listing.objects.get_or_create(
            title='Chapa Payment Test Resort',
            defaults={
                'description': 'Test resort for Chapa payment integration',
                'location': 'Addis Ababa, Ethiopia',
                'price_per_night': Decimal('1500.00'),
                'max_guests': 2,
                'is_available': True,
                'host': user
            }
        )
        print(f"   ✓ Test listing: {listing.title}")
        
        # Create test booking
        check_in = datetime.now().date() + timedelta(days=3)
        check_out = check_in + timedelta(days=2)
        total_price = listing.price_per_night * 2
        
        booking = Booking.objects.create(
            listing=listing,
            user=user,
            check_in=check_in,
            check_out=check_out,
            guests=2,
            total_price=total_price,
            status=Booking.STATUS_PENDING
        )
        print(f"   ✓ Test booking: ID {booking.id}, Amount: {booking.total_price} ETB")
        
        return user, listing, booking
    
    def test_chapa_api_direct(self, booking):
        """Test direct Chapa API call"""
        print("\n🔗 Testing direct Chapa API call...")
        
        headers = {
            'Authorization': f'Bearer {self.secret_key}',
            'Content-Type': 'application/json',
        }
        
        payment_data = {
            'amount': str(booking.total_price),
            'currency': 'ETB',
            'email': booking.user.email,
            'first_name': booking.user.first_name,
            'last_name': booking.user.last_name,
            'phone_number': '0911000000',  # Test phone number
            'tx_ref': f'test_{uuid.uuid4().hex[:12]}',
            'return_url': 'http://localhost:3000/payment/success',
            'description': f'Test payment for booking {booking.id}',
            'meta': {
                'booking_id': booking.id,
                'test_mode': True,
            },
        }
        
        try:
            response = requests.post(
                f'{self.chapa_base_url}/transaction/initialize',
                json=payment_data,
                headers=headers,
                timeout=30
            )
            
            print(f"   📤 Request sent to: {self.chapa_base_url}/transaction/initialize")
            print(f"   📋 Response status: {response.status_code}")
            
            response_data = response.json()
            print(f"   📄 Response data: {json.dumps(response_data, indent=2)}")
            
            if response.status_code == 200 and response_data.get('status') == 'success':
                print("   ✅ Direct Chapa API call successful!")
                checkout_url = response_data['data']['checkout_url']
                print(f"   🔗 Checkout URL: {checkout_url}")
                return True, checkout_url
            else:
                print("   ❌ Direct Chapa API call failed!")
                return False, None
                
        except Exception as e:
            print(f"   ❌ Error during direct API call: {str(e)}")
            return False, None
    
    def test_django_payment_initiation(self, booking):
        """Test payment initiation through Django API"""
        print("\n🐍 Testing Django payment initiation API...")
        
        # First, we need to authenticate (simplified for testing)
        payment_data = {
            'booking_id': booking.id,
            'return_url': 'http://localhost:3000/payment/success',
            'callback_url': 'http://localhost:8000/api/chapa/webhook/'
        }
        
        try:
            # Note: In a real scenario, you'd need proper authentication
            response = requests.post(
                f'{self.base_url}/api/payments/initiate/',
                json=payment_data,
                timeout=30
            )
            
            print(f"   📤 Request sent to: {self.base_url}/api/payments/initiate/")
            print(f"   📋 Response status: {response.status_code}")
            
            if response.status_code in [200, 201]:
                response_data = response.json()
                print(f"   📄 Response data: {json.dumps(response_data, indent=2)}")
                print("   ✅ Django payment initiation successful!")
                return True, response_data.get('checkout_url'), response_data.get('payment_reference')
            else:
                print(f"   ❌ Django payment initiation failed: {response.text}")
                return False, None, None
                
        except Exception as e:
            print(f"   ❌ Error during Django API call: {str(e)}")
            return False, None, None
    
    def test_payment_verification(self, tx_ref):
        """Test payment verification"""
        print(f"\n🔍 Testing payment verification for tx_ref: {tx_ref}")
        
        headers = {
            'Authorization': f'Bearer {self.secret_key}',
            'Content-Type': 'application/json',
        }
        
        try:
            response = requests.get(
                f'{self.chapa_base_url}/transaction/verify/{tx_ref}',
                headers=headers,
                timeout=30
            )
            
            print(f"   📤 Request sent to: {self.chapa_base_url}/transaction/verify/{tx_ref}")
            print(f"   📋 Response status: {response.status_code}")
            
            response_data = response.json()
            print(f"   📄 Response data: {json.dumps(response_data, indent=2)}")
            
            if response.status_code == 200:
                print("   ✅ Payment verification successful!")
                return True, response_data
            else:
                print("   ❌ Payment verification failed!")
                return False, response_data
                
        except Exception as e:
            print(f"   ❌ Error during verification: {str(e)}")
            return False, None
    
    def test_webhook_simulation(self, tx_ref):
        """Simulate webhook call"""
        print(f"\n📡 Simulating webhook for tx_ref: {tx_ref}")
        
        webhook_data = {
            "tx_ref": tx_ref,
            "status": "success",
            "currency": "ETB",
            "amount": "3000.00",
            "charge": "90.00",
            "mode": "test",
            "method": "telebirr",
            "type": "transaction.success",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        try:
            response = requests.post(
                f'{self.base_url}/api/chapa/webhook/',
                json=webhook_data,
                timeout=30
            )
            
            print(f"   📤 Webhook sent to: {self.base_url}/api/chapa/webhook/")
            print(f"   📋 Response status: {response.status_code}")
            print(f"   📄 Response: {response.text}")
            
            if response.status_code == 200:
                print("   ✅ Webhook simulation successful!")
                return True
            else:
                print("   ❌ Webhook simulation failed!")
                return False
                
        except Exception as e:
            print(f"   ❌ Error during webhook simulation: {str(e)}")
            return False
    
    def display_test_summary(self, results):
        """Display test results summary"""
        print("\n" + "="*60)
        print("🧪 CHAPA INTEGRATION TEST RESULTS")
        print("="*60)
        
        total_tests = len(results)
        passed_tests = sum(1 for result in results.values() if result)
        
        print(f"\n📊 Overall Results: {passed_tests}/{total_tests} tests passed")
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {status} {test_name}")
        
        if passed_tests == total_tests:
            print("\n🎉 All tests passed! Chapa integration is working correctly.")
        else:
            print(f"\n⚠️  {total_tests - passed_tests} test(s) failed. Please check the configuration.")
        
        print("\n💡 Next Steps:")
        if results.get('direct_api', False):
            print("   • Direct Chapa API is working - credentials are valid")
        if results.get('django_api', False):
            print("   • Django payment API is working - integration is successful")
        if results.get('webhook', False):
            print("   • Webhook handling is working - real-time updates enabled")
        
        print("\n🔗 For manual testing, use the checkout URLs provided above")
        print("   to complete actual payments in Chapa's test environment.")
    
    def run_tests(self):
        """Run all integration tests"""
        print("🚀 Starting Chapa Payment Integration Tests")
        print("="*60)
        
        # Validate configuration
        if not all([self.secret_key, self.public_key, self.webhook_hash]):
            print("❌ Missing Chapa credentials in environment variables!")
            return
        
        # Create test data
        user, listing, booking = self.create_test_data()
        
        # Initialize results
        results = {}
        
        # Test 1: Direct Chapa API
        success, checkout_url = self.test_chapa_api_direct(booking)
        results['direct_api'] = success
        
        # Test 2: Django payment initiation
        success, django_checkout_url, payment_ref = self.test_django_payment_initiation(booking)
        results['django_api'] = success
        
        # Test 3: Payment verification (using a test tx_ref)
        test_tx_ref = f'test_{uuid.uuid4().hex[:12]}'
        success, verification_data = self.test_payment_verification(test_tx_ref)
        results['verification'] = success
        
        # Test 4: Webhook simulation
        success = self.test_webhook_simulation(payment_ref or test_tx_ref)
        results['webhook'] = success
        
        # Display summary
        self.display_test_summary(results)
        
        # Display checkout URLs for manual testing
        if checkout_url or django_checkout_url:
            print("\n🛒 MANUAL TESTING:")
            if checkout_url:
                print(f"   Direct API Checkout: {checkout_url}")
            if django_checkout_url:
                print(f"   Django API Checkout: {django_checkout_url}")
            print("   Visit these URLs to complete test payments manually.")


if __name__ == "__main__":
    tester = ChapaTestRunner()
    tester.run_tests()