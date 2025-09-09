import React, { useEffect, useRef } from 'react';
import { CommandLineIcon, ClockIcon } from '@heroicons/react/24/outline';

const ProcessingLog = ({ logs = [], isProcessing = false }) => {
  const logEndRef = useRef(null);
  const containerRef = useRef(null);

  useEffect(() => {
    // Auto-scroll to bottom when new logs arrive
    if (logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs]);

  const getLogTypeColor = (logEntry) => {
    if (logEntry.includes('❌') || logEntry.includes('Error') || logEntry.includes('Failed')) {
      return 'text-red-600';
    }
    if (logEntry.includes('✅') || logEntry.includes('completed')) {
      return 'text-green-600';
    }
    if (logEntry.includes('⚡') || logEntry.includes('🔄') || logEntry.includes('Processing')) {
      return 'text-blue-600';
    }
    if (logEntry.includes('📊') || logEntry.includes('stats') || logEntry.includes('Speed')) {
      return 'text-purple-600';
    }
    if (logEntry.includes('⏱️') || logEntry.includes('Phase')) {
      return 'text-orange-600';
    }
    return 'text-gray-700';
  };

  const getLogIcon = (logEntry) => {
    if (logEntry.includes('❌')) return '🔴';
    if (logEntry.includes('✅')) return '🟢';
    if (logEntry.includes('⚡')) return '⚡';
    if (logEntry.includes('🔄')) return '🔄';
    if (logEntry.includes('📊')) return '📊';
    if (logEntry.includes('⏱️')) return '⏰';
    if (logEntry.includes('📖')) return '📖';
    if (logEntry.includes('📤')) return '📤';
    if (logEntry.includes('🚀')) return '🚀';
    return '📝';
  };

  const formatLogEntry = (logEntry) => {
    // Extract timestamp if present
    const timestampMatch = logEntry.match(/^\[([^\]]+)\]/);
    const timestamp = timestampMatch ? timestampMatch[1] : '';
    const message = timestampMatch ? logEntry.substring(timestampMatch[0].length).trim() : logEntry;
    
    return { timestamp, message };
  };

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="flex items-center justify-between p-4 border-b">
        <div className="flex items-center">
          <CommandLineIcon className="h-5 w-5 text-gray-400 mr-2" />
          <h3 className="text-lg font-medium text-gray-900">Processing Log</h3>
          {isProcessing && (
            <div className="ml-3 flex items-center">
              <div className="animate-pulse h-2 w-2 bg-blue-500 rounded-full mr-2"></div>
              <span className="text-sm text-blue-600">Processing...</span>
            </div>
          )}
        </div>
        <div className="flex items-center text-sm text-gray-500">
          <ClockIcon className="h-4 w-4 mr-1" />
          {logs.length} entries
        </div>
      </div>

      <div 
        ref={containerRef}
        className="log-container max-h-96 overflow-y-auto p-4 bg-gray-50 font-mono text-sm"
      >
        {logs.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            <CommandLineIcon className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p>Waiting for processing to start...</p>
          </div>
        ) : (
          <div className="space-y-1">
            {logs.map((logEntry, index) => {
              const { timestamp, message } = formatLogEntry(logEntry);
              const colorClass = getLogTypeColor(logEntry);
              const icon = getLogIcon(logEntry);
              
              return (
                <div key={index} className="flex items-start space-x-2 py-1">
                  <span className="text-xs mt-0.5">{icon}</span>
                  {timestamp && (
                    <span className="text-xs text-gray-400 font-mono mt-0.5 min-w-0 flex-shrink-0">
                      {timestamp}
                    </span>
                  )}
                  <span className={`${colorClass} break-all flex-1`}>
                    {message}
                  </span>
                </div>
              );
            })}
            <div ref={logEndRef} />
          </div>
        )}
      </div>

      {/* Log Stats Footer */}
      {logs.length > 0 && (
        <div className="px-4 py-2 bg-gray-100 border-t text-xs text-gray-500 flex justify-between">
          <span>
            Errors: {logs.filter(log => log.includes('❌') || log.includes('Error')).length}
          </span>
          <span>
            Completed: {logs.filter(log => log.includes('✅') || log.includes('completed')).length}
          </span>
          <span>
            Total: {logs.length} entries
          </span>
        </div>
      )}
    </div>
  );
};

export default ProcessingLog;