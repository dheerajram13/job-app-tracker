import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const jobService = {
  getAllJobs: async () => {
    const response = await api.get('/jobs/');
    return response.data;
  },

  createJob: async (jobData) => {
    const response = await api.post('/jobs/', jobData);
    return response.data;
  },

  updateJob: async (id, jobData) => {
    const response = await api.put(`/jobs/${id}`, jobData);
    return response.data;
  },

  deleteJob: async (id) => {
    const response = await api.delete(`/jobs/${id}`);
    return response.data;
  },

  parseJobUrl: async (url) => {
    const response = await api.post('/jobs/parse-url', { url });
    return response.data;
  }
};

export default api;