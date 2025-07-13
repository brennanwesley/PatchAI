import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

export default function AuthCallback() {
  const navigate = useNavigate();

  useEffect(() => {
    // Get the hash fragment from the URL
    const hash = window.location.hash.substring(1);
    const hashParams = new URLSearchParams(hash);
    
    // Check if this is a password reset callback
    const accessToken = hashParams.get('access_token');
    const type = hashParams.get('type');
    
    if (accessToken && type === 'recovery') {
      // This is a password reset callback, redirect to reset password page with the tokens
      const resetUrl = `/reset-password${window.location.hash}`;
      navigate(resetUrl, { replace: true });
    } else {
      // For other auth callbacks, redirect to home or login
      navigate('/', { replace: true });
    }
  }, [navigate]);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-gray-600 dark:text-gray-300">Processing authentication...</p>
      </div>
    </div>
  );
}
