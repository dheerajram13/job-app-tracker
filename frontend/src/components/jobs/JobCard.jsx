import React, { useState } from 'react';
import { jobService } from '../../services/api';

const JobCard = ({ job, onUpdate }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    title: job.title,
    company: job.company,
    description: job.description || '',
    url: job.url || '',
    status: job.status || 'Applied',
    notes: job.notes || ''
  });

  const getStatusColor = (status) => {
    const colors = {
      Applied: 'bg-yellow-100 text-yellow-800',
      Interview: 'bg-blue-100 text-blue-800',
      Offer: 'bg-green-100 text-green-800',
      Rejected: 'bg-red-100 text-red-800',
      Bookmarked: 'bg-purple-100 text-purple-800',
      default: 'bg-gray-100 text-gray-800'
    };
    return colors[status] || colors.default;
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await jobService.updateJob(job.id, formData);
      setIsEditing(false);
      if (onUpdate) onUpdate();
    } catch (error) {
      console.error('Error updating job:', error);
    }
  };

  const handleStatusChange = async (newStatus) => {
    try {
      await jobService.updateJob(job.id, { status: newStatus });
      if (onUpdate) onUpdate();
    } catch (error) {
      console.error('Error updating job status:', error);
    }
  };

  const handleDelete = async () => {
    if (window.confirm('Are you sure you want to delete this job application?')) {
      try {
        await jobService.deleteJob(job.id);
        if (onUpdate) onUpdate();
      } catch (error) {
        console.error('Error deleting job:', error);
      }
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6 mb-4">
      {!isEditing ? (
        <>
          <div className="flex justify-between items-start">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">{job.title}</h3>
              <p className="text-gray-600">{job.company}</p>
            </div>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(job.status)}`}>
              {job.status}
            </span>
          </div>
          
          <div className="mt-2">
            {job.date_applied && (
              <p className="text-sm text-gray-500">
                Applied on: {new Date(job.date_applied).toLocaleDateString()}
              </p>
            )}
          </div>
          
          {isExpanded && (
            <div className="mt-4 border-t pt-4">
              {job.description && (
                <div className="mb-4">
                  <h4 className="text-sm font-medium text-gray-700">Description</h4>
                  <p className="text-sm text-gray-600 mt-1">{job.description}</p>
                </div>
              )}
              
              {job.notes && (
                <div className="mb-4">
                  <h4 className="text-sm font-medium text-gray-700">Notes</h4>
                  <p className="text-sm text-gray-600 mt-1 whitespace-pre-line">{job.notes}</p>
                </div>
              )}
              
              <div className="mt-4">
                <h4 className="text-sm font-medium text-gray-700">Update Status</h4>
                <div className="mt-2 flex flex-wrap gap-2">
                  {['Bookmarked', 'Applied', 'Interview', 'Offer', 'Rejected'].map(status => (
                    <button
                      key={status}
                      onClick={() => handleStatusChange(status)}
                      className={`px-3 py-1 rounded-full text-xs font-medium ${
                        job.status === status 
                          ? getStatusColor(status) + ' ring-2 ring-offset-2 ring-gray-300' 
                          : 'bg-gray-200 text-gray-800 hover:bg-gray-300'
                      }`}
                    >
                      {status}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}
          
          <div className="mt-4 flex space-x-4">
            <button 
              onClick={() => setIsEditing(true)}
              className="text-indigo-600 hover:text-indigo-900 text-sm font-medium"
            >
              Edit
            </button>
            <button 
              onClick={() => setIsExpanded(!isExpanded)}
              className="text-gray-600 hover:text-gray-900 text-sm font-medium"
            >
              {isExpanded ? 'Hide Details' : 'View Details'}
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
            <button 
              onClick={handleDelete}
              className="text-red-600 hover:text-red-900 text-sm font-medium ml-auto"
            >
              Delete
            </button>
          </div>
        </>
      ) : (
        <form onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label htmlFor="title" className="block text-sm font-medium text-gray-700">
                Job Title
              </label>
              <input
                type="text"
                name="title"
                id="title"
                required
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                value={formData.title}
                onChange={handleChange}
              />
            </div>

            <div>
              <label htmlFor="company" className="block text-sm font-medium text-gray-700">
                Company
              </label>
              <input
                type="text"
                name="company"
                id="company"
                required
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                value={formData.company}
                onChange={handleChange}
              />
            </div>

            <div>
              <label htmlFor="description" className="block text-sm font-medium text-gray-700">
                Description
              </label>
              <textarea
                name="description"
                id="description"
                rows="3"
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                value={formData.description}
                onChange={handleChange}
              />
            </div>

            <div>
              <label htmlFor="url" className="block text-sm font-medium text-gray-700">
                Job Posting URL
              </label>
              <input
                type="url"
                name="url"
                id="url"
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                value={formData.url}
                onChange={handleChange}
              />
            </div>

            <div>
              <label htmlFor="status" className="block text-sm font-medium text-gray-700">
                Status
              </label>
              <select
                name="status"
                id="status"
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                value={formData.status}
                onChange={handleChange}
              >
                <option value="Bookmarked">Bookmarked</option>
                <option value="Applied">Applied</option>
                <option value="Interview">Interview</option>
                <option value="Offer">Offer</option>
                <option value="Rejected">Rejected</option>
              </select>
            </div>

            <div>
              <label htmlFor="notes" className="block text-sm font-medium text-gray-700">
                Notes
              </label>
              <textarea
                name="notes"
                id="notes"
                rows="3"
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                value={formData.notes}
                onChange={handleChange}
              />
            </div>

            <div className="flex justify-end space-x-3">
              <button
                type="button"
                onClick={() => setIsEditing(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md hover:bg-indigo-700"
              >
                Save
              </button>
            </div>
          </div>
        </form>
      )}
    </div>
  );
};

export default JobCard;
// import React, { useState } from 'react';
// import JobModal from './JobModal';

// const JobCard = ({ job, onStatusChange, onDelete }) => {
//   const [showModal, setShowModal] = useState(false);

//   const getStatusColor = (status) => {
//     const colors = {
//       Applied: 'bg-yellow-100 text-yellow-800',
//       Interview: 'bg-blue-100 text-blue-800',
//       Offer: 'bg-green-100 text-green-800',
//       Rejected: 'bg-red-100 text-red-800',
//       'Phone Screen': 'bg-purple-100 text-purple-800',
//       'Technical Interview': 'bg-indigo-100 text-indigo-800',
//       'On-site': 'bg-teal-100 text-teal-800',
//       default: 'bg-gray-100 text-gray-800'
//     };
//     return colors[status] || colors.default;
//   };

//   const formatDate = (dateString) => {
//     try {
//       return new Date(dateString).toLocaleDateString();
//     } catch (error) {
//       console.error('Error formatting date:', error);
//       return 'Invalid date';
//     }
//   };

//   const handleSave = async (updatedJob) => {
//     await onStatusChange(job.id, updatedJob.status);
//     setShowModal(false);
//   };

//   const handleDelete = async () => {
//     await onDelete(job.id);
//     setShowModal(false);
//   };

//   return (
//     <>
//       <div className="bg-white rounded-lg shadow p-6">
//         <div className="flex justify-between items-start">
//           <div>
//             <h3 className="text-lg font-semibold text-gray-900">{job.title}</h3>
//             <p className="text-gray-600">{job.company}</p>
//           </div>
//           <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(job.status)}`}>
//             {job.status}
//           </span>
//         </div>
        
//         <div className="mt-4">
//           <p className="text-sm text-gray-500">Applied on: {formatDate(job.date_applied)}</p>
//         </div>
        
//         {job.description && (
//           <div className="mt-2">
//             <p className="text-sm text-gray-600 line-clamp-2">{job.description}</p>
//           </div>
//         )}
        
//         <div className="mt-4 flex space-x-4">
//           <button 
//             onClick={() => setShowModal(true)}
//             className="text-gray-600 hover:text-gray-900 text-sm font-medium"
//           >
//             View Details
//           </button>
//           {job.url && (
//             <a 
//               href={job.url} 
//               target="_blank" 
//               rel="noopener noreferrer"
//               className="text-gray-600 hover:text-gray-900 text-sm font-medium"
//             >
//               View Posting
//             </a>
//           )}
//         </div>
//       </div>

//       <JobModal
//         job={job}
//         isOpen={showModal}
//         onClose={() => setShowModal(false)}
//         onSave={handleSave}
//         onDelete={handleDelete}
//       />
//     </>
//   );
// };

// export default JobCard;