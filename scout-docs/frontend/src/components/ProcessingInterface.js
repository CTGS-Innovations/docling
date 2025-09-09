import React, { useCallback, useState, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';
import { 
  CloudArrowUpIcon, 
  DocumentIcon, 
  GlobeAltIcon, 
  ArrowPathIcon,
  CpuChipIcon,
  ServerIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const ProcessingInterface = ({ onJobCreated }) => {
  // Form state
  const [pipeline, setPipeline] = useState('fast_text');
  const [outputFormat, setOutputFormat] = useState('markdown');
  const [computeMode, setComputeMode] = useState('cpu'); // 'cpu' or 'gpu'
  
  // Pipeline profiles state
  const [pipelineProfiles, setPipelineProfiles] = useState([]);
  const [isLoadingProfiles, setIsLoadingProfiles] = useState(true);
  
  // Processing state
  const [isProcessing, setIsProcessing] = useState(false);
  const [activeTab, setActiveTab] = useState('file');
  
  // File upload state
  const [isUploading, setIsUploading] = useState(false);
  
  // URL processing state
  const [url, setUrl] = useState('');

  // Load pipeline profiles on component mount
  useEffect(() => {
    const fetchPipelineProfiles = async () => {
      try {
        const response = await axios.get(`${API_URL}/api/pipelines`);
        setPipelineProfiles(response.data.profiles || []);
      } catch (error) {
        console.error('Failed to fetch pipeline profiles:', error);
        // Fallback to basic profiles
        setPipelineProfiles([
          { id: 'standard', name: 'Standard', description: 'General purpose processing' },
          { id: 'vlm', name: 'VLM (Vision)', description: 'AI vision models' }
        ]);
      } finally {
        setIsLoadingProfiles(false);
      }
    };

    fetchPipelineProfiles();
  }, []);

  // Get current pipeline config for display
  const getCurrentPipelineConfig = () => {
    return pipelineProfiles.find(p => p.id === pipeline) || {};
  };

  // Auto-adjust compute mode based on pipeline selection
  useEffect(() => {
    const config = getCurrentPipelineConfig();
    if (config.compute_preference === 'GPU' && computeMode === 'cpu') {
      setComputeMode('gpu'); // Auto-switch to GPU for GPU-preferred pipelines
    } else if (config.compute_preference === 'CPU' && computeMode === 'gpu') {
      setComputeMode('cpu'); // Auto-switch to CPU for CPU-only pipelines
    }
  }, [pipeline, pipelineProfiles]);

  // File drop handler
  const onDrop = useCallback(async (acceptedFiles) => {
    if (acceptedFiles.length === 0) return;

    const file = acceptedFiles[0];
    setIsUploading(true);
    setIsProcessing(true);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('pipeline', pipeline);
      formData.append('output_format', outputFormat);

      // Choose endpoint based on compute mode
      const endpoint = computeMode === 'gpu' ? '/api/upload-gpu' : '/api/upload-cpu';
      const response = await axios.post(`${API_URL}${endpoint}`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      onJobCreated({
        ...response.data,
        filename: file.name,
        pipeline,
        output_format: outputFormat,
        compute_mode: computeMode
      });

    } catch (error) {
      console.error('Upload error:', error);
      alert('Upload failed: ' + (error.response?.data?.detail || error.message));
    } finally {
      setIsUploading(false);
      setIsProcessing(false);
    }
  }, [pipeline, outputFormat, computeMode, onJobCreated]);

  // URL submit handler
  const handleUrlSubmit = async (e) => {
    e.preventDefault();
    if (!url.trim()) return;

    setIsProcessing(true);

    try {
      // Choose endpoint based on compute mode
      const endpoint = computeMode === 'gpu' ? '/api/process-url-gpu' : '/api/process-url-cpu';
      const response = await axios.post(`${API_URL}${endpoint}`, {
        source: url.trim(),
        pipeline,
        output_format: outputFormat
      });

      onJobCreated({
        ...response.data,
        source: url.trim(),
        pipeline,
        output_format: outputFormat,
        compute_mode: computeMode
      });

      setUrl(''); // Clear input after successful submission

    } catch (error) {
      console.error('URL processing error:', error);
      alert('Processing failed: ' + (error.response?.data?.detail || error.message));
    } finally {
      setIsProcessing(false);
    }
  };

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    multiple: false,
    maxSize: 100 * 1024 * 1024, // 100MB
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['.pptx'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'text/html': ['.html'],
      'text/markdown': ['.md'],
      'image/*': ['.png', '.jpg', '.jpeg', '.tiff'],
      'audio/*': ['.wav', '.mp3']
    }
  });

  const sampleUrls = [
    'https://arxiv.org/pdf/2408.09869', // Docling paper
    'https://arxiv.org/pdf/2206.01062', // Another research paper
    'https://example.com/sample.pdf'
  ];

  return (
    <div className="bg-white rounded-lg shadow-lg">
      <div className="px-6 py-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900">Process New Document</h3>
        <p className="text-sm text-gray-600">Upload a file or enter a URL to begin document analysis with customizable processing options</p>
      </div>
      
      <div className="p-6 space-y-6">
        {/* Compact Processing Configuration with Integrated Input */}
        <div className="bg-gray-50 rounded-lg p-4">
          <h4 className="text-sm font-semibold text-gray-800 flex items-center mb-4">
            <InformationCircleIcon className="h-4 w-4 mr-2 text-blue-600" />
            Processing Configuration
          </h4>
          
          {/* Configuration Row */}
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 mb-4">
            {/* Compute Mode */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Compute Mode</label>
              <div className="flex space-x-4">
                <label className="flex items-center">
                  <input
                    type="radio"
                    name="compute_mode"
                    value="cpu"
                    checked={computeMode === 'cpu'}
                    onChange={(e) => setComputeMode(e.target.value)}
                    disabled={isProcessing}
                    className="focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300"
                  />
                  <span className="ml-1 flex items-center text-sm text-gray-700">
                    <CpuChipIcon className="h-4 w-4 mr-1 text-blue-600" />
                    CPU
                  </span>
                </label>
                <label className="flex items-center">
                  <input
                    type="radio"
                    name="compute_mode"
                    value="gpu"
                    checked={computeMode === 'gpu'}
                    onChange={(e) => setComputeMode(e.target.value)}
                    disabled={isProcessing}
                    className="focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300"
                  />
                  <span className="ml-1 flex items-center text-sm text-gray-700">
                    <ServerIcon className="h-4 w-4 mr-1 text-green-600" />
                    GPU
                  </span>
                </label>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                {(() => {
                  const config = getCurrentPipelineConfig();
                  const isRecommended = config.compute_preference === computeMode.toUpperCase() || 
                                       config.compute_preference === 'Either';
                  const recommendedText = isRecommended ? '✓ Recommended' : 
                                        `Recommended: ${config.compute_preference}`;
                  return `${computeMode === 'gpu' ? 'GPU acceleration (~2-10s/page)' : 'Standard processing (~1-3s/page)'} ${recommendedText}`;
                })()}
              </p>
            </div>

            {/* Pipeline */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Pipeline</label>
              <select
                value={pipeline}
                onChange={(e) => setPipeline(e.target.value)}
                className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                disabled={isProcessing || isLoadingProfiles}
              >
                {isLoadingProfiles ? (
                  <option>Loading pipelines...</option>
                ) : (
                  pipelineProfiles.map(profile => (
                    <option key={profile.id} value={profile.id}>
                      {profile.name} ({profile.performance})
                    </option>
                  ))
                )}
              </select>
              <div className="text-xs text-gray-500 mt-1">
                {!isLoadingProfiles && getCurrentPipelineConfig().description && (
                  <div>
                    <div><strong>Use case:</strong> {getCurrentPipelineConfig().use_case}</div>
                    <div><strong>Features:</strong> {getCurrentPipelineConfig().features?.join(', ')}</div>
                    <div><strong>Compute:</strong> {getCurrentPipelineConfig().compute_preference}</div>
                  </div>
                )}
              </div>
            </div>
            
            {/* Output Format */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Output Format</label>
              <select
                value={outputFormat}
                onChange={(e) => setOutputFormat(e.target.value)}
                className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                disabled={isProcessing}
              >
                <option value="markdown">Markdown</option>
                <option value="html">HTML</option>
                <option value="json">JSON</option>
              </select>
              <p className="text-xs text-gray-500 mt-1">Export format</p>
            </div>

            {/* Input Method Toggle */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Input Method</label>
              <div className="flex bg-white border border-gray-300 rounded-md">
                <button
                  onClick={() => setActiveTab('file')}
                  className={`flex-1 px-3 py-2 text-sm font-medium rounded-l-md ${
                    activeTab === 'file'
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-700 hover:text-gray-900'
                  }`}
                  disabled={isProcessing}
                >
                  <DocumentIcon className="h-4 w-4 inline mr-1" />
                  File
                </button>
                <button
                  onClick={() => setActiveTab('url')}
                  className={`flex-1 px-3 py-2 text-sm font-medium rounded-r-md ${
                    activeTab === 'url'
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-700 hover:text-gray-900'
                  }`}
                  disabled={isProcessing}
                >
                  <GlobeAltIcon className="h-4 w-4 inline mr-1" />
                  URL
                </button>
              </div>
              <p className="text-xs text-gray-500 mt-1">Choose input type</p>
            </div>
          </div>

          {/* Compact Input Area */}
          <div className="border-t border-gray-200 pt-4">
            {activeTab === 'file' ? (
              /* Compact File Upload */
              <div
                {...getRootProps()}
                className={`border-2 border-dashed rounded-lg p-4 text-center cursor-pointer transition-colors ${
                  isDragActive && !isDragReject
                    ? 'border-blue-400 bg-blue-50'
                    : isDragReject
                    ? 'border-red-400 bg-red-50'
                    : 'border-gray-300 hover:border-gray-400'
                } ${isProcessing ? 'opacity-50 pointer-events-none' : ''}`}
              >
                <input {...getInputProps()} disabled={isProcessing} />
                
                {isProcessing ? (
                  <div className="flex items-center justify-center space-x-2">
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
                    <p className="text-sm text-gray-600">Processing with {computeMode.toUpperCase()}...</p>
                  </div>
                ) : (
                  <div className="flex items-center justify-center space-x-3">
                    {isDragActive ? (
                      <CloudArrowUpIcon className="h-6 w-6 text-blue-400" />
                    ) : (
                      <DocumentIcon className="h-6 w-6 text-gray-400" />
                    )}
                    
                    <div className="text-left">
                      {isDragActive && !isDragReject ? (
                        <p className="text-sm text-blue-600 font-medium">Drop the file here</p>
                      ) : isDragReject ? (
                        <p className="text-sm text-red-600">File type not supported</p>
                      ) : (
                        <>
                          <p className="text-sm text-gray-700">
                            Drop file here or <span className="text-blue-600 font-medium">browse</span>
                          </p>
                          <p className="text-xs text-gray-500">PDF, DOCX, PPTX, XLSX, HTML, images (max 100MB)</p>
                        </>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              /* Compact URL Processing */
              <form onSubmit={handleUrlSubmit} className="flex space-x-3">
                <div className="flex-1">
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <GlobeAltIcon className="h-4 w-4 text-gray-400" />
                    </div>
                    <input
                      type="url"
                      value={url}
                      onChange={(e) => setUrl(e.target.value)}
                      placeholder="https://example.com/document.pdf"
                      className="block w-full pl-9 pr-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                      disabled={isProcessing}
                      required
                    />
                  </div>
                </div>
                <button
                  type="submit"
                  disabled={isProcessing || !url.trim()}
                  className="flex items-center justify-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isProcessing ? (
                    <>
                      <ArrowPathIcon className="animate-spin h-4 w-4 mr-2" />
                      Processing...
                    </>
                  ) : (
                    <>
                      <ArrowPathIcon className="h-4 w-4 mr-2" />
                      Process URL
                    </>
                  )}
                </button>
              </form>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProcessingInterface;