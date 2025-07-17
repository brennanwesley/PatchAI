import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { FiActivity, FiBarChart2, FiGlobe, FiDollarSign, FiFileText, FiLogIn, FiUserPlus } from 'react-icons/fi';

const LandingPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [customerName, setCustomerName] = useState('');
  const [referralCode, setReferralCode] = useState('');
  const [referralValidation, setReferralValidation] = useState({ valid: null, message: '' });
  const [isLogin, setIsLogin] = useState(true);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showPrivacyModal, setShowPrivacyModal] = useState(false);
  const [showTermsModal, setShowTermsModal] = useState(false);
  const [showContactModal, setShowContactModal] = useState(false);
  const { login, signUp } = useAuth();



  // Validate referral code as user types
  const validateReferralCode = async (code) => {
    if (!code || code.length !== 6) {
      setReferralValidation({ valid: null, message: '' });
      return;
    }

    try {
      const API_URL = process.env.REACT_APP_BACKEND_URL || process.env.NEXT_PUBLIC_API_URL || 'https://patchai-backend.onrender.com';
      const response = await fetch(`${API_URL}/referrals/validate-code`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ referral_code: code.toUpperCase() }),
      });

      const data = await response.json();
      
      if (response.ok) {
        setReferralValidation({
          valid: data.valid,
          message: data.valid 
            ? `Valid referral code from ${data.referring_user_email}` 
            : 'Referral code not found'
        });
      } else {
        setReferralValidation({ valid: false, message: 'Invalid referral code format' });
      }
    } catch (error) {
      console.error('Error validating referral code:', error);
      setReferralValidation({ valid: false, message: 'Unable to validate referral code' });
    }
  };

  const handleAuth = async (e) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      if (isLogin) {
        // Sign in
        await login(email, password);
      } else {
        // Sign up - pass referral code if provided
        const finalReferralCode = referralCode.trim().toUpperCase() || null;
        await signUp(email, password, finalReferralCode, customerName);
        
        // Store customer name and email locally for immediate use
        if (customerName.trim()) {
          localStorage.setItem('customer_name', customerName.trim());
        }
        localStorage.setItem('userEmail', email);
        
        // Show success message and switch to login
        setError({
          type: 'success',
          message: 'Account created successfully! Please check your email to verify your account.',
        });
        setIsLogin(true);
        setPassword('');
        setCustomerName('');
        setReferralCode('');
        setReferralValidation({ valid: null, message: '' });
      }
    } catch (error) {
      console.error('Authentication error:', error);
      setError({
        type: 'error',
        message: error.message || 'An error occurred during authentication. Please try again.'
      });
    } finally {
      setIsLoading(false);
    }
  };
  const [currentTestimonial, setCurrentTestimonial] = useState(0);
  const features = [
    {
      icon: <FiActivity className="w-8 h-8 text-blue-500" />,
      title: 'Production Operations',
      description: 'Optimize well performance and troubleshoot operational challenges'
    },
    {
      icon: <FiBarChart2 className="w-8 h-8 text-green-500" />,
      title: 'Data Analytics & Recommendations',
      description: 'Get actionable insights from your operational data'
    },
    {
      icon: <FiGlobe className="w-8 h-8 text-purple-500" />,
      title: 'Geologic Research',
      description: 'Access geological insights and formation analysis'
    },
    {
      icon: <FiDollarSign className="w-8 h-8 text-yellow-500" />,
      title: 'Asset Economics',
      description: 'Model economic scenarios and forecast production'
    },
    {
      icon: <FiFileText className="w-8 h-8 text-red-500" />,
      title: 'Regulatory & Permitting',
      description: 'Navigate compliance requirements with confidence'
    }
  ];

  const testimonials = [
    {
      text: "PatchAI has boosted my productivity!",
      author: "Operations Engineer for a Mid-Cap E&P"
    },
    {
      text: "WOW! I'm using PatchAI to help me understand standard oilfield operations, it's so helpful!",
      author: "Secretary for a Roustabout Service Company"
    },
    {
      text: "The most intuitive oilfield assistant I've used. Saves me hours every week.",
      author: "Field Supervisor, Permian Basin"
    }
  ];

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTestimonial((prev) => (prev + 1) % testimonials.length);
    }, 5000);
    return () => clearInterval(timer);
  }, [testimonials.length]);

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
      {/* Navigation */}
      <nav className="bg-white dark:bg-gray-900 shadow-sm fixed w-full z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <span className="text-2xl md:text-3xl font-bold text-blue-600 dark:text-blue-400 font-mono tracking-wide">
                Welcome Keith! PatchAI is your helpful friend.
              </span>
            </div>
            <div className="flex items-center space-x-4">
              <button 
                onClick={() => {
                  setIsLogin(true);
                  window.scrollTo({ top: 0, behavior: 'smooth' });
                }}
                className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 hover:text-blue-600 dark:hover:text-blue-400"
              >
                Sign In
              </button>
              <button 
                onClick={() => {
                  setIsLogin(false);
                  window.scrollTo({ top: 0, behavior: 'smooth' });
                }}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors duration-200"
              >
                Get Started
              </button>
            </div>
          </div>
        </div>
      </nav>
      <div className="h-16"></div> {/* Spacer for fixed nav */}

      {/* Hero Section */}
      <div className="py-12 md:py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="lg:grid lg:grid-cols-2 lg:gap-12 items-center">
            {/* Left side - Hero text */}
            <div className="text-center lg:text-left mb-12 lg:mb-0">
              <h1 className="text-4xl md:text-5xl lg:text-6xl font-extrabold text-gray-900 dark:text-white mb-6">
                Your Personal Oilfield Consultant
              </h1>
              <p className="text-xl text-gray-600 dark:text-gray-300 mb-8">
                AI-powered insights and recommendations for the modern oil and gas professional
              </p>
              <button 
                onClick={() => document.getElementById('features').scrollIntoView({ behavior: 'smooth' })}
                className="hidden lg:inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-blue-700 bg-blue-100 hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors duration-200"
              >
                Learn More
              </button>
            </div>

            {/* Right side - Auth form */}
            <div className="bg-white dark:bg-gray-800 shadow-lg rounded-lg p-6 md:p-8">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                  {isLogin ? 'Sign In' : 'Create Account'}
                </h2>
                <button
                  onClick={() => setIsLogin(!isLogin)}
                  className="text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
                >
                  {isLogin ? 'Need an account? Sign up' : 'Already have an account? Sign in'}
                </button>
              </div>

              {error && (
                <div className={`p-3 rounded-md text-sm ${
                  error.type === 'error' 
                    ? 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300' 
                    : 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300'
                }`}>
                  {error.message}
                </div>
              )}

              <form onSubmit={handleAuth} className="space-y-4">
                {isLogin ? (
                  <div>
                    <label htmlFor="email" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Email address
                    </label>
                    <input
                      id="email"
                      name="email"
                      type="email"
                      autoComplete="email"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                      placeholder="you@example.com"
                      disabled={isLoading}
                    />
                  </div>
                ) : (
                  <>
                    <div>
                      <label htmlFor="customerName" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Full Name
                      </label>
                      <input
                        id="customerName"
                        name="customerName"
                        type="text"
                        autoComplete="name"
                        required
                        value={customerName}
                        onChange={(e) => setCustomerName(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                        placeholder="John Doe"
                        disabled={isLoading}
                      />
                    </div>
                    <div>
                      <label htmlFor="email" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Email address
                      </label>
                      <input
                        id="email"
                        name="email"
                        type="email"
                        autoComplete="email"
                        required
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                        placeholder="you@example.com"
                        disabled={isLoading}
                      />
                    </div>
                    <div>
                      <label htmlFor="referralCode" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Referral Code (optional)
                      </label>
                      <input
                        id="referralCode"
                        name="referralCode"
                        type="text"
                        maxLength={6}
                        value={referralCode}
                        onChange={(e) => {
                          setReferralCode(e.target.value);
                          validateReferralCode(e.target.value);
                        }}
                        className={`w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white ${referralValidation.valid === false ? 'border-red-500' : ''}`}
                        placeholder="XXXXXX"
                        disabled={isLoading}
                      />
                      {referralValidation.valid !== null && (
                        <p className={`mt-1 text-xs ${referralValidation.valid ? 'text-green-600' : 'text-red-600'}`}>
                          {referralValidation.message}
                        </p>
                      )}
                    </div>
                  </>
                )}
                <div>
                  <label htmlFor="password" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Password
                  </label>
                  <div className="relative">
                    <input
                      id="password"
                      name="password"
                      type={showPassword ? 'text' : 'password'}
                      autoComplete={isLogin ? 'current-password' : 'new-password'}
                      required
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white pr-10"
                      placeholder={isLogin ? '••••••••' : 'At least 8 characters'}
                      disabled={isLoading}
                      minLength={isLogin ? undefined : 8}
                    />
                    <button
                      type="button"
                      className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                      onClick={() => setShowPassword(!showPassword)}
                      tabIndex="-1"
                    >
                      {showPassword ? (
                        <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                        </svg>
                      ) : (
                        <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                        </svg>
                      )}
                    </button>
                  </div>
                  {!isLogin && (
                    <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                      Use at least 8 characters, one letter, and one number
                    </p>
                  )}
                </div>

                <div>
                  <button
                    type="submit"
                    disabled={isLoading}
                    className={`w-full flex justify-center items-center py-2.5 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white focus:outline-none focus:ring-2 focus:ring-offset-2 ${
                      isLoading
                        ? 'bg-blue-400 cursor-not-allowed'
                        : 'bg-blue-600 hover:bg-blue-700 focus:ring-blue-500'
                    }`}
                  >
                    {isLoading ? (
                      <>
                        <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Processing...
                      </>
                    ) : isLogin ? (
                      <>
                        <FiLogIn className="w-4 h-4 mr-2" />
                        Sign In
                      </>
                    ) : (
                      <>
                        <FiUserPlus className="w-4 h-4 mr-2" />
                        Create Account
                      </>
                    )}
                  </button>
                </div>
                

              </form>
            </div>
          </div>
        </div>
      </div>

      {/* Features Grid */}
      <div id="features" className="py-16 bg-white dark:bg-gray-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-extrabold text-gray-900 dark:text-white sm:text-4xl">
              Comprehensive Oilfield Intelligence
            </h2>
            <p className="mt-4 text-xl text-gray-600 dark:text-gray-300 max-w-3xl mx-auto">
              Everything you need to make informed decisions, all in one place
            </p>
          </div>
          
          <div className="grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
            {features.map((feature, index) => (
              <div 
                key={index}
                className="p-6 bg-white dark:bg-gray-800 rounded-xl shadow-md hover:shadow-lg transition-shadow duration-300 border border-gray-100 dark:border-gray-700"
              >
                <div className="flex flex-col items-center text-center">
                  <div className="p-3 bg-blue-50 dark:bg-blue-900/30 rounded-full mb-4">
                    {feature.icon}
                  </div>
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                    {feature.title}
                  </h3>
                  <p className="text-gray-600 dark:text-gray-300 text-sm">
                    {feature.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Testimonial Section */}
      <div className="py-16 bg-gray-50 dark:bg-gray-800">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-extrabold text-gray-900 dark:text-white sm:text-4xl">
              Trusted by Oil & Gas Professionals
            </h2>
          </div>
          
          <div className="relative">
            <div className="overflow-hidden">
              <div className="transition-all duration-500 ease-in-out">
                <div className="bg-white dark:bg-gray-900 p-8 rounded-xl shadow-lg">
                  <blockquote className="text-center">
                    <p className="text-xl font-medium text-gray-700 dark:text-gray-200 mb-4">
                      "{testimonials[currentTestimonial].text}"
                    </p>
                    <footer className="text-blue-600 dark:text-blue-400 font-medium">
                      — {testimonials[currentTestimonial].author}
                    </footer>
                  </blockquote>
                </div>
              </div>
            </div>
            
            <div className="flex justify-center mt-6 space-x-2">
              {testimonials.map((_, index) => (
                <button
                  key={index}
                  onClick={() => setCurrentTestimonial(index)}
                  className={`w-3 h-3 rounded-full ${currentTestimonial === index ? 'bg-blue-600' : 'bg-gray-300 dark:bg-gray-600'}`}
                  aria-label={`View testimonial ${index + 1}`}
                />
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="bg-blue-600 dark:bg-blue-900">
        <div className="max-w-4xl mx-auto py-16 px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-extrabold text-white sm:text-4xl">
            Ready to transform your operations?
          </h2>
          <p className="mt-4 text-xl text-blue-100 max-w-2xl mx-auto">
            Join industry leaders who are already benefiting from AI-powered oilfield intelligence.
          </p>
          <div className="mt-8 flex flex-col sm:flex-row justify-center gap-4">
            <button 
              onClick={() => {
                setIsLogin(false);
                window.scrollTo({ top: 0, behavior: 'smooth' });
              }}
              className="px-8 py-3 text-base font-medium text-blue-600 bg-white rounded-md hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-white focus:ring-offset-blue-600 transition-all duration-200 transform hover:scale-105"
            >
              Get Started for Free
            </button>
            <button 
              onClick={() => {
                setIsLogin(true);
                window.scrollTo({ top: 0, behavior: 'smooth' });
              }}
              className="px-8 py-3 text-base font-medium text-white border border-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-white focus:ring-offset-blue-600 transition-all duration-200"
            >
              Sign In to Your Account
            </button>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-800">
        <div className="max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="flex items-center">
              <span className="text-xl font-bold text-blue-600 dark:text-blue-400">PatchAI</span>
              <span className="ml-4 text-sm text-gray-500 dark:text-gray-400">
                &copy; {new Date().getFullYear()} PatchAI. All rights reserved.
              </span>
            </div>
            <div className="mt-4 md:mt-0">
              <div className="flex space-x-6">
                <button 
                  onClick={() => setShowPrivacyModal(true)}
                  className="text-gray-500 hover:text-gray-600 dark:text-gray-400 dark:hover:text-gray-300 hover:underline focus:outline-none focus:underline"
                >
                  <span className="sr-only">Privacy</span>
                  Privacy Policy
                </button>
                <button 
                  onClick={() => setShowTermsModal(true)}
                  className="text-gray-500 hover:text-gray-600 dark:text-gray-400 dark:hover:text-gray-300 hover:underline focus:outline-none focus:underline"
                >
                  <span className="sr-only">Terms</span>
                  Terms of Service
                </button>
                <button 
                  onClick={() => setShowContactModal(true)}
                  className="text-gray-500 hover:text-gray-600 dark:text-gray-400 dark:hover:text-gray-300 hover:underline focus:outline-none focus:underline"
                >
                  <span className="sr-only">Contact</span>
                  Contact Us
                </button>
              </div>
            </div>
          </div>
        </div>
      </footer>

      {/* Privacy Policy Modal */}
      {showPrivacyModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50" onClick={() => setShowPrivacyModal(false)}>
          <div className="bg-white dark:bg-gray-800 rounded-lg max-w-4xl w-full max-h-[90vh] overflow-hidden" onClick={(e) => e.stopPropagation()}>
            {/* Modal Header */}
            <div className="flex justify-between items-center p-6 border-b border-gray-200 dark:border-gray-700">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Privacy Policy</h2>
              <button
                onClick={() => setShowPrivacyModal(false)}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded-full p-1"
                aria-label="Close Privacy Policy"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            {/* Modal Body - Scrollable */}
            <div className="p-6 overflow-y-auto max-h-[calc(90vh-120px)]">
              <div className="prose prose-sm max-w-none dark:prose-invert">
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                  <strong>Effective Date:</strong> 6/30/2025<br/>
                  <strong>Owned and Operated by:</strong> TeraScale AI Corporation
                </p>

                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mt-6 mb-3">1. Purpose of This Policy</h3>
                <p className="text-gray-700 dark:text-gray-300 mb-4">
                  This Privacy Policy explains how PatchAI ("we", "us", "our") handles user data when you use our AI chatbot. PatchAI is a software tool powered by third-party AI engines (such as OpenAI) and is intended solely for informational research purposes.
                </p>

                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mt-6 mb-3">2. Use at Your Own Risk</h3>
                <p className="text-gray-700 dark:text-gray-300 mb-2">
                  PatchAI is not a source of legal, financial, medical, or other professional advice. You use the service entirely at your own risk.
                </p>
                <ul className="list-disc list-inside text-gray-700 dark:text-gray-300 mb-4 ml-4">
                  <li>We do not warrant the accuracy or reliability of any AI-generated content.</li>
                  <li>Users are solely responsible for how they interpret, use, or act on the information received.</li>
                  <li>TeraScale AI Corporation assumes no liability for any direct, indirect, or consequential outcomes from the use of PatchAI.</li>
                </ul>

                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mt-6 mb-3">3. No Ownership of AI Outputs</h3>
                <p className="text-gray-700 dark:text-gray-300 mb-2">
                  We do not own or claim intellectual property over:
                </p>
                <ul className="list-disc list-inside text-gray-700 dark:text-gray-300 mb-4 ml-4">
                  <li>Any content generated by the AI model</li>
                  <li>The model itself</li>
                  <li>The training data of the model</li>
                  <li>Any embedded third-party data</li>
                </ul>
                <p className="text-gray-700 dark:text-gray-300 mb-4">
                  Generated content is the responsibility of the third-party AI provider and is subject to their licensing terms.
                </p>

                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mt-6 mb-3">4. Data Collection and Privacy</h3>
                <h4 className="text-md font-medium text-gray-900 dark:text-white mt-4 mb-2">a. User Inputs</h4>
                <p className="text-gray-700 dark:text-gray-300 mb-4">
                  We may store user interactions (queries, messages) for short-term operational improvement, abuse prevention, or debugging purposes. We do not sell or monetize user data.
                </p>
                <h4 className="text-md font-medium text-gray-900 dark:text-white mt-4 mb-2">b. File Uploads</h4>
                <p className="text-gray-700 dark:text-gray-300 mb-4">
                  If you upload a file, you do so at your own discretion. We advise against uploading personal, financial, health, or legally sensitive information.
                </p>
                <h4 className="text-md font-medium text-gray-900 dark:text-white mt-4 mb-2">c. Third-Party Processing</h4>
                <p className="text-gray-700 dark:text-gray-300 mb-4">
                  User inputs are transmitted to external AI models (e.g., OpenAI) for processing. By using PatchAI, you consent to this transmission and processing.
                </p>
                <h4 className="text-md font-medium text-gray-900 dark:text-white mt-4 mb-2">d. Cookies and Tracking</h4>
                <p className="text-gray-700 dark:text-gray-300 mb-4">
                  Basic analytics or cookie tools may be used to monitor usage. No targeted advertising tracking is used.
                </p>

                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mt-6 mb-3">5. Children's Privacy</h3>
                <p className="text-gray-700 dark:text-gray-300 mb-4">
                  PatchAI is not intended for users under the age of 13. If you are under 13, do not use this service.
                </p>

                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mt-6 mb-3">6. Changes to This Policy</h3>
                <p className="text-gray-700 dark:text-gray-300 mb-4">
                  We may update this Privacy Policy at any time. Updates take effect upon posting. Continued use of the service means acceptance of the new policy.
                </p>

                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mt-6 mb-3">7. Legal Jurisdiction and Limitation of Liability</h3>
                <p className="text-gray-700 dark:text-gray-300 mb-2">
                  PatchAI is a product of TeraScale AI Corporation, headquartered in the United States.
                </p>
                <ul className="list-disc list-inside text-gray-700 dark:text-gray-300 mb-4 ml-4">
                  <li>Use is governed by the laws of the State of Texas</li>
                  <li>You agree to hold TeraScale AI Corporation harmless for all claims arising from use of the service</li>
                </ul>

                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mt-6 mb-3">8. Contact Us</h3>
                <p className="text-gray-700 dark:text-gray-300 mb-4">
                  Questions about this Privacy Policy can be sent to:<br/>
                  <a href="mailto:feedbacklooploop@gmail.com" className="text-blue-600 dark:text-blue-400 hover:underline">
                    feedbacklooploop@gmail.com
                  </a>
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Terms of Service Modal */}
      {showTermsModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50" onClick={() => setShowTermsModal(false)}>
          <div className="bg-white dark:bg-gray-800 rounded-lg max-w-4xl w-full max-h-[90vh] overflow-hidden" onClick={(e) => e.stopPropagation()}>
            {/* Modal Header */}
            <div className="flex justify-between items-center p-6 border-b border-gray-200 dark:border-gray-700">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Terms of Service</h2>
              <button
                onClick={() => setShowTermsModal(false)}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded-full p-1"
                aria-label="Close Terms of Service"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            {/* Modal Body - Scrollable */}
            <div className="p-6 overflow-y-auto max-h-[calc(90vh-120px)]">
              <div className="prose prose-sm max-w-none dark:prose-invert">
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                  <strong>Effective Date:</strong> 6/30/2025<br/>
                  <strong>Owned and Operated by:</strong> TeraScale AI Corporation
                </p>

                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mt-6 mb-3">1. Acceptance of Terms</h3>
                <p className="text-gray-700 dark:text-gray-300 mb-4">
                  By accessing or using PatchAI, you agree to be bound by these Terms of Service. If you do not agree to these terms, do not use the service.
                </p>

                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mt-6 mb-3">2. Service Description</h3>
                <p className="text-gray-700 dark:text-gray-300 mb-2">
                  PatchAI is an AI-powered assistant designed to provide informational responses for research and analysis. It is not a source of professional advice.
                </p>
                <ul className="list-disc list-inside text-gray-700 dark:text-gray-300 mb-4 ml-4">
                  <li>PatchAI does not provide legal, medical, financial, or engineering certifications.</li>
                  <li>Outputs are generated via third-party AI services and may contain errors or bias.</li>
                </ul>

                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mt-6 mb-3">3. User Responsibilities</h3>
                <p className="text-gray-700 dark:text-gray-300 mb-2">
                  You agree not to:
                </p>
                <ul className="list-disc list-inside text-gray-700 dark:text-gray-300 mb-4 ml-4">
                  <li>Use PatchAI to generate or distribute harmful, illegal, or fraudulent content</li>
                  <li>Upload personal, private, financial, or confidential data</li>
                  <li>Attempt to reverse-engineer, scrape, copy, or clone any part of PatchAI</li>
                  <li>Represent PatchAI output as legally or scientifically authoritative</li>
                  <li>Use PatchAI for commercial decision-making without independent validation</li>
                </ul>
                <p className="text-gray-700 dark:text-gray-300 mb-4">
                  You are solely responsible for any actions taken based on information received from PatchAI.
                </p>

                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mt-6 mb-3">4. Account Access (if applicable)</h3>
                <p className="text-gray-700 dark:text-gray-300 mb-2">
                  If account-based access is added in the future:
                </p>
                <ul className="list-disc list-inside text-gray-700 dark:text-gray-300 mb-4 ml-4">
                  <li>You are responsible for maintaining the security of your login credentials.</li>
                  <li>Any misuse via your account is your liability.</li>
                </ul>

                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mt-6 mb-3">5. Ownership and Intellectual Property</h3>
                <ul className="list-disc list-inside text-gray-700 dark:text-gray-300 mb-4 ml-4">
                  <li>All frontend/backend code, user interface design, business logic, and proprietary content of PatchAI are owned by TeraScale AI Corporation</li>
                  <li>You may not reuse, reproduce, or republish any part of the PatchAI platform without explicit written consent</li>
                  <li>The underlying AI model is owned by the third-party provider (e.g., OpenAI) and is not owned or operated by PatchAI</li>
                </ul>

                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mt-6 mb-3">6. Termination</h3>
                <p className="text-gray-700 dark:text-gray-300 mb-4">
                  We may suspend or terminate access to PatchAI at any time, with or without cause, especially for violations of these terms.
                </p>

                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mt-6 mb-3">7. Disclaimer of Warranties</h3>
                <p className="text-gray-700 dark:text-gray-300 mb-2">
                  PatchAI is provided "as-is" without warranty of any kind. We do not guarantee:
                </p>
                <ul className="list-disc list-inside text-gray-700 dark:text-gray-300 mb-4 ml-4">
                  <li>Accuracy of outputs</li>
                  <li>Availability or uptime</li>
                  <li>Suitability for any specific purpose</li>
                </ul>

                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mt-6 mb-3">8. Limitation of Liability</h3>
                <p className="text-gray-700 dark:text-gray-300 mb-4">
                  To the maximum extent allowed by law, TeraScale AI Corporation is not liable for any damages, losses, or claims resulting from the use or misuse of PatchAI.
                </p>

                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mt-6 mb-3">9. Indemnification</h3>
                <p className="text-gray-700 dark:text-gray-300 mb-4">
                  You agree to defend, indemnify, and hold harmless TeraScale AI Corporation, its officers, and affiliates from any claims, damages, or liabilities arising from your use of PatchAI.
                </p>

                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mt-6 mb-3">10. Governing Law</h3>
                <p className="text-gray-700 dark:text-gray-300 mb-4">
                  These Terms are governed by the laws of the State of Texas, USA. You agree to resolve any legal disputes in that jurisdiction.
                </p>

                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mt-6 mb-3">11. Contact Us</h3>
                <p className="text-gray-700 dark:text-gray-300 mb-4">
                  For questions regarding these Terms of Service:<br/>
                  <a href="mailto:feedbacklooploop@gmail.com" className="text-blue-600 dark:text-blue-400 hover:underline">
                    feedbacklooploop@gmail.com
                  </a>
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Contact Us Modal */}
      {showContactModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50" onClick={() => setShowContactModal(false)}>
          <div className="bg-white dark:bg-gray-800 rounded-lg max-w-2xl w-full max-h-[90vh] overflow-hidden" onClick={(e) => e.stopPropagation()}>
            {/* Modal Header */}
            <div className="flex justify-between items-center p-6 border-b border-gray-200 dark:border-gray-700">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Contact Us</h2>
              <button
                onClick={() => setShowContactModal(false)}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded-full p-1"
                aria-label="Close Contact Us"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            {/* Modal Body */}
            <div className="p-6">
              <div className="text-center">
                <p className="text-gray-700 dark:text-gray-300 mb-6">
                  For general inquiries, feedback, or support related to PatchAI, please contact our team at:
                </p>
                
                <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 mb-6">
                  <div className="flex items-center justify-center space-x-2">
                    <span className="text-2xl">📧</span>
                    <a 
                      href="mailto:feedbacklooploop@gmail.com" 
                      className="text-xl font-semibold text-blue-600 dark:text-blue-400 hover:underline"
                    >
                      feedbacklooploop@gmail.com
                    </a>
                  </div>
                </div>
                
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  We typically respond within 1–2 business days.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};

export default LandingPage;
