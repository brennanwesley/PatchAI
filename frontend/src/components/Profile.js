import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { supabase } from '../supabaseClient';

export default function Profile({ isOpen, onClose }) {
  const { user } = useAuth();
  const [profile, setProfile] = useState(null);
  const [referralInfo, setReferralInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [copySuccess, setCopySuccess] = useState(false);
  
  // Form state
  const [displayName, setDisplayName] = useState('');
  const [company, setCompany] = useState('');

  // Get API URL from environment
  const API_URL = process.env.REACT_APP_BACKEND_URL || process.env.NEXT_PUBLIC_API_URL || 'https://patchai-backend.onrender.com';

  const getAuthToken = async () => {
    try {
      const { data: { session }, error } = await supabase.auth.getSession();
      if (error) throw error;
      return session?.access_token;
    } catch (error) {
      console.error('Error getting auth token:', error);
      return null;
    }
  };

  const fetchProfileData = useCallback(async () => {
    try {
      setLoading(true);
      setError('');

      const token = await getAuthToken();
      if (!token) {
        throw new Error('Authentication required');
      }

      // Fetch profile data
      const profileResponse = await fetch(`${API_URL}/referrals/profile`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!profileResponse.ok) {
        throw new Error('Failed to fetch profile data');
      }

      const profileData = await profileResponse.json();
      setProfile(profileData);
      setDisplayName(profileData.display_name || '');
      setCompany(profileData.company || '');

      // Fetch referral information
      const referralResponse = await fetch(`${API_URL}/referrals/info`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (referralResponse.ok) {
        const referralData = await referralResponse.json();
        setReferralInfo(referralData);
      }

    } catch (error) {
      console.error('Error fetching profile data:', error);
      setError(error.message || 'Failed to load profile data');
    } finally {
      setLoading(false);
    }
  }, [API_URL]);

  useEffect(() => {
    if (isOpen && user) {
      fetchProfileData();
    }
  }, [isOpen, user, fetchProfileData]);

  const handleSaveProfile = async () => {
    try {
      setSaving(true);
      setError('');
      setSuccess('');

      const token = await getAuthToken();
      if (!token) {
        throw new Error('Authentication required');
      }

      const response = await fetch(`${API_URL}/referrals/profile`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          display_name: displayName.trim() || null,
          company: company.trim() || null,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update profile');
      }

      const updatedProfile = await response.json();
      setProfile(updatedProfile);
      setSuccess('Profile updated successfully!');
      
      // Clear success message after 3 seconds
      setTimeout(() => setSuccess(''), 3000);

    } catch (error) {
      console.error('Error updating profile:', error);
      setError(error.message || 'Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  const generateReferralCode = async () => {
    try {
      setError('');

      const token = await getAuthToken();
      if (!token) {
        throw new Error('Authentication required');
      }

      const response = await fetch(`${API_URL}/referrals/generate-code`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to generate referral code');
      }

      const data = await response.json();
      
      // Update referral info with new code
      setReferralInfo(prev => ({
        ...prev,
        referral_code: data.referral_code
      }));

    } catch (error) {
      console.error('Error generating referral code:', error);
      setError(error.message || 'Failed to generate referral code');
    }
  };

  const copyReferralCode = async () => {
    if (referralInfo?.referral_code) {
      try {
        await navigator.clipboard.writeText(referralInfo.referral_code);
        setCopySuccess(true);
        setTimeout(() => setCopySuccess(false), 2000);
      } catch (error) {
        console.error('Failed to copy referral code:', error);
      }
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
        <div className="mt-3">
          {/* Header */}
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-medium text-gray-900">Profile & Referrals</h3>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {loading ? (
            <div className="flex justify-center py-4">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Error/Success Messages */}
              {error && (
                <div className="rounded-md bg-red-50 p-4">
                  <div className="text-sm text-red-700">{error}</div>
                </div>
              )}
              {success && (
                <div className="rounded-md bg-green-50 p-4">
                  <div className="text-sm text-green-700">{success}</div>
                </div>
              )}

              {/* Profile Information */}
              <div className="space-y-4">
                <h4 className="text-md font-medium text-gray-900">Profile Information</h4>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">Email</label>
                  <div className="mt-1 text-sm text-gray-900 bg-gray-50 px-3 py-2 rounded-md">
                    {profile?.email || user?.email}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Display Name</label>
                  <input
                    type="text"
                    value={displayName}
                    onChange={(e) => setDisplayName(e.target.value)}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    placeholder="Enter your display name"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Company</label>
                  <input
                    type="text"
                    value={company}
                    onChange={(e) => setCompany(e.target.value)}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    placeholder="Enter your company name"
                  />
                </div>

                <button
                  onClick={handleSaveProfile}
                  disabled={saving}
                  className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                >
                  {saving ? 'Saving...' : 'Save Profile'}
                </button>
              </div>

              {/* Referral Information */}
              <div className="space-y-4 border-t pt-4">
                <h4 className="text-md font-medium text-gray-900">Referral Program</h4>
                
                {/* User's Referral Code */}
                <div>
                  <label className="block text-sm font-medium text-gray-700">Your Referral Code</label>
                  {referralInfo?.referral_code ? (
                    <div className="mt-1 flex">
                      <div className="flex-1 text-lg font-mono bg-gray-50 px-3 py-2 rounded-l-md border border-r-0 border-gray-300">
                        {referralInfo.referral_code}
                      </div>
                      <button
                        onClick={copyReferralCode}
                        className="px-3 py-2 border border-gray-300 rounded-r-md bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        {copySuccess ? (
                          <svg className="h-5 w-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                          </svg>
                        ) : (
                          <svg className="h-5 w-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                          </svg>
                        )}
                      </button>
                    </div>
                  ) : (
                    <div className="mt-1">
                      <button
                        onClick={generateReferralCode}
                        className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        Generate Referral Code
                      </button>
                    </div>
                  )}
                  <p className="mt-1 text-xs text-gray-500">
                    Share this code with friends to earn referral rewards!
                  </p>
                </div>

                {/* Referral Stats */}
                {referralInfo && (
                  <div className="grid grid-cols-2 gap-4 text-center">
                    <div className="bg-blue-50 p-3 rounded-md">
                      <div className="text-2xl font-bold text-blue-600">
                        {referralInfo.total_referrals || 0}
                      </div>
                      <div className="text-xs text-gray-600">Total Referrals</div>
                    </div>
                    <div className="bg-green-50 p-3 rounded-md">
                      <div className="text-2xl font-bold text-green-600">
                        ${(referralInfo.total_rewards || 0).toFixed(2)}
                      </div>
                      <div className="text-xs text-gray-600">Total Rewards</div>
                    </div>
                  </div>
                )}

                {/* Referred By Information */}
                {referralInfo?.referred_by_email && (
                  <div className="bg-gray-50 p-3 rounded-md">
                    <div className="text-sm text-gray-600">
                      You were referred by: <span className="font-medium">{referralInfo.referred_by_email}</span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
