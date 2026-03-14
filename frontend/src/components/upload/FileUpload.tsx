'use client';

import { useState, useCallback } from 'react';
import { Upload, File, X, CheckCircle, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui';

interface FileUploadProps {
  onFileSelect: (file: File) => void;
  accept?: string;
  maxSize?: number;
  label?: string;
  disabled?: boolean;
  description?: string;
  file?: File | null;
  onFileRemove?: () => void;
  isUploading?: boolean;
  error?: string | null;
}

export function FileUpload({
  onFileSelect,
  accept = '.pdf,.docx,.txt',
  maxSize = 5,
  label = 'Upload File',
  disabled = false,
  description,
  file: initialFile,
  onFileRemove,
  isUploading = false,
  error: externalError,
}: FileUploadProps) {
  const maxSizeBytes = maxSize * 1024 * 1024;

  const [file, setFile] = useState<File | null>(initialFile || null);
  const [error, setError] = useState<string>(externalError || '');
  const [isDragging, setIsDragging] = useState(false);

  const validateFile = (file: File): string | null => {
    if (file.size > maxSizeBytes) {
      return `File size must be less than ${maxSize}MB`;
    }
    const ext = file.name.split('.').pop()?.toLowerCase();
    const allowedExts = accept.split(',').map(a => a.trim().replace('.', ''));
    if (ext && !allowedExts.includes(ext)) {
      return `File type must be one of: ${accept}`;
    }
    return null;
  };

  const handleFile = useCallback((selectedFile: File) => {
    const validationError = validateFile(selectedFile);
    if (validationError) {
      setError(validationError);
      setFile(null);
      return;
    }
    setError('');
    setFile(selectedFile);
    onFileSelect(selectedFile);
  }, [onFileSelect, maxSize, maxSizeBytes, accept]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (disabled) return;
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) handleFile(droppedFile);
  }, [handleFile, disabled]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    if (!disabled) setIsDragging(true);
  }, [disabled]);

  const handleDragLeave = useCallback(() => {
    setIsDragging(false);
  }, []);

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) handleFile(selectedFile);
  }, [handleFile]);

  const handleRemove = useCallback(() => {
    setFile(null);
    setError('');
    onFileRemove?.();
  }, [onFileRemove]);

  return (
    <div className="w-full">
      <label className="block text-sm font-medium mb-2">{label}</label>
      {description && <p className="text-xs text-gray-500 mb-3">{description}</p>}
      
      {!file ? (
        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          className={`
            border-2 border-dashed rounded-lg p-8 text-center transition-colors
            ${isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300'}
            ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer hover:border-blue-400'}
          `}
        >
          <input
            type="file"
            accept={accept}
            onChange={handleFileInput}
            disabled={disabled}
            className="hidden"
            id="file-upload"
          />
          <label htmlFor="file-upload" className={disabled ? 'cursor-not-allowed' : 'cursor-pointer'}>
            <Upload className="w-12 h-12 mx-auto mb-4 text-gray-400" />
            <p className="text-sm text-gray-600 mb-2">
              Drag and drop your file here, or click to browse
            </p>
            <p className="text-xs text-gray-500">
              Supported formats: {accept} (Max {maxSize}MB)
            </p>
          </label>
        </div>
      ) : (
        <div className="border rounded-lg p-4 flex items-center justify-between bg-green-50 border-green-200">
          <div className="flex items-center gap-3">
            <CheckCircle className="w-5 h-5 text-green-600" />
            <div>
              <p className="text-sm font-medium text-gray-900">{file.name}</p>
              <p className="text-xs text-gray-500">
                {(file.size / 1024).toFixed(1)} KB
              </p>
            </div>
          </div>
          <Button
            onClick={handleRemove}
            disabled={disabled || isUploading}
            variant="ghost"
            size="sm"
          >
            <X className="w-4 h-4" />
          </Button>
        </div>
      )}

      {error && (
        <div className="mt-2 flex items-center gap-2 text-red-600 text-sm">
          <AlertCircle className="w-4 h-4" />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
}
