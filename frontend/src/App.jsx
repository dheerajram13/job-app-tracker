import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth0 } from '@auth0/auth0-react';
import Dashboard from './components/dashboard/Dashboard';
import Login from './components/auth/Login';
import Loading from './components/common/Loading';
import Navbar from './components/layout/Navbar';
import JobForm from './components/jobs/JobForm';
import ScrapedJobs from './components/jobs/ScrapedJobs';
import { ApiWrapper } from './components/api/ApiWrapper';

function App() {
  const { isLoading, isAuthenticated, error } = useAuth0();
  const [showJobForm, setShowJobForm] = useState(false);

  if (error) {
    return <div>Authentication Error: {error.message}</div>;
  }

  // Handle Auth0 loading state
  if (isLoading) {
    // Don't show loading screen during token refresh
    if (localStorage.getItem('auth0_token_refresh')) {
      return <div className="min-h-screen bg-gray-50" />;
    }
    // Show loading screen during initial authentication
    return <Loading />;
  }

  // Set flag for token refresh
  if (isAuthenticated) {
    localStorage.setItem('auth0_token_refresh', 'true');
  }

  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        {isAuthenticated && <Navbar onAddClick={() => setShowJobForm(true)} />}
        
        <div className="py-6">
          <Routes>
            <Route
              path="/login"
              element={isAuthenticated ? <Navigate to="/dashboard" /> : <Login />}
            />
            <Route
              path="/dashboard/*"
              element={
                isAuthenticated ? (
                  <ApiWrapper>
                    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                      <Dashboard />
                    </div>
                  </ApiWrapper>
                ) : (
                  <Navigate to="/login" />
                )
              }
            />
            <Route path="/" element={<Navigate to="/dashboard" />} />
            <Route
              path="/recommended-jobs"
              element={
                isAuthenticated ? (
                  <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <ScrapedJobs />
                  </div>
                ) : (
                  <Navigate to="/login" />
                )
              }
            />
          </Routes>
        </div>

        {showJobForm && (
          <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full m-4">
              <JobForm
                onSubmit={async (formData, token) => {
                  // Handle job submission
                  setShowJobForm(false);
                  // You might want to refresh the dashboard data here
                }}
                onClose={() => setShowJobForm(false)}
              />
            </div>
          </div>
        )}
      </div>
    </Router>
  );
}

export default App;