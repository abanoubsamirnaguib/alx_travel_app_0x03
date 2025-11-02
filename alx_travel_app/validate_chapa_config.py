#!/usr/bin/env python
"""
Chapa Configuration Validator

This script validates that your Chapa test credentials are properly configured
and can communicate with the Chapa API.

Test Credentials:
- Public Key: CHAPUBK_TEST-u93vw9MHQYaPhtA4Fa89JQi5qsCxoyBt
- Secret Key: CHASECK_TEST-TkpRkSUsdv9x3o2A5PRx6hlWE62bvRoI
- Encryption Key: kimUiM6latpe3r1QhR7LEzht

Usage:
    python validate_chapa_config.py
"""

import os
import sys
import django
import requests

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alx_travel_app.settings')
django.setup()

from django.conf import settings


def validate_environment_variables():
    """Validate that all required environment variables are set"""
    print("🔍 Validating Environment Variables...")
    
    required_vars = {
        'CHAPA_PUBLIC_KEY': settings.CHAPA_PUBLIC_KEY,
        'CHAPA_SECRET_KEY': settings.CHAPA_SECRET_KEY,
        'CHAPA_WEBHOOK_HASH': settings.CHAPA_WEBHOOK_HASH,
        'CHAPA_BASE_URL': settings.CHAPA_BASE_URL,
    }
    
    all_valid = True
    
    for var_name, var_value in required_vars.items():
        if var_value and var_value != '':
            print(f"   ✅ {var_name}: {var_value[:20]}...")
        else:
            print(f"   ❌ {var_name}: Not set or empty")
            all_valid = False
    
    return all_valid


def validate_chapa_api_connection():
    """Test connection to Chapa API"""
    print("\n🔗 Testing Chapa API Connection...")
    
    # Test with a simple request to check API connectivity
    headers = {
        'Authorization': f'Bearer {settings.CHAPA_SECRET_KEY}',
        'Content-Type': 'application/json',
    }
    
    # Test payload for initialization (this will likely fail but should give us connection info)
    test_payload = {
        'amount': '100',
        'currency': 'ETB',
        'email': 'test@example.com',
        'first_name': 'Test',
        'last_name': 'User',
        'phone_number': '0911000000',
        'tx_ref': 'test_connection_check',
        'return_url': 'http://localhost:3000/success',
        'description': 'Connection test',
    }
    
    try:
        response = requests.post(
            f'{settings.CHAPA_BASE_URL}/transaction/initialize',
            json=test_payload,
            headers=headers,
            timeout=10
        )
        
        print(f"   📤 Request sent to: {settings.CHAPA_BASE_URL}/transaction/initialize")
        print(f"   📊 Status Code: {response.status_code}")
        
        try:
            response_data = response.json()
            print(f"   📄 Response: {response_data.get('message', 'No message')}")
            
            # Even if the request fails due to invalid data, a 400 with proper JSON response
            # indicates that the API is reachable and credentials are being processed
            if response.status_code in [200, 400] and isinstance(response_data, dict):
                print("   ✅ API Connection: Success (Chapa API is reachable)")
                return True
            else:
                print(f"   ❌ API Connection: Failed (Unexpected response)")
                return False
                
        except ValueError:
            print(f"   ❌ API Connection: Failed (Invalid JSON response)")
            return False
            
    except requests.exceptions.Timeout:
        print("   ❌ API Connection: Timeout (Check internet connection)")
        return False
    except requests.exceptions.ConnectionError:
        print("   ❌ API Connection: Connection Error (Check internet/firewall)")
        return False
    except Exception as e:
        print(f"   ❌ API Connection: Error ({str(e)})")
        return False


def validate_django_settings():
    """Validate Django configuration"""
    print("\n⚙️  Validating Django Configuration...")
    
    checks = {
        'DEBUG': settings.DEBUG,
        'SECRET_KEY': bool(settings.SECRET_KEY),
        'INSTALLED_APPS has listings': 'listings' in settings.INSTALLED_APPS,
        'REST_FRAMEWORK configured': hasattr(settings, 'REST_FRAMEWORK'),
    }
    
    all_valid = True
    
    for check_name, check_result in checks.items():
        if check_result:
            print(f"   ✅ {check_name}")
        else:
            print(f"   ❌ {check_name}")
            all_valid = False
    
    return all_valid


def check_database_models():
    """Check if Payment model is available"""
    print("\n💾 Checking Database Models...")
    
    try:
        from listings.models import Payment, Booking, Listing
        print("   ✅ Payment model imported successfully")
        print("   ✅ Booking model imported successfully")
        print("   ✅ Listing model imported successfully")
        
        # Check if tables exist by attempting to count records
        try:
            payment_count = Payment.objects.count()
            booking_count = Booking.objects.count()
            listing_count = Listing.objects.count()
            
            print(f"   ✅ Database tables accessible:")
            print(f"      - Payments: {payment_count} records")
            print(f"      - Bookings: {booking_count} records")
            print(f"      - Listings: {listing_count} records")
            
            return True
        except Exception as e:
            print(f"   ⚠️  Database tables exist but error accessing: {str(e)}")
            print("   💡 Try running: python manage.py migrate")
            return False
            
    except ImportError as e:
        print(f"   ❌ Model import error: {str(e)}")
        return False


def main():
    """Run all validation checks"""
    print("🔧 Chapa Payment Integration Configuration Validator")
    print("=" * 60)
    
    print(f"\n📋 Expected Test Credentials:")
    print(f"   Public Key: CHAPUBK_TEST-u93vw9MHQYaPhtA4Fa89JQi5qsCxoyBt")
    print(f"   Secret Key: CHASECK_TEST-TkpRkSUsdv9x3o2A5PRx6hlWE62bvRoI")
    print(f"   Webhook Hash: kimUiM6latpe3r1QhR7LEzht")
    
    # Run validation checks
    env_valid = validate_environment_variables()
    django_valid = validate_django_settings()
    db_valid = check_database_models()
    api_valid = validate_chapa_api_connection() if env_valid else False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)
    
    checks = {
        "Environment Variables": env_valid,
        "Django Configuration": django_valid,
        "Database Models": db_valid,
        "Chapa API Connection": api_valid,
    }
    
    passed = sum(1 for result in checks.values() if result)
    total = len(checks)
    
    for check_name, result in checks.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {check_name}")
    
    print(f"\n📈 Overall: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 Configuration is valid! You can proceed with payment integration testing.")
        print("\n🚀 Next steps:")
        print("   1. Run: python test_chapa_integration.py")
        print("   2. Run: python payment_demo.py")
        print("   3. Test manual payments using the checkout URLs")
    else:
        print("\n⚠️  Configuration issues detected. Please fix the failing checks above.")
        
        if not env_valid:
            print("\n🔧 To fix environment variables:")
            print("   1. Check your .env file in the project root")
            print("   2. Ensure all Chapa credentials are properly set")
        
        if not db_valid:
            print("\n🔧 To fix database issues:")
            print("   1. Run: python manage.py makemigrations")
            print("   2. Run: python manage.py migrate")
        
        if not api_valid and env_valid:
            print("\n🔧 To fix API connection:")
            print("   1. Check your internet connection")
            print("   2. Verify Chapa API credentials are correct")
            print("   3. Check if firewall is blocking requests")


if __name__ == "__main__":
    main()