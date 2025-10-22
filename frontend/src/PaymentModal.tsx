import React, { useState } from 'react';
import { paymentService } from './paymentService';
import { useSubscription } from './SubscriptionContext';

interface PaymentModalProps {
  isOpen: boolean;
  onClose: () => void;
  plan: {
    name: string;
    price: number;
    features: string[];
  };
}

const PaymentModal: React.FC<PaymentModalProps> = ({ isOpen, onClose, plan }) => {
  const [isProcessing, setIsProcessing] = useState(false);
  const { setSubscription } = useSubscription();

  // Listen for successful payment events
  React.useEffect(() => {
    const handlePaymentSuccess = () => {
      console.log('Payment successful, closing modal...');
      // Small delay to let user see the success message
      setTimeout(() => {
        onClose();
      }, 2000);
    };

    window.addEventListener('paymentSuccess', handlePaymentSuccess);
    return () => {
      window.removeEventListener('paymentSuccess', handlePaymentSuccess);
    };
  }, [onClose]);

  const handlePayment = async () => {
    setIsProcessing(true);
    try {
      await paymentService.initiatePayment(plan.price);
    } catch (error) {
      console.error('Payment error:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl p-8 max-w-md w-full max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-gray-900">Complete Your Purchase</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="mb-6">
          <div className="bg-gradient-to-r from-blue-500 to-sky-500 rounded-xl p-6 text-white">
            <h3 className="text-xl font-bold mb-2">{plan.name} Plan</h3>
            <div className="text-3xl font-bold mb-2">
              ${plan.price.toFixed(2)}
              <span className="text-lg font-normal opacity-80">/month</span>
            </div>
            <p className="text-blue-100">Billed monthly, cancel anytime</p>
          </div>
        </div>

        <div className="mb-6">
          <h4 className="font-semibold text-gray-900 mb-3">What's included:</h4>
          <ul className="space-y-2">
            {plan.features.map((feature, index) => (
              <li key={index} className="flex items-center gap-3">
                <span className="text-blue-500 text-lg">✓</span>
                <span className="text-gray-700">{feature}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="space-y-3">
          <button
            onClick={handlePayment}
            disabled={isProcessing}
            className="w-full bg-gradient-to-r from-blue-600 to-sky-600 hover:from-blue-700 hover:to-sky-700 disabled:from-gray-400 disabled:to-gray-500 text-white py-3 px-6 rounded-xl font-semibold transition-all duration-200 transform hover:scale-105 disabled:scale-100 disabled:cursor-not-allowed shadow-lg"
          >
            {isProcessing ? (
              <div className="flex items-center justify-center gap-2">
                <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
                Processing...
              </div>
            ) : (
              `Pay $${plan.price.toFixed(2)}/month`
            )}
          </button>
          
          <button
            onClick={onClose}
            className="w-full bg-gray-100 hover:bg-gray-200 text-gray-700 py-3 px-6 rounded-xl font-semibold transition-all duration-200"
          >
            Cancel
          </button>
        </div>

        <div className="mt-6 text-center">
          <p className="text-xs text-gray-500">
            Secure payment powered by Razorpay
          </p>
          <div className="flex justify-center items-center gap-2 mt-2">
            <div className="w-6 h-4 bg-blue-600 rounded text-white text-xs flex items-center justify-center font-bold">
              R
            </div>
            <span className="text-xs text-gray-500">Razorpay</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PaymentModal;
