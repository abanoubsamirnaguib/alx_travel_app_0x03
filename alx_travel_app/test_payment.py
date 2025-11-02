"""
Test script for Chapa payment integration
This script demonstrates how to test the payment workflow
"""

import requests
import json
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:8000/api"
TEST_USER_CREDENTIALS = {
    "username": "testuser",
    "password": "testpassword123"
}

def get_auth_token():
    """Get authentication token for API requests"""
    # This assumes you have token authentication set up
    # Adjust based on your authentication method
    login_url = f"{BASE_URL}/auth/login/"
    response = requests.post(login_url, data=TEST_USER_CREDENTIALS)
    if response.status_code == 200:
        return response.json().get('token')
    else:
        print("Failed to authenticate")
        return None

def create_test_listing():
    """Create a test listing"""
    token = get_auth_token()
    if not token:
        return None
    
    headers = {"Authorization": f"Bearer {token}"}
    listing_data = {
        "title": "Test Beach House",
        "description": "Beautiful beach house for testing",
        "location": "Addis Ababa, Ethiopia",
        "price_per_night": "1500.00",
        "max_guests": 4,
        "is_available": True,
        "image_url": "https://example.com/beach-house.jpg"
    }
    
    response = requests.post(f"{BASE_URL}/listings/", json=listing_data, headers=headers)
    if response.status_code == 201:
        return response.json()
    else:
        print("Failed to create listing:", response.text)
        return None

def create_test_booking(listing_id):
    """Create a test booking"""
    token = get_auth_token()
    if not token:
        return None
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Calculate dates
    check_in = datetime.now().date() + timedelta(days=7)
    check_out = check_in + timedelta(days=3)
    
    booking_data = {
        "listing": listing_id,
        "check_in": check_in.isoformat(),
        "check_out": check_out.isoformat(),
        "guests": 2,
        "total_price": "4500.00"  # 3 nights * 1500
    }
    
    response = requests.post(f"{BASE_URL}/bookings/", json=booking_data, headers=headers)
    if response.status_code == 201:
        return response.json()
    else:
        print("Failed to create booking:", response.text)
        return None

def initiate_payment(booking_id):
    """Initiate payment for a booking"""
    token = get_auth_token()
    if not token:
        return None
    
    headers = {"Authorization": f"Bearer {token}"}
    payment_data = {
        "booking_id": booking_id,
        "return_url": "http://localhost:3000/payment/success",
        "callback_url": "http://localhost:8000/api/chapa/webhook/"
    }
    
    response = requests.post(f"{BASE_URL}/payments/initiate/", json=payment_data, headers=headers)
    if response.status_code == 201:
        return response.json()
    else:
        print("Failed to initiate payment:", response.text)
        return None

def verify_payment(tx_ref):
    """Verify payment status"""
    token = get_auth_token()
    if not token:
        return None
    
    headers = {"Authorization": f"Bearer {token}"}
    verification_data = {"tx_ref": tx_ref}
    
    response = requests.post(f"{BASE_URL}/payments/verify/", json=verification_data, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print("Failed to verify payment:", response.text)
        return None

def run_payment_test():
    """Run complete payment test workflow"""
    print("=== Chapa Payment Integration Test ===\n")
    
    # Step 1: Create a test listing
    print("1. Creating test listing...")
    listing = create_test_listing()
    if not listing:
        return
    print(f"   Created listing: {listing['title']} (ID: {listing['id']})\n")
    
    # Step 2: Create a test booking
    print("2. Creating test booking...")
    booking = create_test_booking(listing['id'])
    if not booking:
        return
    print(f"   Created booking: ID {booking['id']}, Total: {booking['total_price']}\n")
    
    # Step 3: Initiate payment
    print("3. Initiating payment...")
    payment_result = initiate_payment(booking['id'])
    if not payment_result:
        return
    
    print(f"   Payment initiated successfully!")
    print(f"   Payment Reference: {payment_result['payment_reference']}")
    print(f"   Checkout URL: {payment_result['checkout_url']}")
    print("\n   --> Please visit the checkout URL to complete the payment in Chapa's sandbox environment\n")
    
    # Step 4: Wait for user to complete payment and then verify
    input("Press Enter after completing the payment to verify...")
    
    print("4. Verifying payment...")
    verification_result = verify_payment(payment_result['payment_reference'])
    if verification_result:
        print(f"   Payment Status: {verification_result['payment_status']}")
        print(f"   Booking Status: {verification_result['booking_status']}")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    run_payment_test()