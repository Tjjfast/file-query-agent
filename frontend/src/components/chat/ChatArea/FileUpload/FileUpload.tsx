'use client'

import { useState, useRef } from 'react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Loader2, Upload } from 'lucide-react'

interface FileWithStatus {
  file: File
  originalName: string
  status: 'pending' | 'uploading' | 'done' | 'error'
  preview?: string | null
  size: number
  error?: string
}

export default function FileUpload() {
  const [files, setFiles] = useState<FileWithStatus[]>([])
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [isUploading, setIsUploading] = useState(false)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files?.length) return

    const newFiles = Array.from(e.target.files).map(file => {
      // Create a preview URL for the file (optional, for future use)
      const preview = file.type.startsWith('image/') ? URL.createObjectURL(file) : null
      
      return {
        file,
        originalName: file.name,
        status: 'pending' as const,
        preview,
        size: file.size
      }
    })

    setFiles(prev => [...prev, ...newFiles])
    // Reset the input value to allow selecting the same file again
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index))
  }

  const uploadFiles = async () => {
    if (files.length === 0) return

    setIsUploading(true)
    const formData = new FormData()
    
    // Add all files to FormData
    files.forEach(({ file }) => {
      formData.append('files', file)
    })

    // Update all files to uploading status
    setFiles(prev => 
      prev.map(file => ({
        ...file,
        status: 'uploading' as const
      }))
    )

    try {
      console.log('Sending request to upload files...')
      const API_BASE_URL = 'http://localhost:1111'  // Make sure this matches your backend URL
      
      const response = await fetch(`${API_BASE_URL}/upload`, {
        method: 'POST',
        body: formData,
        headers: {
          'Accept': 'application/json',
        },
        credentials: 'include'  // Important for CORS with credentials
      }).catch(error => {
        console.error('Network error:', error)
        throw new Error(`Failed to connect to the server. Please check if the backend is running on ${API_BASE_URL}`)
      })

      console.log('Response status:', response.status)
      
      if (!response.ok) {
        const errorText = await response.text()
        console.error('Upload failed:', errorText)
        throw new Error(`Upload failed: ${response.status} ${response.statusText}\n${errorText}`)
      }

      const result = await response.json()
      console.log('Upload successful:', result)
      
      // Update all files to done status
      setFiles(prev => 
        prev.map(file => ({
          ...file,
          status: 'done' as const
        }))
      )
      
      toast.success('Files uploaded and indexed successfully')
      // Clear files after successful upload
      setTimeout(() => setFiles([]), 2000)
    } catch (error: unknown) {
      console.error('Upload error:', error)
      const errorMessage = error instanceof Error ? error.message : 'An unknown error occurred'
      toast.error(`Error uploading files: ${errorMessage}`)
      
      // Update all files to error status
      setFiles(prev => 
        prev.map(file => ({
          ...file,
          status: 'error' as const,
          error: errorMessage
        }))
      )
    } finally {
      setIsUploading(false)
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'done':
        return 'text-green-500'
      case 'uploading':
        return 'text-blue-500'
      case 'error':
        return 'text-red-500'
      default:
        return 'text-gray-500'
    }
  }

  return (
    <div className="w-full max-w-2xl mx-auto mb-4">
      <div className="flex flex-col gap-4">
        <div className="flex items-center gap-4">
          <div className="relative">
            <Button
              type="button"
              variant="outline"
              className="flex items-center gap-2 relative"
              disabled={isUploading}
              onClick={() => fileInputRef.current?.click()}
            >
              <Upload className="h-4 w-4" />
              Select Files
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileChange}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                multiple
                accept=".pdf,.doc,.docx,.txt,.csv"
                style={{ display: 'none' }}
              />
            </Button>
          </div>
          
          <Button
            onClick={uploadFiles}
            disabled={files.length === 0 || isUploading}
            className="flex items-center gap-2"
            variant="default"
          >
            {isUploading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Uploading...
              </>
            ) : (
              'Upload Files'
            )}
          </Button>
        </div>
      </div>

      {files.length > 0 && (
        <div className="mt-2 space-y-2 max-h-40 overflow-y-auto p-2 bg-secondary/10 rounded-md">
          {files.map((file, index) => (
            <div 
              key={`${file.file.name}-${index}`}
              className="flex items-center justify-between text-sm p-2 hover:bg-secondary/20 rounded"
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-medium truncate" title={file.originalName}>
                    {file.originalName}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {formatFileSize(file.file.size)}
                  </span>
                </div>
                {file.status === 'error' && file.error && (
                  <div className="text-xs text-red-500">{file.error}</div>
                )}
              </div>
              <div className="flex items-center gap-2">
                <span className={`text-xs ${getStatusColor(file.status)}`}>
                  {file.status.charAt(0).toUpperCase() + file.status.slice(1)}
                </span>
                <button
                  onClick={() => removeFile(index)}
                  className="text-muted-foreground hover:text-foreground"
                  disabled={file.status === 'uploading'}
                >
                  ×
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
