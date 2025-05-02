import { useAuth0 } from '@auth0/auth0-react';

export const useAuth = () => {
  const { getAccessTokenSilently, isAuthenticated } = useAuth0();

  const getTokenSilently = async () => {
    try {
      return await getAccessTokenSilently();
    } catch (error) {
      console.error('Error getting token:', error);
      return null;
    }
  };

  return {
    getTokenSilently,
    isAuthenticated
  };
};
