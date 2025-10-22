import razorpay
import os
from typing import Dict, Any
from datetime import datetime
import hashlib
import hmac

class PaymentService:
    def __init__(self):
        self.client = razorpay.Client(
            auth=(os.getenv("RAZORPAY_KEY_ID", "rzp_test_RWZv6Fqh8F4Pdy"), 
                  os.getenv("RAZORPAY_KEY_SECRET", "IJPqUvqe1WNpXjTeH6zwijAB"))
        )
    
    def create_order(self, amount: int, currency: str = "INR", receipt: str = None) -> Dict[str, Any]:
        """
        Create a Razorpay order
        """
        try:
            order_data = {
                "amount": amount * 100,  # Convert to paise
                "currency": currency,
                "receipt": receipt or f"receipt_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "notes": {
                    "plan": "premium_monthly",
                    "created_at": datetime.now().isoformat()
                }
            }
            
            order = self.client.order.create(data=order_data)
            return {
                "success": True,
                "order_id": order["id"],
                "amount": order["amount"],
                "currency": order["currency"],
                "receipt": order["receipt"]
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def verify_payment(self, razorpay_order_id: str, razorpay_payment_id: str, razorpay_signature: str) -> Dict[str, Any]:
        """
        Verify Razorpay payment signature
        """
        try:
            # Create the signature string
            signature_string = f"{razorpay_order_id}|{razorpay_payment_id}"
            
            # Generate expected signature
            expected_signature = hmac.new(
                self.client.auth[1].encode('utf-8'),
                signature_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Verify signature
            if hmac.compare_digest(expected_signature, razorpay_signature):
                return {
                    "success": True,
                    "verified": True,
                    "payment_id": razorpay_payment_id,
                    "order_id": razorpay_order_id
                }
            else:
                return {
                    "success": False,
                    "verified": False,
                    "error": "Invalid signature"
                }
        except Exception as e:
            return {
                "success": False,
                "verified": False,
                "error": str(e)
            }
    
    def get_payment_details(self, payment_id: str) -> Dict[str, Any]:
        """
        Get payment details from Razorpay
        """
        try:
            payment = self.client.payment.fetch(payment_id)
            return {
                "success": True,
                "payment": payment
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

# Initialize payment service
payment_service = PaymentService()
