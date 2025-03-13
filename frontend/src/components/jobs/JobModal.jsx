import React, { useState, useEffect } from 'react';
import { X } from 'lucide-react';
import { useAuth0 } from '@auth0/auth0-react';
import { jobService } from '../../services/api';

const JobModal = ({ job, isOpen, onClose, onSave, onDelete, mode = 'view' }) => {
  const [formData, setFormData] = useState(job || {});
  const [isEditing, setIsEditing] = useState(mode === 'edit');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { getAccessTokenSilently } = useAuth0();

  useEffect(() => {
    setFormData(job || {});
    setIsEditing(mode === 'edit');
  }, [job, mode]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const token = await getAccessTokenSilently();
      await jobService.updateJob(token, job.id, formData);
      onSave(formData);
      onClose();
    } catch (error) {
      console.error('Error updating job:', error);
      alert('Failed to update job');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (window.confirm('Are you sure you want to delete this job application?')) {
      setIsSubmitting(true);
      try {
        const token = await getAccessTokenSilently();
        await jobService.deleteJob(token, job.id);
        onDelete(job.id);
        onClose();
      } catch (error) {
        console.error('Error deleting job:', error);
        alert('Failed to delete job');
      } finally {
        setIsSubmitting(false);
      }
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold">
              {isEditing ? 'Edit Job Application' : 'View Job Application'}
            </h2>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700"
              disabled={isSubmitting}
            >
              <X size={24} />
            </button>
          </div>

          <form onSubmit={handleSubmit}>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Job Title
                </label>
                {isEditing ? (
                  <input
                    type="text"
                    name="title"
                    value={formData.title || ''}
                    onChange={handleChange}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                    required
                    disabled={isSubmitting}
                  />
                ) : (
                  <p className="mt-1 text-gray-900">{formData.title}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Company
                </label>
                {isEditing ? (
                  <input
                    type="text"
                    name="company"
                    value={formData.company || ''}
                    onChange={handleChange}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                    required
                    disabled={isSubmitting}
                  />
                ) : (
                  <p className="mt-1 text-gray-900">{formData.company}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Status
                </label>
                {isEditing ? (
                  <select
                    name="status"
                    value={formData.status || 'Applied'}
                    onChange={handleChange}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                    disabled={isSubmitting}
                  >
                    <option value="Applied">Applied</option>
                    <option value="Phone Screen">Phone Screen</option>
                    <option value="Technical Interview">Technical Interview</option>
                    <option value="On-site">On-site</option>
                    <option value="Offer">Offer</option>
                    <option value="Rejected">Rejected</option>
                  </select>
                ) : (
                  <p className="mt-1 text-gray-900">{formData.status}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Job Posting URL
                </label>
                {isEditing ? (
                  <input
                    type="url"
                    name="url"
                    value={formData.url || ''}
                    onChange={handleChange}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                    disabled={isSubmitting}
                  />
                ) : (
                  <a
                    href={formData.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="mt-1 text-indigo-600 hover:text-indigo-800"
                  >
                    {formData.url}
                  </a>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Description
                </label>
                {isEditing ? (
                  <textarea
                    name="description"
                    value={formData.description || ''}
                    onChange={handleChange}
                    rows="4"
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                    disabled={isSubmitting}
                  />
                ) : (
                  <p className="mt-1 text-gray-900 whitespace-pre-wrap">
                    {formData.description}
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Notes
                </label>
                {isEditing ? (
                  <textarea
                    name="notes"
                    value={formData.notes || ''}
                    onChange={handleChange}
                    rows="4"
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                    disabled={isSubmitting}
                  />
                ) : (
                  <p className="mt-1 text-gray-900 whitespace-pre-wrap">
                    {formData.notes}
                  </p>
                )}
              </div>
            </div>

            <div className="mt-6 flex justify-end space-x-3">
              {!isEditing && (
                <button
                  type="button"
                  onClick={() => setIsEditing(true)}
                  className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-md"
                  disabled={isSubmitting}
                >
                  Edit
                </button>
              )}
              {isEditing && (
                <>
                  <button
                    type="button"
                    onClick={() => setIsEditing(false)}
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                    disabled={isSubmitting}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-md"
                    disabled={isSubmitting}
                  >
                    {isSubmitting ? 'Saving...' : 'Save Changes'}
                  </button>
                </>
              )}
              <button
                type="button"
                onClick={handleDelete}
                className="px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-md"
                disabled={isSubmitting}
              >
                {isSubmitting ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default JobModal;