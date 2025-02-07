import React from 'react';

const JobCard = ({ job }) => {
  const getStatusColor = (status) => {
    const colors = {
      Applied: 'bg-yellow-100 text-yellow-800',
      Interview: 'bg-blue-100 text-blue-800',
      Offer: 'bg-green-100 text-green-800',
      Rejected: 'bg-red-100 text-red-800',
      default: 'bg-gray-100 text-gray-800'
    };
    return colors[status] || colors.default;
  };

  return (
    <div className="bg-white rounded-lg shadow p-6 mb-4">
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
        <p className="text-sm text-gray-500">Applied on: {new Date(job.dateApplied).toLocaleDateString()}</p>
      </div>
      <div className="mt-4 flex space-x-4">
        <button className="text-indigo-600 hover:text-indigo-900 text-sm font-medium">
          Edit
        </button>
        <button className="text-gray-600 hover:text-gray-900 text-sm font-medium">
          View Details
        </button>
        <a 
          href={job.url} 
          target="_blank" 
          rel="noopener noreferrer"
          className="text-gray-600 hover:text-gray-900 text-sm font-medium"
        >
          View Posting
        </a>
      </div>
    </div>
  );
};

export default JobCard;