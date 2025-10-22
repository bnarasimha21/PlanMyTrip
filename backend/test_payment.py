#!/usr/bin/env python3
"""
Test script for Razorpay payment integration
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from payment_service import payment_service

def test_create_order():
    """Test order creation"""
    print("Testing order creation...")
    
    result = payment_service.create_order(
        amount=999,  # $9.99 in cents
        currency="INR",
        receipt="test_receipt_001"
    )
    
    print(f"Order creation result: {result}")
    
    if result["success"]:
        print("✅ Order creation successful")
        return result["order_id"]
    else:
        print(f"❌ Order creation failed: {result['error']}")
        return None

def test_payment_verification():
    """Test payment verification (mock)"""
    print("\nTesting payment verification...")
    
    # This would normally be called with real payment data
    # For testing, we'll just verify the method exists and handles errors
    result = payment_service.verify_payment(
        razorpay_order_id="test_order",
        razorpay_payment_id="test_payment",
        razorpay_signature="test_signature"
    )
    
    print(f"Payment verification result: {result}")
    
    if not result["success"]:
        print("✅ Payment verification correctly rejected invalid signature")
    else:
        print("❌ Payment verification should have failed with test data")

def main():
    """Run all tests"""
    print("🧪 Testing Razorpay Payment Service")
    print("=" * 40)
    
    # Test order creation
    order_id = test_create_order()
    
    # Test payment verification
    test_payment_verification()
    
    print("\n" + "=" * 40)
    print("✅ All tests completed")
    
    if order_id:
        print(f"📝 Test order ID: {order_id}")
        print("💡 You can use this order ID for frontend testing")

if __name__ == "__main__":
    main()
