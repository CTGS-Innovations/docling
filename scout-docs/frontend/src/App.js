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
  const [sockets, setSockets] = useState({});
  const [systemInfo, setSystemInfo] = useState({ compute_type: 'CPU', compute_details: 'Loading...' });

  useEffect(() => {
    // Cleanup all sockets on unmount only
    return () => {
      setSockets(currentSockets => {
        Object.values(currentSockets).forEach(socket => {
          if (socket.readyState === WebSocket.OPEN) {
            socket.close();
          }
        });
        return currentSockets;
      });
    };
  }, []); // No dependencies to prevent premature cleanup

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
    // Don't create duplicate connections
    if (sockets[jobId]) {
      return;
    }

    const wsUrl = `${API_URL.replace('http', 'ws')}/ws/${jobId}`;
    const newSocket = new WebSocket(wsUrl);

    newSocket.onopen = () => {
      console.log(`Connected to WebSocket for job ${jobId}`);
    };

    newSocket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log(`Job update received for ${jobId}:`, data);
        if (data.type === 'job_update') {
          setJobs(prev => {
            const updatedJobs = {
              ...prev,
              [jobId]: { ...prev[jobId], ...data.data }
            };
            
            // Auto-select completed jobs for immediate result display
            const currentSelectedJob = prev[selectedJob];
            if ((!selectedJob || (currentSelectedJob?.status === 'processing' && data.data.status === 'completed'))) {
              setSelectedJob(jobId);
            }
            
            return updatedJobs;
          });
          
          // Auto-close socket if job is completed or failed
          if (data.data.status === 'completed' || data.data.status === 'failed') {
            setTimeout(() => {
              if (newSocket.readyState === WebSocket.OPEN) {
                newSocket.close();
              }
            }, 2000); // Close after 2 seconds to ensure final update is processed
          }
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    newSocket.onclose = () => {
      console.log(`Disconnected from WebSocket for job ${jobId}`);
      // Remove from sockets state when closed
      setSockets(prev => {
        const newSockets = { ...prev };
        delete newSockets[jobId];
        return newSockets;
      });
    };

    newSocket.onerror = (error) => {
      console.error(`WebSocket error for job ${jobId}:`, error);
      // Fallback to polling when WebSocket fails
      setTimeout(() => {
        refreshJobStatus(jobId);
      }, 1000);
    };

    // Add to sockets state
    setSockets(prev => ({
      ...prev,
      [jobId]: newSocket
    }));
  };

  const handleJobCreated = (jobData) => {
    const jobId = jobData.job_id;
    setJobs(prev => ({
      ...prev,
      [jobId]: {
        ...jobData,
        status: 'processing', // Ensure it shows as processing immediately
        logs: [],
        progress: 0
      }
    }));
    
    // Only select the job if no job is currently selected
    if (!selectedJob) {
      setSelectedJob(jobId);
    }
    connectToJob(jobId);
    
    // Start polling as backup for WebSocket failures
    startJobPolling(jobId);
  };

  const startJobPolling = (jobId) => {
    const pollInterval = setInterval(async () => {
      try {
        // Get current job status from API to check if still processing
        const response = await axios.get(`${API_URL}/api/jobs/${jobId}`);
        const jobData = response.data;
        
        // Update job state
        setJobs(prev => ({
          ...prev,
          [jobId]: { ...prev[jobId], ...jobData }
        }));
        
        // Stop polling if job is complete
        if (jobData.status === 'completed' || jobData.status === 'failed') {
          clearInterval(pollInterval);
          
          // Auto-select completed job if no other job selected or current is processing
          setJobs(prev => {
            const currentSelectedJob = prev[selectedJob];
            if (!selectedJob || (currentSelectedJob?.status === 'processing' && jobData.status === 'completed')) {
              setSelectedJob(jobId);
            }
            return prev;
          });
        }
      } catch (error) {
        console.error(`Polling error for job ${jobId}:`, error);
        clearInterval(pollInterval);
      }
    }, 2000); // Poll every 2 seconds
    
    // Auto-cleanup after 5 minutes
    setTimeout(() => {
      clearInterval(pollInterval);
    }, 300000);
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

  // Calculate aggregate throughput stats for batch processing
  const getAggregateStats = () => {
    const allJobs = Object.values(jobs);
    const completedJobs = allJobs.filter(j => j.status === 'completed' && j.result?.metrics);
    if (completedJobs.length === 0) return null;

    const totalPages = completedJobs.reduce((sum, job) => sum + (job.result.metrics.document_pages || 0), 0);
    const totalWords = completedJobs.reduce((sum, job) => sum + (job.result.metrics.words_processed || 0), 0);
    const totalTime = completedJobs.reduce((sum, job) => sum + (job.result.metrics.total_time || 0), 0);
    const totalSize = completedJobs.reduce((sum, job) => sum + (job.result.metrics.document_size_bytes || 0), 0);
    
    // Calculate individual job throughputs for max detection
    const jobThroughputs = completedJobs.map(job => ({
      pagesPerSecond: job.result.metrics.document_pages / job.result.metrics.total_time,
      timePerPage: job.result.metrics.total_time / job.result.metrics.document_pages,
      totalTime: job.result.metrics.total_time
    }));
    
    const avgTimePerJob = totalTime / completedJobs.length;
    const avgPagesPerSecond = totalPages / totalTime;
    const avgMBPerSecond = totalSize > 0 ? (totalSize / (1024 * 1024)) / totalTime : 0;
    
    // Max throughput metrics
    const maxPagesPerSecond = Math.max(...jobThroughputs.map(j => j.pagesPerSecond));
    const minTimePerPage = Math.min(...jobThroughputs.map(j => j.timePerPage));
    const fastestJobTime = Math.min(...jobThroughputs.map(j => j.totalTime));
    
    // Processing mode detection
    const computeModes = allJobs.map(j => j.compute_mode || 'cpu').filter(Boolean);
    const isGpuAccelerated = computeModes.some(mode => mode === 'gpu');
    // More accurate: we have concurrent requests but likely single-threaded compute
    const isConcurrentRequests = allJobs.length > 1;
    const isActivelyProcessingMultiple = jobStats.processing > 1;
    
    // Get the most recent completion time for rate calculation
    const sortedJobs = completedJobs.sort((a, b) => new Date(b.start_time) - new Date(a.start_time));
    const latestJob = sortedJobs[0];
    
    return {
      completedJobs: completedJobs.length,
      totalJobs: jobStats.total,
      totalPages,
      totalWords,
      avgTimePerJob,
      avgPagesPerSecond,
      maxPagesPerSecond,
      minTimePerPage,
      fastestJobTime,
      avgMBPerSecond,
      latestJobTime: latestJob?.result?.metrics?.total_time || 0,
      isGpuAccelerated,
      isConcurrentRequests,
      isActivelyProcessingMultiple,
      computeMode: isGpuAccelerated ? 'GPU' : 'CPU',
      processingMode: isConcurrentRequests ? 'Concurrent Requests' : 'Single Request',
      computeArchitecture: 'Single-threaded' // Honest about actual compute architecture
    };
  };

  const aggregateStats = getAggregateStats();

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

        {/* High-Performance Batch Processing Dashboard */}
        {aggregateStats && jobStats.total > 1 && (
          <div className="bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900 rounded-xl shadow-2xl border border-indigo-500/20 overflow-hidden">
            {/* Animated header with processing pulse */}
            <div className="relative px-6 py-4 bg-gradient-to-r from-indigo-600/90 to-blue-600/90 backdrop-blur-sm">
              <div className="absolute inset-0 bg-gradient-to-r from-blue-400/20 to-purple-400/20 animate-pulse"></div>
              <div className="relative flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="relative">
                    <CpuChipIcon className="h-6 w-6 text-white animate-pulse" />
                    {jobStats.processing > 0 && (
                      <div className="absolute -top-1 -right-1 w-3 h-3 bg-green-400 rounded-full animate-ping"></div>
                    )}
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-white flex items-center">
                      High-Speed Batch Processing
                      {jobStats.processing > 0 && (
                        <span className="ml-2 text-xs bg-green-400/20 text-green-300 px-2 py-1 rounded-full border border-green-400/30 animate-bounce">
                          ⚡ LIVE
                        </span>
                      )}
                    </h3>
                    <p className="text-sm text-blue-200">
                      {aggregateStats.processingMode} • {aggregateStats.computeArchitecture} • {aggregateStats.computeMode} • Peak: {aggregateStats.maxPagesPerSecond.toFixed(1)} pages/sec
                    </p>
                  </div>
                </div>
                
                {/* Real-time completion percentage */}
                <div className="text-right">
                  <div className="text-3xl font-bold text-white">
                    {Math.round((aggregateStats.completedJobs / aggregateStats.totalJobs) * 100)}%
                  </div>
                  <div className="text-xs text-blue-200">Complete</div>
                </div>
              </div>
              
              {/* Progress bar with animation */}
              <div className="mt-3 bg-white/10 rounded-full h-2 overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-green-400 to-blue-400 transition-all duration-1000 ease-out relative"
                  style={{ width: `${(aggregateStats.completedJobs / aggregateStats.totalJobs) * 100}%` }}
                >
                  <div className="absolute inset-0 bg-white/20 animate-pulse"></div>
                </div>
              </div>
            </div>
            
            <div className="p-6 bg-slate-900/50 backdrop-blur-sm">
              {/* Performance metrics grid */}
              <div className="grid grid-cols-2 lg:grid-cols-6 gap-6">
                {/* Completion Counter with Animation */}
                <div className="text-center relative">
                  <div className="relative inline-block">
                    <div className="text-4xl font-bold text-green-400 transition-all duration-500 transform hover:scale-110">
                      {aggregateStats.completedJobs}
                    </div>
                    <div className="text-lg text-gray-400">/{aggregateStats.totalJobs}</div>
                    {jobStats.processing > 0 && (
                      <div className="absolute -top-2 -right-2 w-4 h-4 bg-green-400 rounded-full animate-ping"></div>
                    )}
                  </div>
                  <div className="text-xs text-green-300 uppercase tracking-wider mt-1">Documents</div>
                </div>

                {/* Processing Architecture */}
                <div className="text-center relative">
                  <div className="text-2xl font-bold text-cyan-400 transition-all duration-500">
                    {aggregateStats.isConcurrentRequests ? '📨' : '🔧'}
                  </div>
                  <div className="text-sm font-semibold text-cyan-300 mt-1">
                    {aggregateStats.processingMode}
                  </div>
                  <div className="text-xs text-cyan-300 uppercase tracking-wider">
                    {aggregateStats.computeArchitecture}
                  </div>
                  <div className="text-xs text-cyan-400 mt-1">
                    {aggregateStats.computeMode}
                  </div>
                  {aggregateStats.isConcurrentRequests && (
                    <div className="absolute inset-0 bg-cyan-400/10 rounded-lg animate-pulse"></div>
                  )}
                </div>

                {/* MAX SPEED - Highlighted */}
                <div className="text-center relative">
                  <div className="relative">
                    <div className="text-sm text-red-400 font-bold uppercase tracking-wider">MAX SPEED</div>
                    <div className="text-5xl font-bold text-red-400 transition-all duration-500 drop-shadow-lg">
                      {aggregateStats.maxPagesPerSecond.toFixed(1)}
                    </div>
                    <div className="text-xs text-red-300 uppercase tracking-wider mt-1">Pages/sec</div>
                    <div className="absolute inset-0 bg-red-400/20 rounded-lg animate-pulse"></div>
                  </div>
                </div>

                {/* Average Speed */}
                <div className="text-center relative">
                  <div className="text-sm text-blue-400 font-semibold uppercase tracking-wider">AVG</div>
                  <div className="text-4xl font-bold text-blue-400 transition-all duration-500">
                    {aggregateStats.avgPagesPerSecond.toFixed(1)}
                  </div>
                  <div className="text-xs text-blue-300 uppercase tracking-wider mt-1">Pages/sec</div>
                  <div className="absolute inset-0 bg-blue-400/10 rounded-lg animate-pulse"></div>
                </div>

                {/* Fastest Job */}
                <div className="text-center">
                  <div className="text-sm text-green-400 font-semibold uppercase tracking-wider">FASTEST</div>
                  <div className="text-4xl font-bold text-green-400">
                    {aggregateStats.fastestJobTime.toFixed(2)}s
                  </div>
                  <div className="text-xs text-green-300 uppercase tracking-wider mt-1">Job Time</div>
                </div>

                {/* Total Pages */}
                <div className="text-center">
                  <div className="text-sm text-purple-400 font-semibold uppercase tracking-wider">TOTAL</div>
                  <div className="text-4xl font-bold text-purple-400 transition-all duration-500">
                    {aggregateStats.totalPages}
                  </div>
                  <div className="text-xs text-purple-300 uppercase tracking-wider mt-1">Pages</div>
                </div>
              </div>

              {/* Real-time status bar */}
              <div className="mt-6 pt-4 border-t border-gray-700/50">
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center space-x-4">
                    {jobStats.processing > 0 ? (
                      <span className="flex items-center text-green-400 animate-pulse">
                        <div className="w-2 h-2 bg-green-400 rounded-full mr-2 animate-ping"></div>
                        {jobStats.processing} jobs queued • {aggregateStats.computeArchitecture} • {aggregateStats.computeMode}
                      </span>
                    ) : (
                      <span className="flex items-center text-green-400">
                        <CheckCircleIcon className="h-4 w-4 mr-2" />
                        Batch complete • {aggregateStats.computeArchitecture} • Peak: {aggregateStats.maxPagesPerSecond.toFixed(1)} pages/sec
                      </span>
                    )}
                  </div>
                  
                  {aggregateStats.latestJobTime > 0 && (
                    <div className="flex items-center space-x-2 text-blue-300">
                      <ArrowPathIcon className="h-4 w-4" />
                      <span>Latest: {aggregateStats.latestJobTime.toFixed(2)}s</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

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