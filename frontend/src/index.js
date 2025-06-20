import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { supabase } from './supabaseClient';
import './index.css';
import App from './App';
import LandingPage from './components/LandingPage';
import reportWebVitals from './reportWebVitals';

// Auth wrapper component to protect routes
const PrivateRoute = ({ children }) => {
  const [loading, setLoading] = React.useState(true);
  const [session, setSession] = React.useState(null);
  const [initialCheckDone, setInitialCheckDone] = React.useState(false);
  const navigate = useNavigate();

  React.useEffect(() => {
    let mounted = true;

    const checkAuth = async () => {
      try {
        // Check for existing session
        const { data: { session } } = await supabase.auth.getSession();
        if (mounted) {
          setSession(session);
          setInitialCheckDone(true);
        }
      } catch (error) {
        console.error('Error checking auth:', error);
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      if (mounted) {
        setSession(session);
        setInitialCheckDone(true);
        setLoading(false);
        
        // Only redirect if we're not already on the right page
        if (session && window.location.pathname !== '/chat') {
          navigate('/chat');
        } else if (!session) {
          navigate('/');
        }
      }
    });

    // Initial auth check
    checkAuth();

    return () => {
      mounted = false;
      subscription?.unsubscribe();
    };
  }, [navigate]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50 dark:bg-gray-900">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  // Only render the protected route if we have a session and initial check is done
  if (!session && initialCheckDone) {
    return <Navigate to="/" replace />;
  }
  
  if (session) {
    return React.cloneElement(children, { user: session.user, loading });
  }
  
  return null;
};

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <Router>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route
          path="/chat"
          element={
            <PrivateRoute>
              <App />
            </PrivateRoute>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  </React.StrictMode>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
