import React, { useState, useEffect } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import { jobService } from '../../services/api';

const ScrapedJobs = () => {
  const { getAccessTokenSilently } = useAuth0();
  const [searchTerm, setSearchTerm] = useState('');
  const [location, setLocation] = useState('Australia');
  const [siteName, setSiteName] = useState('all');
  const [isLoading, setIsLoading] = useState(false);
  const [taskId, setTaskId] = useState(null);
  const [taskStatus, setTaskStatus] = useState(null);
  const [allJobs, setAllJobs] = useState([]);
  const [displayedJobs, setDisplayedJobs] = useState([]);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  
  const JOBS_PER_PAGE = 15;

  // Predefined job roles for quick selection
  const jobRoles = [
    "Software Engineer",
    "AI Engineer", 
    "Data Engineer",
    "Full Stack Developer",
    "Machine Learning Engineer",
    "Data Scientist",
    "Software Engineer Intern",
    "Data Scientist Intern"
  ];

  // Job sites options
  const siteOptions = [
    { value: 'all', label: 'All Job Boards' },
    { value: 'linkedin', label: 'LinkedIn' },
    { value: 'indeed', label: 'Indeed' },
    { value: 'glassdoor', label: 'Glassdoor' },
    { value: 'google', label: 'Google Jobs' }
  ];

  // Check task status periodically
  useEffect(() => {
    if (!taskId || taskStatus?.status === 'completed' || taskStatus?.status === 'failed') {
      // Reset loading state when task is done or doesn't exist
      setIsLoading(false);
      return;
    }

    const intervalId = setInterval(async () => {
      try {
        // Get token before making API call
        const token = await getAccessTokenSilently();
        if (!token) {
          setError('Authentication required');
          setIsLoading(false);
          clearInterval(intervalId);
          return;
        }

        const response = await jobService.getScrapedJobs(taskId, token);
        console.log("Task status poll response:", response);
        setTaskStatus(response);
        
        if (response.status === 'completed') {
          // Check if we have any jobs, even if some sources had errors
          if (response.results && response.results.length > 0) {
            // Sort jobs by date (newest first)
            let sortedJobs = [...response.results];
            sortJobsByDate(sortedJobs);
            
            setAllJobs(sortedJobs);
            // Initialize with first page of jobs
            setDisplayedJobs(sortedJobs.slice(0, JOBS_PER_PAGE));
            setHasMore(sortedJobs.length > JOBS_PER_PAGE);
            setPage(1);
            setIsLoading(false);
            clearInterval(intervalId);
          } else {
            setError("No jobs found. Try a different search term or location.");
            setIsLoading(false);
            clearInterval(intervalId);
          }
        } else if (response.status === 'failed') {
          setError(`Error: ${response.error}`);
          setIsLoading(false);
          clearInterval(intervalId);
        }
      } catch (err) {
        console.error('Error checking task status:', err);
        setError('Error checking task status');
        setIsLoading(false);
        clearInterval(intervalId);
      }
    }, 3000); // Increased interval to 3 seconds to reduce server load

    return () => clearInterval(intervalId);
  }, [taskId, taskStatus]);

  // Function to sort jobs by date (newest first)
  const sortJobsByDate = (jobsArray) => {
    jobsArray.sort((a, b) => {
      // First try to sort by the date_posted field if it exists
      const dateA = getDateValue(a.date_posted);
      const dateB = getDateValue(b.date_posted);
      
      // Compare date values (lower value = more recent)
      return dateA - dateB;
    });
  };

  // Helper function to convert date strings to sortable values
  const getDateValue = (dateStr) => {
    if (!dateStr) return 9999;
    
    const str = dateStr.toLowerCase();
    
    // Common patterns like "3 days ago", "Posted yesterday", etc.
    if (str.includes('just now') || str.includes('today') || str.includes('hours ago')) {
      return 0;  // Most recent
    } else if (str.includes('yesterday')) {
      return 1;
    } else if (str.includes('days ago')) {
      try {
        // Extract the number from "X days ago"
        const matches = str.match(/(\d+)\s*days?\s*ago/);
        return matches ? parseInt(matches[1]) : 5;
      } catch (e) {
        return 5;  // Default to 5 days ago if can't parse
      }
    } else if (str.includes('week')) {
      return 7;  // About a week ago
    } else if (str.includes('month')) {
      return 30;  // About a month ago
    } else {
      return 15;  // Default value for unknown formats
    }
  };

  // Load more jobs
  const loadMoreJobs = () => {
    const nextPage = page + 1;
    const startIdx = (nextPage - 1) * JOBS_PER_PAGE;
    const endIdx = nextPage * JOBS_PER_PAGE;
    
    // Add next page of jobs to displayed jobs
    const newDisplayedJobs = [...displayedJobs, ...allJobs.slice(startIdx, endIdx)];
    setDisplayedJobs(newDisplayedJobs);
    setPage(nextPage);
    setHasMore(endIdx < allJobs.length);
  };

  // Set job role from predefined list
  const handleSelectJobRole = (role) => {
    setSearchTerm(role);
  };

  const handleScrape = async (e) => {
    e.preventDefault();
    
    // Get token first to ensure we're authenticated
    try {
      const token = await getAccessTokenSilently();
      if (!token) {
        setError('Authentication required');
        return;
      }

      // Reset all state
      setError(null);
      setAllJobs([]);
      setDisplayedJobs([]);
      setTaskId(null);
      setTaskStatus(null);
      setPage(1);
      setIsLoading(true);

      // Prepare request parameters to match backend expectations
      const requestParams = {
        search_terms: [searchTerm],  // Convert to array as expected by backend
        location: location || 'Australia',
        num_jobs: 50,
        sites: siteName === 'all' ? undefined : [siteName]  // Send as array if specific site selected
      };
      
      // Only add site_name if a specific board is selected
      if (siteName !== 'all') {
        requestParams.site_name = siteName;
      }

      console.log("Making scrape request with parameters:", requestParams);

      const response = await jobService.scrapeJobs(requestParams, token);
      console.log("Scrape API response:", response);
      setTaskId(response.task_id);
    } catch (err) {
      console.error('Error scraping jobs:', err);
      setError(`Error: ${err.message || 'Failed to start job scraping'}`);
      setIsLoading(false);
    }
  };

  const handleAddJob = async (job) => {
    try {
      await jobService.addScrapedJob(job);
      // Mark as added in both all jobs and displayed jobs arrays
      const updatedAllJobs = allJobs.map(j => 
        j.url === job.url ? { ...j, added: true } : j
      );
      setAllJobs(updatedAllJobs);
      
      const updatedDisplayedJobs = displayedJobs.map(j => 
        j.url === job.url ? { ...j, added: true } : j
      );
      setDisplayedJobs(updatedDisplayedJobs);
    } catch (err) {
      console.error('Error adding job:', err);
      setError(`Error adding job: ${err.message}`);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-semibold mb-4">Find Latest Jobs</h2>
      
      {/* Job Role Quick Select */}
      <div className="mb-4">
        <p className="text-sm font-medium text-gray-700 mb-2">Quick Select Job Role:</p>
        <div className="flex flex-wrap gap-2">
          {jobRoles.map((role, index) => (
            <button
              key={index}
              type="button"
              onClick={() => handleSelectJobRole(role)}
              className={`px-3 py-1 text-xs rounded-full border ${
                searchTerm === role 
                  ? 'bg-indigo-100 text-indigo-800 border-indigo-300' 
                  : 'bg-gray-100 text-gray-800 border-gray-200 hover:bg-gray-200'
              }`}
            >
              {role}
            </button>
          ))}
        </div>
      </div>
      
      <form onSubmit={handleScrape} className="mb-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="searchTerm" className="block text-sm font-medium text-gray-700 mb-1">
              Job Title / Keywords
            </label>
            <input
              type="text"
              id="searchTerm"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="e.g., Software Engineer"
              required
            />
          </div>
          
          <div>
            <label htmlFor="location" className="block text-sm font-medium text-gray-700 mb-1">
              Location
            </label>
            <input
              type="text"
              id="location"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="e.g., Australia, Remote, Sydney"
            />
          </div>
          
          <div>
            <label htmlFor="siteName" className="block text-sm font-medium text-gray-700 mb-1">
              Job Board (Optional)
            </label>
            <select
              id="siteName"
              value={siteName}
              onChange={(e) => setSiteName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            >
              {siteOptions.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        </div>
        
        <button
          type="submit"
          disabled={isLoading}
          className="mt-4 w-full py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
        >
          {isLoading ? 'Searching...' : 'Search Jobs'}
        </button>
      </form>
      
      {error && (
        <div className="mb-4 p-4 border border-red-300 bg-red-50 text-red-800 rounded-md">
          {error}
        </div>
      )}
      
      {isLoading && (
        <div className="flex justify-center items-center p-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
          <span className="ml-2">Searching for jobs...</span>
        </div>
      )}
      
      {taskStatus?.status === 'completed' && displayedJobs.length === 0 && (
        <div className="text-center p-8 text-gray-500">
          No jobs found matching your criteria. Try broadening your search.
        </div>
      )}
      
      {displayedJobs.length > 0 && (
        <div className="mt-4">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-medium">Found {allJobs.length} jobs</h3>
            <p className="text-sm text-gray-500">Showing latest jobs first</p>
          </div>
          
          <div className="space-y-4">
            {displayedJobs.map((job, index) => (
              <div key={index} className="border border-gray-200 rounded-md p-4 hover:bg-gray-50">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">{job.title}</h3>
                    <p className="text-gray-600">{job.company}</p>
                    <p className="text-gray-500 text-sm">{job.location}</p>
                    <p className="text-gray-500 text-sm">Posted: {job.date_posted}</p>
                  </div>
                  <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded uppercase font-semibold">
                    {job.source}
                  </span>
                </div>
                {job.detailed_description && (
                  <div className="mt-2">
                    <p className="text-sm text-gray-600">
                      {job.detailed_description.length > 200 
                        ? `${job.detailed_description.substring(0, 200)}...` 
                        : job.detailed_description}
                    </p>
                    <button 
                      onClick={() => alert(job.detailed_description)}
                      className="text-xs text-indigo-600 hover:text-indigo-800 mt-1"
                    >
                      Read More
                    </button>
                  </div>
                )}
                <div className="mt-4 flex space-x-4">
                  <a 
                    href={job.url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-indigo-600 hover:text-indigo-900 text-sm font-medium"
                  >
                    View Job
                  </a>
                  {!job.added ? (
                    <button
                      onClick={() => handleAddJob(job)}
                      className="text-green-600 hover:text-green-900 text-sm font-medium"
                    >
                      Add to Tracker
                    </button>
                  ) : (
                    <span className="text-green-600 text-sm font-medium">
                      ✓ Added
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
          
          {hasMore && (
            <div className="mt-6 text-center">
              <button
                onClick={loadMoreJobs}
                className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                Load More Jobs
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ScrapedJobs;