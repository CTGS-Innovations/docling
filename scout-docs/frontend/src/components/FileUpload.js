import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';
import { CloudArrowUpIcon, DocumentIcon } from '@heroicons/react/24/outline';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const FileUpload = ({ onJobCreated }) => {
  const [isUploading, setIsUploading] = useState(false);
  const [pipeline, setPipeline] = useState('standard');
  const [outputFormat, setOutputFormat] = useState('markdown');

  const onDrop = useCallback(async (acceptedFiles) => {
    if (acceptedFiles.length === 0) return;

    const file = acceptedFiles[0];
    setIsUploading(true);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('pipeline', pipeline);
      formData.append('output_format', outputFormat);

      const response = await axios.post(`${API_URL}/api/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      onJobCreated({
        ...response.data,
        filename: file.name,
        pipeline,
        output_format: outputFormat
      });

    } catch (error) {
      console.error('Upload error:', error);
      alert('Upload failed: ' + (error.response?.data?.detail || error.message));
    } finally {
      setIsUploading(false);
    }
  }, [pipeline, outputFormat, onJobCreated]);

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
            disabled={isUploading}
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
            disabled={isUploading}
          >
            <option value="markdown">Markdown</option>
            <option value="html">HTML</option>
            <option value="json">JSON</option>
          </select>
        </div>
      </div>

      {/* Dropzone */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
          isDragActive && !isDragReject
            ? 'border-blue-400 bg-blue-50'
            : isDragReject
            ? 'border-red-400 bg-red-50'
            : 'border-gray-300 hover:border-gray-400'
        } ${isUploading ? 'opacity-50 pointer-events-none' : ''}`}
      >
        <input {...getInputProps()} disabled={isUploading} />
        
        {isUploading ? (
          <div className="space-y-2">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="text-sm text-gray-600">Uploading and processing...</p>
          </div>
        ) : (
          <div className="space-y-2">
            {isDragActive ? (
              <CloudArrowUpIcon className="h-12 w-12 text-blue-400 mx-auto" />
            ) : (
              <DocumentIcon className="h-12 w-12 text-gray-400 mx-auto" />
            )}
            
            {isDragActive && !isDragReject ? (
              <p className="text-sm text-blue-600">Drop the file here...</p>
            ) : isDragReject ? (
              <p className="text-sm text-red-600">File type not supported</p>
            ) : (
              <div>
                <p className="text-sm text-gray-600">
                  Drag & drop a document here, or <span className="text-blue-600 font-medium">browse</span>
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  Supports PDF, DOCX, PPTX, XLSX, HTML, images, audio (max 100MB)
                </p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Processing Info */}
      <div className="text-xs text-gray-500 space-y-1">
        <p><strong>Pipeline:</strong> {pipeline === 'vlm' ? 'Vision Language Model (slower, more accurate)' : 'Standard processing (faster)'}</p>
        <p><strong>Output:</strong> {outputFormat.toUpperCase()} format for downstream processing</p>
      </div>
    </div>
  );
};

export default FileUpload;