import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { 
  DocumentTextIcon, 
  CodeBracketIcon, 
  EyeIcon,
  ArrowDownTrayIcon,
  ClipboardDocumentIcon
} from '@heroicons/react/24/outline';

const ResultsViewer = ({ result, jobId }) => {
  const [viewMode, setViewMode] = useState('rendered');
  const [copySuccess, setCopySuccess] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(result.output_content);
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const handleDownload = () => {
    const extension = result.output_format === 'markdown' ? 'md' : 
                     result.output_format === 'html' ? 'html' : 'json';
    const filename = `docling-output-${jobId.substring(0, 8)}.${extension}`;
    
    const blob = new Blob([result.output_content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const renderContent = () => {
    const content = result.output_content;

    if (viewMode === 'raw') {
      return (
        <SyntaxHighlighter
          language={result.output_format === 'json' ? 'json' : 'markdown'}
          style={oneLight}
          customStyle={{
            margin: 0,
            borderRadius: '6px',
            fontSize: '14px'
          }}
        >
          {content}
        </SyntaxHighlighter>
      );
    }

    // Rendered view
    if (result.output_format === 'markdown') {
      return (
        <div className="markdown-body prose prose-sm max-w-none">
          <ReactMarkdown
            components={{
              code({node, inline, className, children, ...props}) {
                const match = /language-(\w+)/.exec(className || '')
                return !inline && match ? (
                  <SyntaxHighlighter
                    style={oneLight}
                    language={match[1]}
                    PreTag="div"
                    {...props}
                  >
                    {String(children).replace(/\n$/, '')}
                  </SyntaxHighlighter>
                ) : (
                  <code className={className} {...props}>
                    {children}
                  </code>
                )
              }
            }}
          >
            {content}
          </ReactMarkdown>
        </div>
      );
    } else if (result.output_format === 'html') {
      return (
        <div 
          className="prose prose-sm max-w-none"
          dangerouslySetInnerHTML={{ __html: content }}
        />
      );
    } else if (result.output_format === 'json') {
      try {
        const jsonData = JSON.parse(content);
        return (
          <SyntaxHighlighter
            language="json"
            style={oneLight}
            customStyle={{
              margin: 0,
              borderRadius: '6px',
              fontSize: '14px'
            }}
          >
            {JSON.stringify(jsonData, null, 2)}
          </SyntaxHighlighter>
        );
      } catch (e) {
        return <pre className="text-red-600">Invalid JSON: {e.message}</pre>;
      }
    }

    return <div className="text-gray-500">Unsupported format</div>;
  };

  const getContentStats = () => {
    const content = result.output_content;
    const lines = content.split('\n').length;
    const words = content.split(/\s+/).filter(w => w.length > 0).length;
    const characters = content.length;

    return { lines, words, characters };
  };

  const stats = getContentStats();

  return (
    <div className="bg-white rounded-lg shadow">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b">
        <div className="flex items-center">
          <DocumentTextIcon className="h-5 w-5 text-gray-400 mr-2" />
          <h3 className="text-lg font-medium text-gray-900">
            Results ({result.output_format.toUpperCase()})
          </h3>
          <span className="ml-2 px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full">
            Success
          </span>
        </div>

        <div className="flex items-center space-x-2">
          {/* View Mode Toggle */}
          <div className="flex rounded-md shadow-sm">
            <button
              onClick={() => setViewMode('rendered')}
              className={`px-3 py-1 text-xs font-medium border ${
                viewMode === 'rendered'
                  ? 'bg-blue-50 border-blue-500 text-blue-700'
                  : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
              } rounded-l-md`}
            >
              <EyeIcon className="h-3 w-3 mr-1 inline" />
              Rendered
            </button>
            <button
              onClick={() => setViewMode('raw')}
              className={`px-3 py-1 text-xs font-medium border-t border-b border-r ${
                viewMode === 'raw'
                  ? 'bg-blue-50 border-blue-500 text-blue-700'
                  : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
              } rounded-r-md`}
            >
              <CodeBracketIcon className="h-3 w-3 mr-1 inline" />
              Raw
            </button>
          </div>

          {/* Action Buttons */}
          <button
            onClick={handleCopy}
            className="flex items-center px-3 py-1 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
          >
            <ClipboardDocumentIcon className="h-3 w-3 mr-1" />
            {copySuccess ? 'Copied!' : 'Copy'}
          </button>
          
          <button
            onClick={handleDownload}
            className="flex items-center px-3 py-1 text-xs font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700"
          >
            <ArrowDownTrayIcon className="h-3 w-3 mr-1" />
            Download
          </button>
        </div>
      </div>

      {/* Stats Bar */}
      <div className="px-4 py-2 bg-gray-50 border-b text-xs text-gray-600 flex justify-between">
        <div className="flex space-x-4">
          <span><strong>Lines:</strong> {stats.lines.toLocaleString()}</span>
          <span><strong>Words:</strong> {stats.words.toLocaleString()}</span>
          <span><strong>Characters:</strong> {stats.characters.toLocaleString()}</span>
        </div>
        <div className="flex space-x-4">
          <span><strong>Format:</strong> {result.output_format.toUpperCase()}</span>
          {result.metadata?.processed_at && (
            <span><strong>Processed:</strong> {new Date(result.metadata.processed_at).toLocaleTimeString()}</span>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        <div className="max-h-96 overflow-y-auto border border-gray-200 rounded-md">
          <div className="p-4">
            {renderContent()}
          </div>
        </div>
      </div>

      {/* Performance Metrics */}
      {result.metrics && (
        <div className="px-4 py-3 bg-gray-50 border-t">
          <h4 className="text-sm font-medium text-gray-900 mb-2">Performance Breakdown</h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
            <div>
              <span className="block text-gray-500">Loading</span>
              <span className="font-medium">{(result.metrics.document_loading_time * 1000).toFixed(0)}ms</span>
            </div>
            <div>
              <span className="block text-gray-500">Conversion</span>
              <span className="font-medium">{(result.metrics.conversion_time * 1000).toFixed(0)}ms</span>
            </div>
            <div>
              <span className="block text-gray-500">Output Gen</span>
              <span className="font-medium">{(result.metrics.output_generation_time * 1000).toFixed(0)}ms</span>
            </div>
            <div>
              <span className="block text-gray-500">Total</span>
              <span className="font-medium text-blue-600">{(result.metrics.total_time * 1000).toFixed(0)}ms</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ResultsViewer;