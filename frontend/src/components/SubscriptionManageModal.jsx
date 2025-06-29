import React, { useState } from 'react';
import ReactDOM from 'react-dom';
import { requestSubscriptionCancellation } from '../services/cancellationService';

export default function SubscriptionManageModal({ isOpen, onClose, subscription }) {
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [showFinalMessage, setShowFinalMessage] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  if (!isOpen) return null;

  const handleUpgradeClick = () => {
    // Placeholder for future upgrade functionality
    console.log('Upgrade to Premium clicked - Coming Soon!');
  };

  const handleCancelClick = () => {
    // Show confirmation dialog
    setShowConfirmation(true);
  };

  const handleConfirmCancel = async () => {
    try {
      setIsProcessing(true);
      
      // Call backend to log cancellation request
      const result = await requestSubscriptionCancellation('User requested cancellation via modal');
      
      console.log('✅ Cancellation request logged:', result);
      
      // Hide confirmation and show final message
      setShowConfirmation(false);
      setShowFinalMessage(true);
      
    } catch (error) {
      console.error('❌ Cancellation request failed:', error);
      alert(`Failed to process cancellation request: ${error.message}`);
      setShowConfirmation(false);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleCancelCancel = () => {
    setShowConfirmation(false);
  };

  const handleCloseFinalMessage = () => {
    setShowFinalMessage(false);
    onClose();
  };

  // Confirmation Dialog
  if (showConfirmation) {
    const confirmationContent = (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-red-900">
              Cancel Subscription
            </h2>
            <button
              onClick={handleCancelCancel}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Confirmation Content */}
          <div className="p-6">
            <div className="text-center mb-6">
              <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100 mb-4">
                <svg className="h-6 w-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Are you sure you want to cancel your subscription to PatchAI?
              </h3>
              <p className="text-sm text-gray-600">
                This will log your cancellation request for review.
              </p>
            </div>

            {/* Action Buttons */}
            <div className="flex space-x-3">
              <button
                onClick={handleCancelCancel}
                disabled={isProcessing}
                className="flex-1 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
              >
                No, Keep Subscription
              </button>
              <button
                onClick={handleConfirmCancel}
                disabled={isProcessing}
                className="flex-1 px-4 py-2 text-sm font-medium text-white bg-red-600 border border-transparent rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50"
              >
                {isProcessing ? 'Processing...' : 'Yes, Cancel'}
              </button>
            </div>
          </div>
        </div>
      </div>
    );
    return ReactDOM.createPortal(confirmationContent, document.body);
  }

  // Final Message
  if (showFinalMessage) {
    const finalMessageContent = (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900">
              Subscription Cancelled
            </h2>
            <button
              onClick={handleCloseFinalMessage}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Final Message Content */}
          <div className="p-6 text-center">
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-blue-100 mb-4">
              <svg className="h-6 w-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Sorry to see you go!
            </h3>
            <p className="text-sm text-gray-600 mb-6">
              Your subscription has been cancelled. We've logged your request and will process it shortly.
            </p>
            <button
              onClick={handleCloseFinalMessage}
              className="w-full px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    );
    return ReactDOM.createPortal(finalMessageContent, document.body);
  }

  // Main Modal Content
  const modalContent = (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">
            Manage Subscription
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Current Plan Info */}
          <div className="mb-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
            <h3 className="font-medium text-blue-900 mb-2">Current Plan</h3>
            <div className="text-sm text-blue-700">
              <p className="font-medium">
                {subscription?.plan_name || 'Standard Plan'}
              </p>
              <p className="text-blue-600">
                Status: {subscription?.subscription_status === 'active' ? '✅ Active' : '⚠️ Inactive'}
              </p>
              {subscription?.current_period_end && (
                <p className="text-blue-600">
                  Next billing: {new Date(subscription.current_period_end).toLocaleDateString()}
                </p>
              )}
            </div>
          </div>

          {/* Action Options */}
          <div className="space-y-3">
            {/* Upgrade Option */}
            <button
              onClick={handleUpgradeClick}
              className="w-full p-4 text-left border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-all group"
            >
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-medium text-gray-900 group-hover:text-blue-900">
                    🚀 Upgrade to Premium
                  </h4>
                  <p className="text-sm text-gray-600 group-hover:text-blue-700">
                    Access advanced features and priority support
                  </p>
                </div>
                <div className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded-full">
                  Coming Soon
                </div>
              </div>
            </button>

            {/* Cancel Option */}
            <button
              onClick={handleCancelClick}
              className="w-full p-4 text-left border border-gray-200 rounded-lg hover:border-red-300 hover:bg-red-50 transition-all group"
            >
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-medium text-gray-900 group-hover:text-red-900">
                    ❌ Cancel Plan
                  </h4>
                  <p className="text-sm text-gray-600 group-hover:text-red-700">
                    Cancel your subscription and downgrade to free tier
                  </p>
                </div>
              </div>
            </button>
          </div>

          {/* Help Text */}
          <div className="mt-6 p-3 bg-gray-50 rounded-lg">
            <p className="text-xs text-gray-600 text-center">
              Need help? Contact support at{' '}
              <a href="mailto:support@patchai.app" className="text-blue-600 hover:text-blue-800">
                support@patchai.app
              </a>
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end p-6 border-t border-gray-200">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );

  // Render modal using portal
  return ReactDOM.createPortal(modalContent, document.body);
}
