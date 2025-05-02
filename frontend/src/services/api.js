import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

// Create axios instance
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth0Token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor to handle 401 errors
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response && error.response.status === 401) {
      // Handle unauthorized error
      // This will trigger Auth0's login flow
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const jobService = {

  getAllJobs: async (token) => {
    try {
      const response = await api.get('/jobs/', {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching jobs:', error);
      throw error;
    }
  },

  createJob: async (jobData, token) => {
    try {
      const response = await api.post('/jobs/', jobData, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      return response.data;
    } catch (error) {
      console.error('Error creating job:', error);
      throw error;
    }
  },

  updateJob: async (id, jobData, token) => {
    try {
      const response = await api.put(`/jobs/${id}`, jobData, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      return response.data;
    } catch (error) {
      console.error('Error updating job:', error);
      throw error;
    }
  },

  deleteJob: async (id, token) => {
    try {
      const response = await api.delete(`/jobs/${id}`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      return response.data;
    } catch (error) {
      console.error('Error deleting job:', error);
      throw error;
    }
  },

  parseJobUrl: async (url, token) => {
    try {
      const response = await api.post('/jobs/parse-url', { url }, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      return response.data;
    } catch (error) {
      console.error('Error parsing job URL:', error);
      throw error;
    }
  },
  
  // Enhanced job scraping with support for multiple sites and options
  scrapeJobs: async (searchParams, token) => {
    try {
      // Store the token in localStorage for the interceptor
      if (token) {
        localStorage.setItem('auth0Token', token);
      }
      
      const response = await api.post('/jobs/scrape', searchParams, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      return response.data;
    } catch (error) {
      console.error('Error scraping jobs:', error);
      throw error;
    }
  },
  
  getScrapedJobs: async (taskId, token) => {
    try {
      const response = await api.get(`/jobs/scrape/${taskId}`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      return response.data;
    } catch (error) {
      console.error('Error getting scraped jobs:', error);
      throw error;
    }
  },
  
  addScrapedJob: async (jobData, token) => {
    try {
      const response = await api.post('/jobs/add-scraped', jobData, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      return response.data;
    } catch (error) {
      console.error('Error adding scraped job:', error);
      throw error;
    }
  },

  // Advanced search capabilities
  advancedSearch: async (searchParams, token) => {
    try {
      const response = await api.post('/jobs/advanced-search', searchParams, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      return response.data;
    } catch (error) {
      console.error('Error performing advanced search:', error);
      throw error;
    }
  },
  
  // Multi-site job search
  multiSiteSearch: async (sites, searchTerm, location, token) => {
    try {
      const response = await api.post('/jobs/scrape', {
        site_name: sites,
        search_term: searchTerm,
        location: location || 'Australia',
        num_jobs: 50,
        sort_order: 'desc'
      }, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      return response.data;
    } catch (error) {
      console.error('Error performing multi-site search:', error);
      throw error;
    }
  }
};

// Resume-related operations
export const resumeService = {
  getAllResumes: async () => {
    const response = await api.get('/resumes/');
    return response.data;
  },
  
  getResume: async (id) => {
    const response = await api.get(`/resumes/${id}`);
    return response.data;
  },
  
  createResume: async (resumeData) => {
    const response = await api.post('/resumes/', resumeData);
    return response.data;
  },
  
  updateResume: async (id, resumeData) => {
    const response = await api.put(`/resumes/${id}`, resumeData);
    return response.data;
  },
  
  deleteResume: async (id) => {
    const response = await api.delete(`/resumes/${id}`);
    return response.data;
  }
};

export default api;