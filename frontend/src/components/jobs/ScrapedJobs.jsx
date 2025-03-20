// src/components/jobs/ScrapedJobs.jsx
import React, { useState, useEffect } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import { Search, Filter, ExternalLink, CheckCircle } from 'lucide-react';
import axios from 'axios';

// Update your API service with these new methods
const API_URL = 'http://localhost:8000/api';

const getScrapedJobs = async (token, filters = {}) => {
  const { searchQuery, minRelevance, skills, applied, limit = 50, offset = 0 } = filters;
  
  const response = await axios.get(`${API_URL}/jobs/scraped`, {
    headers: { Authorization: `Bearer ${token}` },
    params: { 
      search_query: searchQuery, 
      min_relevance: minRelevance,
      skills,
      applied,
      limit,
      offset
    }
  });
  return response.data;
};

const markJobApplied = async (token, jobId) => {
  const response = await axios.post(`${API_URL}/jobs/scraped/${jobId}/apply`, {}, {
    headers: { Authorization: `Bearer ${token}` }
  });
  return response.data;
};

const triggerJobScraping = async (token, searchTerms, location = 'Australia') => {
  const response = await axios.post(`${API_URL}/jobs/scrape`, 
    { 
      search_terms: searchTerms,
      location
    }, 
    {
      headers: { Authorization: `Bearer ${token}` }
    }
  );
  return response.data;
};

