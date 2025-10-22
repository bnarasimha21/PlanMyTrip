// Payment service for Razorpay integration
const RAZORPAY_KEY_ID = 'rzp_test_RWZv6Fqh8F4Pdy';
const API_BASE_URL = 'http://localhost:8000';

export interface CreateOrderRequest {
  amount: number;
  currency?: string;
  receipt?: string;
}

export interface CreateOrderResponse {
  success: boolean;
  order_id?: string;
  amount?: number;
  currency?: string;
  receipt?: string;
  error?: string;
}

export interface VerifyPaymentRequest {
  razorpay_order_id: string;
  razorpay_payment_id: string;
  razorpay_signature: string;
}

export interface VerifyPaymentResponse {
  success: boolean;
  verified?: boolean;
  payment_id?: string;
  order_id?: string;
  error?: string;
}

class PaymentService {
  private loadRazorpayScript(): Promise<boolean> {
    return new Promise((resolve) => {
      // Check if Razorpay is already loaded
      if (typeof (window as any).Razorpay !== 'undefined') {
        console.log('Razorpay already loaded');
        resolve(true);
        return;
      }

      // Check if script is already being loaded
      const existingScript = document.querySelector('script[src="https://checkout.razorpay.com/v1/checkout.js"]');
      if (existingScript) {
        console.log('Razorpay script already exists, waiting for load...');
        existingScript.addEventListener('load', () => resolve(true));
        existingScript.addEventListener('error', () => resolve(false));
        return;
      }

      console.log('Loading Razorpay script...');
      const script = document.createElement('script');
      script.src = 'https://checkout.razorpay.com/v1/checkout.js';
      script.onload = () => {
        console.log('Razorpay script loaded successfully');
        resolve(true);
      };
      script.onerror = (error) => {
        console.error('Failed to load Razorpay script:', error);
        resolve(false);
      };
      document.body.appendChild(script);
    });
  }

  async createOrder(orderData: CreateOrderRequest): Promise<CreateOrderResponse> {
    try {
      console.log('Creating order with data:', orderData);
      console.log('API URL:', `${API_BASE_URL}/payment/create-order`);
      
      const response = await fetch(`${API_BASE_URL}/payment/create-order`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(orderData),
      });

      console.log('Order creation response status:', response.status);
      const result = await response.json();
      console.log('Order creation result:', result);
      return result;
    } catch (error) {
      console.error('Order creation error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred',
      };
    }
  }

  async verifyPayment(verificationData: VerifyPaymentRequest): Promise<VerifyPaymentResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/payment/verify`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(verificationData),
      });

      const result = await response.json();
      return result;
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred',
      };
    }
  }

  async initiatePayment(amount: number, currency: string = 'INR'): Promise<boolean> {
    try {
      console.log('Initiating payment for amount:', amount, 'currency:', currency);
      
      // Load Razorpay script
      const scriptLoaded = await this.loadRazorpayScript();
      console.log('Razorpay script loaded:', scriptLoaded);
      if (!scriptLoaded) {
        throw new Error('Failed to load Razorpay script');
      }

      // Check if Razorpay is available
      if (typeof (window as any).Razorpay === 'undefined') {
        throw new Error('Razorpay not available on window object');
      }
      console.log('Razorpay object available:', typeof (window as any).Razorpay);

      // Create order
      console.log('Creating order...');
      const amountInCents = Math.round(amount * 100);
      console.log(`Converting ${amount} to ${amountInCents} cents`);
      const orderResult = await this.createOrder({
        amount: amountInCents, // Convert to cents
        currency: 'INR', // Force INR for Indian payment methods
        receipt: `receipt_${Date.now()}`,
      });
      console.log('Order creation result:', orderResult);

      if (!orderResult.success || !orderResult.order_id) {
        throw new Error(orderResult.error || 'Failed to create order');
      }

      // Initialize Razorpay
      const options = {
        key: RAZORPAY_KEY_ID,
        amount: orderResult.amount,
        currency: 'INR', // Force INR for Indian payment methods
        name: 'Plan My Trip',
        description: 'Premium Subscription',
        order_id: orderResult.order_id,
        // Note: UPI may not be available in test mode
        // For production, UPI will be automatically available for INR transactions
        method: {
          netbanking: true,
          wallet: true,
          upi: true,
          card: true,
          emi: true,
          paylater: true
        },
        handler: async (response: any) => {
          try {
            // Verify payment
            const verificationResult = await this.verifyPayment({
              razorpay_order_id: response.razorpay_order_id,
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_signature: response.razorpay_signature,
            });

            if (verificationResult.success && verificationResult.verified) {
              // Payment successful
              console.log('Payment successful:', verificationResult);
              // Set subscription in localStorage
              localStorage.setItem('subscription_plan', 'premium');
              // Trigger a custom event to notify other components
              window.dispatchEvent(new CustomEvent('subscriptionUpdated', { 
                detail: { plan: 'premium', isSubscribed: true } 
              }));
              // Trigger payment success event to close modal
              window.dispatchEvent(new CustomEvent('paymentSuccess'));
              alert('Payment successful! Welcome to Premium!');
            } else {
              console.error('Payment verification failed:', verificationResult.error);
              alert('Payment verification failed. Please try again.');
            }
          } catch (error) {
            console.error('Payment verification error:', error);
            alert('Payment verification failed. Please contact support.');
          }
        },
        prefill: {
          name: 'User Name', // You can get this from user context
          email: 'user@example.com', // You can get this from user context
          contact: '9999999999', // Indian mobile number format
        },
        notes: {
          plan: 'premium_monthly',
          source: 'web_app'
        },
        theme: {
          color: '#8B5CF6', // Purple theme to match your app
        },
        modal: {
          ondismiss: () => {
            console.log('Payment modal dismissed');
          },
        },
        // Additional options for Indian payments
        retry: {
          enabled: true,
          max_count: 3
        },
        timeout: 900, // 15 minutes timeout
        remember_customer: true,
      };

      console.log('Razorpay options:', JSON.stringify(options, null, 2));
      console.log('⚠️ Note: UPI may not be available in test mode. In production, UPI will be automatically available for INR transactions.');
      console.log('Creating Razorpay instance...');
      
      const razorpay = new (window as any).Razorpay(options);
      console.log('Razorpay instance created:', razorpay);
      
      console.log('Opening Razorpay checkout...');
      razorpay.open();

      return true;
    } catch (error) {
      console.error('Payment initiation error:', error);
      console.error('Error details:', {
        message: error instanceof Error ? error.message : 'Unknown error',
        stack: error instanceof Error ? error.stack : undefined
      });
      alert(`Failed to initiate payment: ${error instanceof Error ? error.message : 'Unknown error'}. Please try again.`);
      return false;
    }
  }
}

export const paymentService = new PaymentService();
