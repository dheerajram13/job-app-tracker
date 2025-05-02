import { useAuth0 } from '@auth0/auth0-react';

// Create a service to handle authentication
export const authService = {
  // Get token silently - can only be called from React components
  async getTokenSilently() {
    const { getAccessTokenSilently } = useAuth0();
    try {
      return await getAccessTokenSilently();
    } catch (error) {
      console.error('Error getting token:', error);
      return null;
    }
  },

  // Check if user is authenticated
  isAuthenticated() {
    const { isAuthenticated } = useAuth0();
    return isAuthenticated;
  }
};

// Export the useAuth0 hook for components
export { useAuth0 };
