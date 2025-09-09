import React, { useState, useEffect } from 'react';
// WebSocket will be handled with native WebSocket API
import axios from 'axios';
import FileUpload from './components/FileUpload';
import URLInput from './components/URLInput';
import ProcessingLog from './components/ProcessingLog';
import ResultsViewer from './components/ResultsViewer';
import JobsList from './components/JobsList';
import { ClockIcon, DocumentTextIcon } from '@heroicons/react/24/outline';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
  const [jobs, setJobs] = useState({});
  const [selectedJob, setSelectedJob] = useState(null);
  const [socket, setSocket] = useState(null);
  const [activeTab, setActiveTab] = useState('upload');

  useEffect(() => {
    // Initialize socket connection when needed
    return () => {
      if (socket) {
        socket.close();
      }
    };
  }, [socket]);

  const connectToJob = (jobId) => {
    if (socket) {
      socket.close();
    }

    const wsUrl = `${API_URL.replace('http', 'ws')}/ws/${jobId}`;
    const newSocket = new WebSocket(wsUrl);

    newSocket.onopen = () => {
      console.log('Connected to WebSocket for job', jobId);
    };

    newSocket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('Job update received:', data);
        if (data.type === 'job_update') {
          setJobs(prev => ({
            ...prev,
            [jobId]: { ...prev[jobId], ...data.data }
          }));
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    newSocket.onclose = () => {
      console.log('Disconnected from WebSocket');
    };

    newSocket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    setSocket(newSocket);
  };

  const handleJobCreated = (jobData) => {
    const jobId = jobData.job_id;
    setJobs(prev => ({
      ...prev,
      [jobId]: {
        ...jobData,
        logs: [],
        progress: 0
      }
    }));
    setSelectedJob(jobId);
    connectToJob(jobId);
  };

  const refreshJobStatus = async (jobId) => {
    try {
      const response = await axios.get(`${API_URL}/api/jobs/${jobId}`);
      setJobs(prev => ({
        ...prev,
        [jobId]: response.data
      }));
    } catch (error) {
      console.error('Error refreshing job status:', error);
    }
  };

  const formatDuration = (seconds) => {
    if (!seconds) return '0.000s';
    return `${seconds.toFixed(3)}s`;
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'text-green-600';
      case 'failed': return 'text-red-600';
      case 'processing': return 'text-blue-600';
      default: return 'text-gray-600';
    }
  };

  const selectedJobData = selectedJob ? jobs[selectedJob] : null;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <DocumentTextIcon className="h-8 w-8 text-blue-600 mr-3" />
              <h1 className="text-2xl font-bold text-gray-900">Docling Demo</h1>
              <span className="ml-3 px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded-full">
                Document Processing Pipeline
              </span>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center text-sm text-gray-500">
                <ClockIcon className="h-4 w-4 mr-1" />
                Active Jobs: {Object.keys(jobs).length}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Left Panel - Input Controls */}
          <div className="lg:col-span-1 space-y-6">
            {/* Tab Navigation */}
            <div className="bg-white rounded-lg shadow">
              <div className="border-b border-gray-200">
                <nav className="-mb-px flex">
                  <button
                    onClick={() => setActiveTab('upload')}
                    className={`py-2 px-4 border-b-2 font-medium text-sm ${
                      activeTab === 'upload'
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700'
                    }`}
                  >
                    Upload File
                  </button>
                  <button
                    onClick={() => setActiveTab('url')}
                    className={`py-2 px-4 border-b-2 font-medium text-sm ${
                      activeTab === 'url'
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700'
                    }`}
                  >
                    Process URL
                  </button>
                </nav>
              </div>
              
              <div className="p-6">
                {activeTab === 'upload' && (
                  <FileUpload onJobCreated={handleJobCreated} />
                )}
                {activeTab === 'url' && (
                  <URLInput onJobCreated={handleJobCreated} />
                )}
              </div>
            </div>

            {/* Jobs List */}
            <JobsList 
              jobs={jobs} 
              selectedJob={selectedJob}
              onSelectJob={(jobId) => {
                setSelectedJob(jobId);
                connectToJob(jobId);
                refreshJobStatus(jobId);
              }}
            />
          </div>

          {/* Right Panel - Processing Display */}
          <div className="lg:col-span-2 space-y-6">
            {selectedJobData ? (
              <>
                {/* Job Header */}
                <div className="bg-white rounded-lg shadow p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="text-lg font-semibold text-gray-900">
                      Processing: {selectedJobData.filename || selectedJobData.source}
                    </h2>
                    <div className="flex items-center space-x-4">
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                        selectedJobData.status === 'completed' ? 'bg-green-100 text-green-800' :
                        selectedJobData.status === 'failed' ? 'bg-red-100 text-red-800' :
                        selectedJobData.status === 'processing' ? 'bg-blue-100 text-blue-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {selectedJobData.status}
                      </span>
                      {selectedJobData.duration && (
                        <span className="text-sm text-gray-500">
                          {formatDuration(selectedJobData.duration)}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Progress Bar */}
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${selectedJobData.progress || 0}%` }}
                    ></div>
                  </div>
                  <div className="mt-2 text-sm text-gray-500">
                    Progress: {selectedJobData.progress || 0}%
                  </div>

                  {/* Metrics */}
                  {selectedJobData.result?.metrics && (
                    <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-blue-600">
                          {selectedJobData.result.metrics.document_pages}
                        </div>
                        <div className="text-xs text-gray-500">Pages</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-green-600">
                          {Math.round(selectedJobData.result.metrics.words_processed / selectedJobData.result.metrics.total_time)}
                        </div>
                        <div className="text-xs text-gray-500">Words/sec</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-purple-600">
                          {(selectedJobData.result.metrics.document_size_bytes / 1024).toFixed(1)}K
                        </div>
                        <div className="text-xs text-gray-500">File Size</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-orange-600">
                          {selectedJobData.result.metrics.words_processed.toLocaleString()}
                        </div>
                        <div className="text-xs text-gray-500">Words</div>
                      </div>
                    </div>
                  )}
                </div>

                {/* Processing Log */}
                <ProcessingLog 
                  logs={selectedJobData.logs || []} 
                  isProcessing={selectedJobData.status === 'processing'}
                />

                {/* Results */}
                {selectedJobData.result?.success && (
                  <ResultsViewer 
                    result={selectedJobData.result}
                    jobId={selectedJob}
                  />
                )}
              </>
            ) : (
              <div className="bg-white rounded-lg shadow p-12 text-center">
                <DocumentTextIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  No Job Selected
                </h3>
                <p className="text-gray-500">
                  Upload a file or enter a URL to start processing documents with Docling
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;