import React, { useState, useEffect } from 'react';
// WebSocket will be handled with native WebSocket API
import axios from 'axios';
import ProcessingInterface from './components/ProcessingInterface';
import ProcessingLog from './components/ProcessingLog';
import ResultsViewer from './components/ResultsViewer';
import CompactJobsTable from './components/CompactJobsTable';
import { 
  ClockIcon, 
  DocumentTextIcon, 
  CpuChipIcon,
  ServerIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  ArrowPathIcon,
  GlobeAltIcon
} from '@heroicons/react/24/outline';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
  const [jobs, setJobs] = useState({});
  const [selectedJob, setSelectedJob] = useState(null);
  const [socket, setSocket] = useState(null);
  const [systemInfo, setSystemInfo] = useState({ compute_type: 'CPU', compute_details: 'Loading...' });

  useEffect(() => {
    // Initialize socket connection when needed
    return () => {
      if (socket) {
        socket.close();
      }
    };
  }, [socket]);

  useEffect(() => {
    // Fetch system information
    const fetchSystemInfo = async () => {
      try {
        const response = await axios.get(`${API_URL}/api/system-info`);
        setSystemInfo(response.data);
      } catch (error) {
        console.error('Failed to fetch system info:', error);
      }
    };
    
    fetchSystemInfo();
    // Refresh system info every 30 seconds
    const interval = setInterval(fetchSystemInfo, 30000);
    return () => clearInterval(interval);
  }, []);

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

  // Calculate job statistics for header
  const jobStats = {
    total: Object.keys(jobs).length,
    processing: Object.values(jobs).filter(j => j.status === 'processing').length,
    completed: Object.values(jobs).filter(j => j.status === 'completed').length,
    failed: Object.values(jobs).filter(j => j.status === 'failed').length
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Executive Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-20">
            <div className="flex items-center">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-blue-600 rounded-lg">
                  <DocumentTextIcon className="h-6 w-6 text-white" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold text-gray-900">Docling Processing Center</h1>
                  <p className="text-sm text-gray-600">Advanced Document Analysis & Conversion</p>
                </div>
              </div>
            </div>
            
            {/* Executive Dashboard Stats */}
            <div className="flex items-center space-x-8">
              <div className="flex items-center space-x-6">
                <div className="text-center">
                  <div className="flex items-center space-x-1">
                    <CpuChipIcon className="h-4 w-4 text-gray-400" />
                    <span className="text-2xl font-bold text-gray-900">{jobStats.total}</span>
                  </div>
                  <span className="text-xs text-gray-500">Total Jobs</span>
                </div>

                <div className="text-center">
                  <div className="flex items-center space-x-1">
                    {systemInfo.compute_type === 'GPU' ? (
                      <ServerIcon className="h-4 w-4 text-green-500" />
                    ) : (
                      <CpuChipIcon className="h-4 w-4 text-blue-500" />
                    )}
                    <span className={`text-lg font-bold ${
                      systemInfo.compute_type === 'GPU' ? 'text-green-600' : 'text-blue-600'
                    }`}>
                      {systemInfo.compute_type}
                    </span>
                  </div>
                  <span className="text-xs text-gray-500" title={systemInfo.compute_details}>
                    Available
                  </span>
                </div>
                
                {jobStats.processing > 0 && (
                  <div className="text-center">
                    <div className="flex items-center space-x-1">
                      <ArrowPathIcon className="h-4 w-4 text-blue-500 animate-spin" />
                      <span className="text-2xl font-bold text-blue-600">{jobStats.processing}</span>
                    </div>
                    <span className="text-xs text-gray-500">Processing</span>
                  </div>
                )}
                
                <div className="text-center">
                  <div className="flex items-center space-x-1">
                    <CheckCircleIcon className="h-4 w-4 text-green-500" />
                    <span className="text-2xl font-bold text-green-600">{jobStats.completed}</span>
                  </div>
                  <span className="text-xs text-gray-500">Completed</span>
                </div>
                
                {jobStats.failed > 0 && (
                  <div className="text-center">
                    <div className="flex items-center space-x-1">
                      <ExclamationCircleIcon className="h-4 w-4 text-red-500" />
                      <span className="text-2xl font-bold text-red-600">{jobStats.failed}</span>
                    </div>
                    <span className="text-xs text-gray-500">Failed</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        
        {/* Consolidated Processing Interface at Top */}
        <ProcessingInterface onJobCreated={handleJobCreated} />

        {/* Jobs Table */}
        <CompactJobsTable 
          jobs={jobs} 
          selectedJob={selectedJob}
          onSelectJob={(jobId) => {
            setSelectedJob(jobId);
            connectToJob(jobId);
            refreshJobStatus(jobId);
          }}
        />

        {/* Streamlined Processing Display - Only show if job selected */}
        {selectedJobData && (
          <div className="space-y-4">

            {/* Results */}
            {selectedJobData.result?.success && (
              <ResultsViewer 
                result={selectedJobData.result}
                jobId={selectedJob}
              />
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;