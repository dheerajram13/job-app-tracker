import React, { useState, useEffect } from 'react';
import Navbar from './components/layout/Navbar';
import JobCard from './components/jobs/JobCard';
import JobForm from './components/jobs/JobForm';
import { jobService } from './services/api';

function App() {
  const [jobs, setJobs] = useState([]);
  const [showJobForm, setShowJobForm] = useState(false);

  useEffect(() => {
    fetchJobs();
  }, []);

  const fetchJobs = async () => {
    try {
      const data = await jobService.getAllJobs();
      setJobs(data);
    } catch (error) {
      console.error('Error fetching jobs:', error);
    }
  };

  const handleJobSubmit = async (jobData) => {
    try {
      await jobService.createJob(jobData);
      setShowJobForm(false);
      fetchJobs();
    } catch (error) {
      console.error('Error creating job:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <Navbar />
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-gray-900">Job Applications</h2>
            <button
              onClick={() => setShowJobForm(true)}
              className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700"
            >
              Add New Job
            </button>
          </div>

          {showJobForm && (
            <div className="mb-6">
              <JobForm
                onSubmit={handleJobSubmit}
                onClose={() => setShowJobForm(false)}
              />
            </div>
          )}

          <div className="space-y-4">
            {jobs.map(job => (
              <JobCard key={job.id} job={job} />
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;