import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const jobService = {
  getAllJobs: async (token, filters = {}) => {
    const { status = 'all', search = '', sortBy = 'dateApplied' } = filters;
    const response = await api.get('/jobs/', {
      headers: { Authorization: `Bearer ${token}` },
      params: { status, search, sortBy }
    });
    return response.data;
  },

  createJob: async (token, jobData) => {
    const response = await api.post('/jobs/', jobData, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  },

  updateJob: async (token, jobId, updates) => {
    const response = await api.put(`/jobs/${jobId}`, updates, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  },

  deleteJob: async (token, jobId) => {
    const response = await api.delete(`/jobs/${jobId}`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  },

  parseJobUrl: async (token, url) => {
    const response = await api.post('/jobs/parse-url', { url }, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  }
};

export default api;