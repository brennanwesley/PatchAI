import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiActivity, FiBarChart2, FiGlobe, FiDollarSign, FiFileText } from 'react-icons/fi';

const LandingPage = () => {
  const [currentTestimonial, setCurrentTestimonial] = useState(0);
  const navigate = useNavigate();

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
      <nav className="bg-white dark:bg-gray-900 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <span className="text-xl font-bold text-blue-600 dark:text-blue-400">PatchAI</span>
            </div>
            <div className="flex items-center space-x-4">
              <button 
                onClick={() => navigate('/login')}
                className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 hover:text-blue-600 dark:hover:text-blue-400"
              >
                Log In
              </button>
              <button 
                onClick={() => navigate('/signup')}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Get Started
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <div className="py-20 px-4 sm:px-6 lg:px-8 text-center">
        <h1 className="text-4xl md:text-5xl lg:text-6xl font-extrabold text-gray-900 dark:text-white mb-6">
          Your Virtual Oilfield Consultant
        </h1>
        <p className="text-xl text-gray-600 dark:text-gray-300 max-w-3xl mx-auto mb-12">
          AI-powered insights and recommendations for the modern energy professional
        </p>
        <div className="flex flex-col sm:flex-row justify-center gap-4">
          <button 
            onClick={() => navigate('/signup')}
            className="px-8 py-3 text-base font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-all duration-200 transform hover:scale-105"
          >
            Start Free Trial
          </button>
          <button 
            onClick={() => document.getElementById('features').scrollIntoView({ behavior: 'smooth' })}
            className="px-8 py-3 text-base font-medium text-blue-600 bg-white dark:bg-gray-800 border border-blue-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-all duration-200"
          >
            Learn More
          </button>
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
              Trusted by Energy Professionals
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
          <div className="mt-8">
            <button 
              onClick={() => navigate('/signup')}
              className="px-8 py-3 text-base font-medium text-blue-600 bg-white rounded-md hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-white focus:ring-offset-blue-600 transition-all duration-200 transform hover:scale-105"
            >
              Get Started for Free
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
                © {new Date().getFullYear()} PatchAI. All rights reserved.
              </span>
            </div>
            <div className="mt-4 md:mt-0">
              <div className="flex space-x-6">
                <a href="#" className="text-gray-500 hover:text-gray-600 dark:text-gray-400 dark:hover:text-gray-300">
                  <span className="sr-only">Privacy</span>
                  Privacy Policy
                </a>
                <a href="#" className="text-gray-500 hover:text-gray-600 dark:text-gray-400 dark:hover:text-gray-300">
                  <span className="sr-only">Terms</span>
                  Terms of Service
                </a>
                <a href="#" className="text-gray-500 hover:text-gray-600 dark:text-gray-400 dark:hover:text-gray-300">
                  <span className="sr-only">Contact</span>
                  Contact Us
                </a>
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
