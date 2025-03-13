import React, { useState, useEffect } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import { Search, Filter, Plus } from 'lucide-react';
import JobCard from '../../components/jobs/JobCard';
import JobForm from '../../components/jobs/JobForm';
import { jobService } from '../../services/api';

const Dashboard = () => {
  const [jobs, setJobs] = useState([]);
  const [showJobForm, setShowJobForm] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [filters, setFilters] = useState({
    status: 'all',
    search: '',
    sortBy: 'dateApplied'
  });

  const { getAccessTokenSilently } = useAuth0();

  useEffect(() => {
    fetchJobs();
  }, [filters]);

  const fetchJobs = async () => {
    try {
      setIsLoading(true);
      const token = await getAccessTokenSilently();
      const data = await jobService.getAllJobs(token, filters);
      setJobs(data);
    } catch (error) {
      console.error('Error fetching jobs:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleJobSubmit = async (jobData, token) => {
    try {
      await jobService.createJob(token, jobData);
      setShowJobForm(false);
      fetchJobs();
    } catch (error) {
      console.error('Error creating job:', error);
    }
  };

  const handleStatusChange = async (jobId, newStatus) => {
    try {
      const token = await getAccessTokenSilently();
      await jobService.updateJob(token, jobId, { status: newStatus });
      fetchJobs();
    } catch (error) {
      console.error('Error updating job status:', error);
    }
  };

  const handleDeleteJob = async (jobId) => {
    if (window.confirm('Are you sure you want to delete this job application?')) {
      try {
        const token = await getAccessTokenSilently();
        await jobService.deleteJob(token, jobId);
        fetchJobs();
      } catch (error) {
        console.error('Error deleting job:', error);
      }
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header Section */}
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Job Applications</h1>
        <button
          onClick={() => setShowJobForm(true)}
          className="flex items-center px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
        >
          <Plus className="w-4 h-4 mr-2" />
          Add New Job
        </button>
      </div>

      {/* Filters Section */}
      <div className="mb-6 flex flex-wrap gap-4">
        <div className="flex-1 min-w-[200px]">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder="Search jobs..."
              className="pl-10 w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
              value={filters.search}
              onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
            />
          </div>
        </div>
        <div className="flex gap-4">
          <select
            value={filters.status}
            onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
            className="rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
          >
            <option value="all">All Status</option>
            <option value="Applied">Applied</option>
            <option value="Phone Screen">Phone Screen</option>
            <option value="Technical Interview">Technical Interview</option>
            <option value="On-site">On-site</option>
            <option value="Offer">Offer</option>
            <option value="Rejected">Rejected</option>
          </select>
          <select
            value={filters.sortBy}
            onChange={(e) => setFilters(prev => ({ ...prev, sortBy: e.target.value }))}
            className="rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
          >
            <option value="dateApplied">Sort by Date Applied</option>
            <option value="company">Sort by Company</option>
            <option value="status">Sort by Status</option>
          </select>
        </div>
      </div>

      {/* Job Form Modal */}
      {showJobForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg w-full max-w-2xl mx-4">
            <JobForm
              onSubmit={handleJobSubmit}
              onClose={() => setShowJobForm(false)}
            />
          </div>
        </div>
      )}

      {/* Jobs Grid */}
{isLoading ? (
  <div className="text-center py-8">Loading...</div>
) : jobs.length === 0 ? (
  <div className="text-center py-8 text-gray-500">
    <p>No job applications found.</p>
    <p className="mt-2">Start by clicking "Add New Job" to track your first application!</p>
  </div>
) : (
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    {jobs.map(job => (
      <JobCard
        key={job.id}
        job={job}
        onStatusChange={handleStatusChange}
        onDelete={handleDeleteJob}
      />
    ))}
  </div>
)}
    </div>
  );
};

export default Dashboard;