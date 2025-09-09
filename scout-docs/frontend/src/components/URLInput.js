import React, { useState } from 'react';
import axios from 'axios';
import { GlobeAltIcon, ArrowPathIcon } from '@heroicons/react/24/outline';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const URLInput = ({ onJobCreated }) => {
  const [url, setUrl] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [pipeline, setPipeline] = useState('standard');
  const [outputFormat, setOutputFormat] = useState('markdown');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!url.trim()) return;

    setIsProcessing(true);

    try {
      const response = await axios.post(`${API_URL}/api/process-url`, {
        source: url.trim(),
        pipeline,
        output_format: outputFormat
      });

      onJobCreated({
        ...response.data,
        source: url.trim(),
        pipeline,
        output_format: outputFormat
      });

      setUrl(''); // Clear input after successful submission

    } catch (error) {
      console.error('URL processing error:', error);
      alert('Processing failed: ' + (error.response?.data?.detail || error.message));
    } finally {
      setIsProcessing(false);
    }
  };

  const sampleUrls = [
    'https://arxiv.org/pdf/2408.09869', // Docling paper
    'https://arxiv.org/pdf/2206.01062', // Another research paper
    'https://example.com/sample.pdf'
  ];

  return (
    <div className="space-y-4">
      {/* Configuration */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Pipeline
          </label>
          <select
            value={pipeline}
            onChange={(e) => setPipeline(e.target.value)}
            className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            disabled={isProcessing}
          >
            <option value="standard">Standard</option>
            <option value="vlm">VLM (Vision)</option>
          </select>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Output Format
          </label>
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
        </div>
      </div>

      {/* URL Input Form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Document URL
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <GlobeAltIcon className="h-5 w-5 text-gray-400" />
            </div>
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://example.com/document.pdf"
              className="block w-full pl-10 pr-12 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              disabled={isProcessing}
              required
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={isProcessing || !url.trim()}
          className="w-full flex items-center justify-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isProcessing ? (
            <>
              <ArrowPathIcon className="animate-spin -ml-1 mr-2 h-4 w-4" />
              Processing...
            </>
          ) : (
            <>
              <GlobeAltIcon className="-ml-1 mr-2 h-4 w-4" />
              Process URL
            </>
          )}
        </button>
      </form>

      {/* Sample URLs */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Sample URLs
        </label>
        <div className="space-y-2">
          {sampleUrls.map((sampleUrl, index) => (
            <button
              key={index}
              onClick={() => setUrl(sampleUrl)}
              className="block w-full text-left px-3 py-2 text-sm text-blue-600 hover:bg-blue-50 rounded-md border border-blue-200"
              disabled={isProcessing}
            >
              {sampleUrl}
            </button>
          ))}
        </div>
      </div>

      {/* Processing Info */}
      <div className="text-xs text-gray-500 space-y-1">
        <p><strong>Supported:</strong> PDF, HTML, and other web-accessible documents</p>
        <p><strong>Pipeline:</strong> {pipeline === 'vlm' ? 'Vision Language Model (slower, more accurate)' : 'Standard processing (faster)'}</p>
      </div>
    </div>
  );
};

export default URLInput;