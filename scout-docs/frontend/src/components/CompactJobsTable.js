import React from 'react';
import { 
  CheckCircleIcon, 
  XCircleIcon, 
  ArrowPathIcon,
  ClockIcon,
  DocumentIcon,
  GlobeAltIcon,
  PlayIcon,
  ChevronRightIcon,
  CpuChipIcon,
  RocketLaunchIcon
} from '@heroicons/react/24/outline';

const CompactJobsTable = ({ jobs, selectedJob, onSelectJob }) => {
  const jobsArray = Object.values(jobs)
    .sort((a, b) => new Date(b.start_time) - new Date(a.start_time))
    .slice(0, 10); // Show only the 10 most recent jobs

  const getPipelineDisplayName = (pipelineId) => {
    const pipelineNames = {
      'fast_text': 'Fast Text',
      'balanced': 'Balanced',
      'ocr_only': 'OCR Focused',
      'table_focused': 'Table Focused',
      'full_extraction': 'Full Extraction',
      'standard': 'Standard',
      'vlm': 'VLM (Vision)'
    };
    return pipelineNames[pipelineId] || pipelineId;
  };

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


  const formatTime = (timeString) => {
    if (!timeString) return '';
    const date = new Date(timeString);
    const now = new Date();
    const diffMinutes = Math.floor((now - date) / 60000);
    
    if (diffMinutes < 1) return '';
    if (diffMinutes < 60) return `${diffMinutes}m ago`;
    if (diffMinutes < 1440) return `${Math.floor(diffMinutes / 60)}h ago`;
    return date.toLocaleDateString();
  };

  const formatDuration = (seconds) => {
    if (!seconds) return '';
    return seconds < 1 ? `${Math.round(seconds * 1000)}ms` : `${seconds.toFixed(1)}s`;
  };

  const truncateText = (text, maxLength = 40) => {
    if (!text) return '';
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
  };

  if (jobsArray.length === 0) {
    return (
      <div className="executive-card">
        <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
          <h3 className="text-lg font-semibold text-gray-900">Processing Jobs Overview</h3>
          <p className="text-sm text-gray-600 mt-1">Monitor and manage your document processing tasks</p>
        </div>
        <div className="p-16 text-center">
          <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-blue-100 mb-6">
            <DocumentIcon className="h-8 w-8 text-blue-600" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Ready to Process Documents</h3>
          <p className="text-gray-500 max-w-md mx-auto">Upload a file or enter a URL below to start your first document processing job and see the results here.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="executive-card">
      <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Processing Jobs Overview</h3>
            <p className="text-sm text-gray-600 mt-1">Monitor and manage your document processing tasks</p>
          </div>
          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
            {jobsArray.length} of {Object.keys(jobs).length} jobs
          </span>
        </div>
      </div>

      <div className="overflow-hidden">
        <table className="executive-table">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Document
              </th>
              <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Compute / Pipeline
              </th>
              <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Performance
              </th>
              <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Throughput
              </th>
              <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Started / Action
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {jobsArray.map((job) => (
              <tr 
                key={job.job_id}
                className={`hover:bg-gray-50 transition-colors cursor-pointer ${
                  selectedJob === job.job_id ? 'bg-blue-50 ring-2 ring-blue-500 ring-inset' : ''
                }`}
                onClick={() => onSelectJob(job.job_id)}
              >
                {/* Compact Single Row with All Info */}
                <td className="px-4 py-2">
                  <div className="flex items-center space-x-3">
                    {/* Icon */}
                    <div className="flex-shrink-0">
                      {job.filename ? (
                        <DocumentIcon className="h-4 w-4 text-gray-400" />
                      ) : (
                        <GlobeAltIcon className="h-4 w-4 text-gray-400" />
                      )}
                    </div>
                    
                    {/* Document Name */}
                    <div className="min-w-0 flex-1">
                      <div className="text-sm font-medium text-gray-900 truncate">
                        {job.filename || truncateText(job.source, 50) || 'Processing...'}
                      </div>
                      <div className="text-xs text-gray-500">
                        {job.status === 'processing' ? 'Processing...' : ''}
                      </div>
                    </div>
                  </div>
                </td>

                {/* Status & Progress Combined */}
                <td className="px-4 py-2">
                  <div className="flex items-center space-x-2">
                    {getStatusIcon(job.status)}
                    {job.status === 'processing' && job.progress > 0 && (
                      <span className="text-xs text-blue-600 font-medium">
                        {job.progress}%
                      </span>
                    )}
                  </div>
                </td>

                {/* Compute Type & Pipeline */}
                <td className="px-4 py-2">
                  <div className="flex items-center space-x-2">
                    <span 
                      className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
                        job.result?.metrics?.compute_type === 'GPU' 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-blue-100 text-blue-800'
                      }`}
                      title={job.result?.metrics?.compute_details || job.compute_mode || 'Processing unit information'}
                    >
                      {job.result?.metrics?.compute_type === 'GPU' ? (
                        <>
                          <RocketLaunchIcon className="h-3 w-3 mr-1" />
                          GPU
                        </>
                      ) : job.result?.metrics?.compute_type === 'CPU' ? (
                        <>
                          <CpuChipIcon className="h-3 w-3 mr-1" />
                          CPU
                        </>
                      ) : (
                        <>
                          <CpuChipIcon className="h-3 w-3 mr-1" />
                          {job.compute_mode?.toUpperCase() || 'CPU'}
                        </>
                      )}
                    </span>
                    <span className="text-xs text-gray-600">
                      • {getPipelineDisplayName(job.pipeline) || 'Processing...'}
                    </span>
                  </div>
                </td>

                {/* Performance */}
                <td className="px-4 py-2 text-xs text-gray-600">
                  {job.result?.metrics ? (
                    <div className="font-medium text-blue-600">
                      {formatDuration(job.result.metrics.total_time)} • {job.result.metrics.document_pages} page{job.result.metrics.document_pages !== 1 ? 's' : ''} • {job.result.metrics.words_processed >= 1000 ? `${Math.round(job.result.metrics.words_processed / 1000)}K` : job.result.metrics.words_processed} words
                    </div>
                  ) : job.duration ? (
                    <div className="font-medium text-blue-600">{formatDuration(job.duration)}</div>
                  ) : (
                    <div className="text-gray-400">Processing...</div>
                  )}
                </td>

                {/* Throughput */}
                <td className="px-4 py-2 text-xs text-gray-600">
                  {job.result?.metrics ? (
                    <div className="font-medium text-green-600">
                      {(job.result.metrics.document_pages / job.result.metrics.total_time).toFixed(1)} pages/s{job.result.metrics.document_size_bytes ? ` • ${((job.result.metrics.document_size_bytes / (1024 * 1024)) / job.result.metrics.total_time).toFixed(1)} MB/s` : ''}
                    </div>
                  ) : (
                    <div className="text-gray-400">—</div>
                  )}
                </td>

                {/* Time & Action Combined */}
                <td className="px-4 py-2 text-right">
                  <div className="flex items-center justify-end space-x-3">
                    <span className="text-xs text-gray-500">{formatTime(job.start_time)}</span>
                    <button 
                      className={`text-xs px-2 py-1 rounded ${
                        selectedJob === job.job_id 
                          ? 'bg-blue-100 text-blue-800 font-medium' 
                          : 'text-blue-600 hover:text-blue-900 hover:bg-blue-50'
                      }`}
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectJob(job.job_id);
                      }}
                    >
                      {selectedJob === job.job_id ? 'Selected' : 'View'}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {Object.keys(jobs).length > 10 && (
        <div className="px-6 py-3 bg-gray-50 text-center border-t">
          <span className="text-sm text-gray-500">
            Showing 10 most recent jobs of {Object.keys(jobs).length} total
          </span>
        </div>
      )}
    </div>
  );
};

export default CompactJobsTable;