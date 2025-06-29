import React from 'react';
import ReactDOM from 'react-dom';

export default function SubscriptionManageModal({ isOpen, onClose, subscription }) {
  if (!isOpen) return null;

  const handleUpgradeClick = () => {
    // Placeholder for future upgrade functionality
    console.log('Upgrade to Premium clicked - Coming Soon!');
  };

  const handleCancelClick = () => {
    // Placeholder for future cancel functionality
    console.log('Cancel Plan clicked - Coming Soon!');
  };

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
                <div className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-full">
                  Coming Soon
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
