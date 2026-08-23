/**
 * DataUpload Component
 * CSV file upload with validation
 */

import React, { useState } from 'react';
import { uploadAPI } from '../services/api';

const DataUpload = ({ onUploadSuccess }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      if (file.name.endsWith('.csv')) {
        setSelectedFile(file);
        setError(null);
      } else {
        setError('Please select a CSV file');
        setSelectedFile(null);
      }
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Please select a file first');
      return;
    }

    try {
      setUploading(true);
      setError(null);
      const response = await uploadAPI.uploadCSV(selectedFile);
      setResult(response);
      
      if (response.success && onUploadSuccess) {
        setTimeout(() => {
          onUploadSuccess(response);
          handleClose();
        }, 2000);
      }
    } catch (err) {
      setError(err.toString());
    } finally {
      setUploading(false);
    }
  };

  const handleClose = () => {
    setIsOpen(false);
    setSelectedFile(null);
    setResult(null);
    setError(null);
  };

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 transition-colors duration-200 text-sm flex items-center space-x-2"
      >
        <span>📤</span>
        <span>Upload Data</span>
      </button>

      {isOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full">
            {/* Header */}
            <div className="bg-gray-600 text-white px-6 py-4 flex items-center justify-between rounded-t-lg">
              <h2 className="text-xl font-bold">Upload Test Data</h2>
              <button
                onClick={handleClose}
                className="text-white hover:text-gray-200 text-2xl"
              >
                ×
              </button>
            </div>

            {/* Content */}
            <div className="p-6">
              {/* Instructions */}
              <div className="mb-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
                <h3 className="text-sm font-semibold text-blue-900 mb-2">Instructions</h3>
                <ul className="text-sm text-blue-800 space-y-1 list-disc list-inside">
                  <li>Upload a CSV file with test data</li>
                  <li>File must match the required column structure</li>
                  <li>Existing tests (same name) will be updated</li>
                  <li>New tests will be added to the database</li>
                </ul>
              </div>

              {/* File Input */}
              <div className="mb-6">
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Select CSV File
                </label>
                <input
                  type="file"
                  accept=".csv"
                  onChange={handleFileSelect}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-capgemini-blue"
                />
                {selectedFile && (
                  <div className="mt-2 text-sm text-gray-600">
                    Selected: <strong>{selectedFile.name}</strong> ({(selectedFile.size / 1024).toFixed(2)} KB)
                  </div>
                )}
              </div>

              {/* Error Display */}
              {error && (
                <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
                  <div className="flex items-start">
                    <span className="text-red-600 mr-2">❌</span>
                    <div className="flex-1">
                      <h4 className="text-sm font-semibold text-red-900 mb-1">Error</h4>
                      <p className="text-sm text-red-700">{error}</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Result Display */}
              {result && (
                <div
                  className={`mb-6 p-4 rounded-lg border ${
                    result.success
                      ? 'bg-green-50 border-green-200'
                      : 'bg-yellow-50 border-yellow-200'
                  }`}
                >
                  <div className="flex items-start">
                    <span className={result.success ? 'text-green-600' : 'text-yellow-600'}>
                      {result.success ? '✓' : '⚠️'}
                    </span>
                    <div className="ml-2 flex-1">
                      <h4
                        className={`text-sm font-semibold mb-2 ${
                          result.success ? 'text-green-900' : 'text-yellow-900'
                        }`}
                      >
                        Upload {result.success ? 'Successful' : 'Completed with Warnings'}
                      </h4>
                      <div className="text-sm space-y-1">
                        <div>New tests added: <strong>{result.new_tests}</strong></div>
                        <div>Tests updated: <strong>{result.updated_tests}</strong></div>
                        <div>Total tests in database: <strong>{result.total_tests_now}</strong></div>
                      </div>
                      {result.warnings && result.warnings.length > 0 && (
                        <div className="mt-3 text-sm text-yellow-800">
                          <strong>Warnings:</strong>
                          <ul className="list-disc list-inside ml-2 mt-1">
                            {result.warnings.map((warning, index) => (
                              <li key={index}>{warning}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Upload Button */}
              <button
                onClick={handleUpload}
                disabled={!selectedFile || uploading}
                className="w-full bg-capgemini-blue text-white px-6 py-3 rounded-lg font-semibold hover:bg-capgemini-darkblue transition-colors duration-200 disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                {uploading ? (
                  <span className="flex items-center justify-center">
                    <div
                      className="spinner mr-3"
                      style={{ width: '20px', height: '20px', borderWidth: '2px' }}
                    ></div>
                    Uploading...
                  </span>
                ) : (
                  'Upload File'
                )}
              </button>
            </div>

            {/* Footer */}
            <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex justify-end rounded-b-lg">
              <button
                onClick={handleClose}
                className="px-6 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors duration-200"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default DataUpload;