const ScrapedJobs = () => {
  const [jobs, setJobs] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSearching, setIsSearching] = useState(false);
  const [totalJobs, setTotalJobs] = useState(0);
  const [topSkills, setTopSkills] = useState([]);
  const [selectedSkills, setSelectedSkills] = useState([]);
  const [filters, setFilters] = useState({
    searchQuery: '',
    minRelevance: 0,
    skills: '',
    applied: null,
    limit: 50,
    offset: 0
  });

  const { getAccessTokenSilently } = useAuth0();

  // Fetch top skills
  useEffect(() => {
    const fetchTopSkills = async () => {
      try {
        const token = await getAccessTokenSilently();
        const response = await axios.get(`${API_URL}/jobs/top-skills`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setTopSkills(response.data.skills || []);
      } catch (error) {
        console.error('Error fetching top skills:', error);
      }
    };

    fetchTopSkills();
  }, [getAccessTokenSilently]);

  // Fetch jobs when filters change
  useEffect(() => {
    fetchJobs();
  }, [filters]);

  const fetchJobs = async () => {
    try {
      setIsLoading(true);
      const token = await getAccessTokenSilently();
      
      const data = await getScrapedJobs(token, filters);
      setJobs(data.jobs || []);
      setTotalJobs(data.total || 0);
    } catch (error) {
      console.error('Error fetching scraped jobs:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleApply = async (jobId) => {
    try {
      const token = await getAccessTokenSilently();
      await markJobApplied(token, jobId);
      
      // Update the local state
      setJobs(prevJobs => 
        prevJobs.map(job => 
          job.id === jobId ? { ...job, applied: true, status: 'Applied' } : job
        )
      );
    } catch (error) {
      console.error('Error marking job as applied:', error);
    }
  };

  const handleSearch = async () => {
    try {
      setIsSearching(true);
      const token = await getAccessTokenSilently();
      
      // Default search terms if none provided
      const searchTerms = [
        "Software Engineer",
        "Full Stack Developer", 
        "Machine Learning Engineer", 
        "Data Scientist"
      ];
      
      await triggerJobScraping(token, searchTerms);
      
      // Show notification
      alert("Job search started! New results will appear shortly.");
      
      // Reload after a delay to show new results
      setTimeout(() => {
        fetchJobs();
        setIsSearching(false);
      }, 5000);
    } catch (error) {
      console.error('Error triggering job search:', error);
      setIsSearching(false);
    }
  };

  const toggleSkill = (skill) => {
    if (selectedSkills.includes(skill)) {
      setSelectedSkills(selectedSkills.filter(s => s !== skill));
    } else {
      setSelectedSkills([...selectedSkills, skill]);
    }
    
    // Update filter
    const updatedSkills = selectedSkills.includes(skill) 
      ? selectedSkills.filter(s => s !== skill) 
      : [...selectedSkills, skill];
      
    setFilters(prev => ({
      ...prev,
      skills: updatedSkills.join(',')
    }));
  };

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header Section */}
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Recommended Jobs</h1>
        <button
          onClick={handleSearch}
          disabled={isSearching}
          className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50"
        >
          {isSearching ? 'Searching...' : 'Find New Jobs'}
        </button>
      </div>

      {/* Filters Section */}
      <div className="mb-6 bg-white p-4 rounded-lg shadow">
        <div className="flex flex-wrap gap-4 mb-4">
          <div className="flex-1 min-w-[200px]">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="Search by title or company..."
                className="pl-10 w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                value={filters.searchQuery}
                onChange={(e) => setFilters(prev => ({ ...prev, searchQuery: e.target.value }))}
              />
            </div>
          </div>
          
          <select
            value={filters.minRelevance}
            onChange={(e) => setFilters(prev => ({ ...prev, minRelevance: e.target.value }))}
            className="rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
          >
            <option value="0">All Jobs</option>
            <option value="50">Relevance 50+</option>
            <option value="70">Relevance 70+</option>
            <option value="90">Relevance 90+</option>
          </select>
          
          <select
            value={filters.applied === null ? '' : filters.applied.toString()}
            onChange={(e) => {
              const value = e.target.value;
              setFilters(prev => ({ 
                ...prev, 
                applied: value === '' ? null : value === 'true'
              }));
            }}
            className="rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
          >
            <option value="">All Application Status</option>
            <option value="true">Applied</option>
            <option value="false">Not Applied</option>
          </select>
        </div>
        
        {/* Skills filter */}
        <div>
          <h3 className="text-sm font-medium text-gray-700 mb-2">Filter by Skills:</h3>
          <div className="flex flex-wrap gap-2">
            {topSkills.slice(0, 12).map((skill) => (
              <button
                key={skill}
                onClick={() => toggleSkill(skill)}
                className={`px-3 py-1 text-xs rounded-full ${
                  selectedSkills.includes(skill)
                    ? 'bg-indigo-100 text-indigo-800 border-indigo-300'
                    : 'bg-gray-100 text-gray-800 border-gray-200'
                } border`}
              >
                {skill}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Jobs Grid */}
      {isLoading ? (
        <div className="text-center py-8">Loading...</div>
      ) : jobs.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <p>No job recommendations found.</p>
          <p className="mt-2">Try adjusting your filters or trigger a new job search.</p>
        </div>
      ) : (
        <div>
          <p className="mb-4 text-gray-600">Found {totalJobs} matching jobs</p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {jobs.map(job => (
              <div key={job.id} className="bg-white rounded-lg shadow p-6">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">{job.title}</h3>
                    <p className="text-gray-600">{job.company}</p>
                  </div>
                  <span className="px-3 py-1 rounded-full text-sm font-medium bg-purple-100 text-purple-800">
                    {Math.round(job.relevance_score)}% Match
                  </span>
                </div>
                
                <div className="mt-4">
                  <p className="text-sm text-gray-500">Location: {job.location}</p>
                  <p className="text-sm text-gray-500">Posted: {job.date_applied}</p>
                </div>
                
                {job.description && (
                  <div className="mt-2">
                    <p className="text-sm text-gray-600 line-clamp-2">{job.description}</p>
                  </div>
                )}
                
                {job.skills && job.skills.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-2">
                    {job.skills.slice(0, 5).map((skill, index) => (
                      <span key={index} className="px-2 py-1 bg-gray-100 text-gray-800 text-xs rounded">
                        {skill}
                      </span>
                    ))}
                    {job.skills.length > 5 && (
                      <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">
                        +{job.skills.length - 5} more
                      </span>
                    )}
                  </div>
                )}
                
                <div className="mt-4 flex justify-between">
                  <a
                    href={job.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-indigo-600 hover:text-indigo-800 text-sm font-medium flex items-center"
                  >
                    <ExternalLink className="w-3 h-3 mr-1" />
                    View Job
                  </a>
                  
                  {job.applied ? (
                    <span className="text-green-600 text-sm font-medium flex items-center">
                      <CheckCircle className="w-3 h-3 mr-1" />
                      Applied
                    </span>
                  ) : (
                    <button
                      onClick={() => handleApply(job.id)}
                      className="text-gray-600 hover:text-gray-900 text-sm font-medium"
                    >
                      Mark as Applied
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
          
          {/* Pagination */}
          {totalJobs > filters.limit && (
            <div className="mt-8 flex justify-center">
              <button
                onClick={() => setFilters(prev => ({ ...prev, offset: Math.max(0, prev.offset - prev.limit) }))}
                disabled={filters.offset === 0}
                className="px-4 py-2 mr-2 border border-gray-300 rounded-md disabled:opacity-50"
              >
                Previous
              </button>
              <button
                onClick={() => setFilters(prev => ({ ...prev, offset: prev.offset + prev.limit }))}
                disabled={filters.offset + filters.limit >= totalJobs}
                className="px-4 py-2 border border-gray-300 rounded-md disabled:opacity-50"
              >
                Next
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ScrapedJobs;