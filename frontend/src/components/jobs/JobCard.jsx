import React, { useState } from 'react';
import JobModal from './JobModal';

const JobCard = ({ job, onStatusChange, onDelete }) => {
  const [showModal, setShowModal] = useState(false);

  const getStatusColor = (status) => {
    const colors = {
      Applied: 'bg-yellow-100 text-yellow-800',
      Interview: 'bg-blue-100 text-blue-800',
      Offer: 'bg-green-100 text-green-800',
      Rejected: 'bg-red-100 text-red-800',
      'Phone Screen': 'bg-purple-100 text-purple-800',
      'Technical Interview': 'bg-indigo-100 text-indigo-800',
      'On-site': 'bg-teal-100 text-teal-800',
      default: 'bg-gray-100 text-gray-800'
    };
    return colors[status] || colors.default;
  };

  const formatDate = (dateString) => {
    try {
      return new Date(dateString).toLocaleDateString();
    } catch (error) {
      console.error('Error formatting date:', error);
      return 'Invalid date';
    }
  };

  const handleSave = async (updatedJob) => {
    await onStatusChange(job.id, updatedJob.status);
    setShowModal(false);
  };

  const handleDelete = async () => {
    await onDelete(job.id);
    setShowModal(false);
  };

  return (
    <>
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-start">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">{job.title}</h3>
            <p className="text-gray-600">{job.company}</p>
          </div>
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(job.status)}`}>
            {job.status}
          </span>
        </div>
        
        <div className="mt-4">
          <p className="text-sm text-gray-500">Applied on: {formatDate(job.date_applied)}</p>
        </div>
        
        {job.description && (
          <div className="mt-2">
            <p className="text-sm text-gray-600 line-clamp-2">{job.description}</p>
          </div>
        )}
        
        <div className="mt-4 flex space-x-4">
          <button 
            onClick={() => setShowModal(true)}
            className="text-gray-600 hover:text-gray-900 text-sm font-medium"
          >
            View Details
          </button>
          {job.url && (
            <a 
              href={job.url} 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-gray-600 hover:text-gray-900 text-sm font-medium"
            >
              View Posting
            </a>
          )}
        </div>
      </div>

      <JobModal
        job={job}
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        onSave={handleSave}
        onDelete={handleDelete}
      />
    </>
  );
};

export default JobCard;