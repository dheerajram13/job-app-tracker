import React from 'react';
import { useAuth } from '../../hooks/useAuth';
import { jobService } from '../../services/api';

export const ApiWrapper = ({ children }) => {
  const { getTokenSilently } = useAuth();

  // Override the default API methods with authenticated versions
  const authenticatedJobService = {
    ...jobService,
    scrapeJobs: async (searchParams) => {
      try {
        const token = await getTokenSilently();
        if (!token) {
          throw new Error('Not authenticated');
        }
        // Pass the token to the API call
        return jobService.scrapeJobs({ ...searchParams, token });
      } catch (error) {
        console.error('Error in API wrapper:', error);
        throw error;
      }
    }
  };

  return (
    <React.Fragment>
      {React.Children.map(children, child => 
        React.cloneElement(child, { jobService: authenticatedJobService })
      )}
    </React.Fragment>
  );
};
