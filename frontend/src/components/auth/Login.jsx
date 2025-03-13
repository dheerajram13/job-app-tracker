// src/components/auth/Login.jsx
import React from 'react';
import { useAuth0 } from '@auth0/auth0-react';

const Login = () => {
  const { loginWithRedirect } = useAuth0();

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8 p-8 bg-white rounded-lg shadow-lg">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Job Application Tracker
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Track and manage your job applications in one place
          </p>
        </div>
        <button
          onClick={() => loginWithRedirect()}
          className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
        >
          Sign in to continue
        </button>
      </div>
    </div>
  );
};

export default Login;