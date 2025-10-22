# Razorpay Integration for Plan My Trip

This document describes the Razorpay payment integration implemented for the Plan My Trip application.

## Overview

The integration allows users to purchase a premium subscription ($9.99/month) using Razorpay's payment gateway. The implementation includes both backend API endpoints and frontend payment components.

## Backend Implementation

### Dependencies Added
- `razorpay>=1.3.0` - Razorpay Python SDK

### Files Created/Modified
- `backend/payment_service.py` - Payment service with Razorpay integration
- `backend/api.py` - Added payment endpoints

### API Endpoints

#### 1. Create Payment Order
```
POST /payment/create-order
```
**Request Body:**
```json
{
  "amount": 999,
  "currency": "INR",
  "receipt": "optional_receipt_id"
}
```

**Response:**
```json
{
  "success": true,
  "order_id": "order_xyz",
  "amount": 99900,
  "currency": "INR",
  "receipt": "receipt_xyz"
}
```

#### 2. Verify Payment
```
POST /payment/verify
```
**Request Body:**
```json
{
  "razorpay_order_id": "order_xyz",
  "razorpay_payment_id": "pay_xyz",
  "razorpay_signature": "signature_xyz"
}
```

#### 3. Get Payment Details
```
GET /payment/details/{payment_id}
```

### Configuration

The Razorpay credentials are configured in `payment_service.py`:
- Key ID: `rzp_test_RWZv6Fqh8F4Pdy`
- Key Secret: `IJPqUvqe1WNpXjTeH6zwijAB`

**Note:** These are test credentials. For production, use environment variables:
```python
RAZORPAY_KEY_ID=your_production_key_id
RAZORPAY_KEY_SECRET=your_production_key_secret
```

## Frontend Implementation

### Dependencies Added
- `razorpay: ^2.2.0` - Razorpay JavaScript SDK

### Files Created/Modified
- `frontend/src/paymentService.ts` - Payment service for frontend
- `frontend/src/PaymentModal.tsx` - Payment modal component
- `frontend/src/SubscriptionContext.tsx` - Subscription state management
- `frontend/src/HomePage.tsx` - Updated with payment integration
- `frontend/src/App.tsx` - Added SubscriptionProvider

### Components

#### PaymentModal
A modal component that displays:
- Plan details and pricing
- Payment button with Razorpay integration
- Loading states during payment processing
- Success/error handling

#### SubscriptionContext
Manages subscription state across the application:
- Tracks subscription status
- Persists subscription data in localStorage
- Listens for payment completion events

#### PaymentService
Handles all payment-related operations:
- Creates Razorpay orders
- Initiates payment process
- Verifies payment signatures
- Manages payment success/failure

## Payment Flow

1. User clicks "Upgrade to Premium" button
2. PaymentModal opens with plan details
3. User clicks "Pay $9.99/month" button
4. Razorpay checkout opens
5. User completes payment
6. Payment is verified on backend
7. Subscription status is updated
8. User gains access to premium features

## Security Features

- Payment signature verification using HMAC-SHA256
- Secure order creation on backend
- No sensitive data stored in frontend
- Test mode enabled for development

## Testing

### Test Cards (Razorpay Test Mode)
- **Success:** 4111 1111 1111 1111
- **Failure:** 4000 0000 0000 0002
- **CVV:** Any 3 digits
- **Expiry:** Any future date

### Test UPI IDs
- success@razorpay
- failure@razorpay

## Environment Variables

Create a `.env` file in the frontend directory:
```env
VITE_API_URL=http://localhost:8000
VITE_RAZORPAY_KEY_ID=rzp_test_RWZv6Fqh8F4Pdy
```

## Production Deployment

1. Replace test credentials with production credentials
2. Update API URLs to production endpoints
3. Enable webhook handling for payment events
4. Implement proper error logging and monitoring
5. Add subscription management features (cancel, upgrade, etc.)

## Features Implemented

✅ Payment order creation
✅ Payment verification
✅ Frontend payment modal
✅ Subscription state management
✅ Payment success handling
✅ Error handling and user feedback
✅ Responsive design
✅ Test mode configuration

## Future Enhancements

- Webhook handling for payment events
- Subscription management (cancel, upgrade, downgrade)
- Multiple payment plans
- Invoice generation
- Payment history
- Refund handling
- Analytics and reporting
