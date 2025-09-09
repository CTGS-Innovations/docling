import React from 'react';
import { 
  ClockIcon, 
  CheckCircleIcon, 
  XCircleIcon, 
  ArrowPathIcon,
  DocumentIcon,
  GlobeAltIcon
} from '@heroicons/react/24/outline';

const JobsList = ({ jobs, selectedJob, onSelectJob }) => {
  const jobsArray = Object.values(jobs).sort((a, b) => 
    new Date(b.start_time) - new Date(a.start_time)
  );

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="h-4 w-4 text-green-500" />;
      case 'failed':
        return <XCircleIcon className="h-4 w-4 text-red-500" />;
      case 'processing':
        return <ArrowPathIcon className="h-4 w-4 text-blue-500 animate-spin" />;
      default:
        return <ClockIcon className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'failed':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'processing':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const formatTime = (timeString) => {
    if (!timeString) return '';
    const date = new Date(timeString);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const formatDuration = (seconds) => {
    if (!seconds) return '';
    return seconds < 1 ? `${Math.round(seconds * 1000)}ms` : `${seconds.toFixed(1)}s`;
  };

  const truncateText = (text, maxLength = 30) => {
    if (!text) return '';
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
  };

  if (jobsArray.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6 text-center">
        <ClockIcon className="h-8 w-8 text-gray-400 mx-auto mb-2" />
        <h3 className="text-sm font-medium text-gray-900 mb-1">No Jobs Yet</h3>
        <p className="text-xs text-gray-500">
          Upload a file or process a URL to see jobs here
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-4 border-b">
        <h3 className="text-lg font-medium text-gray-900">Processing Jobs</h3>
        <p className="text-sm text-gray-500">{jobsArray.length} total jobs</p>
      </div>

      <div className="divide-y divide-gray-200 max-h-96 overflow-y-auto">
        {jobsArray.map((job) => (
          <button
            key={job.job_id}
            onClick={() => onSelectJob(job.job_id)}
            className={`w-full text-left p-4 hover:bg-gray-50 transition-colors ${
              selectedJob === job.job_id ? 'bg-blue-50 border-l-4 border-blue-500' : ''
            }`}
          >
            <div className="flex items-start justify-between">
              <div className="flex items-start space-x-3 flex-1 min-w-0">
                {/* Source Icon */}
                <div className="flex-shrink-0 mt-0.5">
                  {job.filename ? (
                    <DocumentIcon className="h-4 w-4 text-gray-400" />
                  ) : (
                    <GlobeAltIcon className="h-4 w-4 text-gray-400" />
                  )}
                </div>

                {/* Job Details */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2 mb-1">
                    {getStatusIcon(job.status)}
                    <span className="text-sm font-medium text-gray-900 truncate">
                      {truncateText(job.filename || job.source)}
                    </span>
                  </div>

                  <div className="flex items-center justify-between mb-2">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${getStatusColor(job.status)}`}>
                      {job.status}
                    </span>
                    {job.duration && (
                      <span className="text-xs text-gray-500">
                        {formatDuration(job.duration)}
                      </span>
                    )}
                  </div>

                  {/* Progress Bar */}
                  {job.status === 'processing' && (
                    <div className="w-full bg-gray-200 rounded-full h-1.5 mb-2">
                      <div
                        className="bg-blue-600 h-1.5 rounded-full transition-all duration-300"
                        style={{ width: `${job.progress || 0}%` }}
                      ></div>
                    </div>
                  )}

                  {/* Job Metadata */}
                  <div className="flex items-center justify-between text-xs text-gray-500">
                    <span>
                      {job.pipeline} • {job.output_format}
                    </span>
                    <span>
                      {formatTime(job.start_time)}
                    </span>
                  </div>

                  {/* Performance Preview */}
                  {job.result?.metrics && job.status === 'completed' && (
                    <div className="mt-2 flex items-center space-x-3 text-xs text-gray-500">
                      <span>{job.result.metrics.document_pages} pages</span>
                      <span>{Math.round(job.result.metrics.words_processed / job.result.metrics.total_time)} words/s</span>
                      <span>{job.result.metrics.words_processed.toLocaleString()} words</span>
                    </div>
                  )}

                  {/* Error Preview */}
                  {job.status === 'failed' && job.result?.error_message && (
                    <div className="mt-2 text-xs text-red-600 truncate">
                      {truncateText(job.result.error_message, 50)}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
};

export default JobsList;