import { useRef, useState } from 'react'
import { Upload } from 'lucide-react'

export default function FileUpload({ onFilesSelected, multiple = false, accept = '.pdf,.png,.jpg,.jpeg' }) {
  const [dragging, setDragging] = useState(false)
  const [selectedFiles, setSelectedFiles] = useState([])
  const inputRef = useRef(null)

  const handleDragOver = (e) => {
    e.preventDefault()
    setDragging(true)
  }

  const handleDragLeave = () => setDragging(false)

  const handleDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    const files = Array.from(e.dataTransfer.files)
    setSelectedFiles(files)
    onFilesSelected(files)
  }

  const handleClick = () => inputRef.current?.click()

  const handleChange = (e) => {
    const files = Array.from(e.target.files)
    setSelectedFiles(files)
    onFilesSelected(files)
  }

  return (
    <div>
      <div
        className={`upload-zone ${dragging ? 'dragging' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleClick}
      >
        <Upload className="upload-zone-icon" size={48} />
        <div className="upload-zone-text">
          {selectedFiles.length > 0
            ? `${selectedFiles.length} file(s) selected`
            : 'Drop files here or click to browse'}
        </div>
        <div className="upload-zone-hint">
          Supports PDF, PNG, JPG • {multiple ? 'Multiple files allowed' : 'Single file'}
        </div>
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          multiple={multiple}
          onChange={handleChange}
          style={{ display: 'none' }}
        />
      </div>
      {selectedFiles.length > 0 && (
        <div className="mt-12">
          {selectedFiles.map((f, i) => (
            <div key={i} className="flex items-center gap-8 text-sm" style={{ padding: '6px 0' }}>
              <span style={{ color: 'var(--accent-blue)' }}>📄</span>
              <span className="truncate" style={{ flex: 1 }}>{f.name}</span>
              <span className="text-muted">{(f.size / 1024).toFixed(0)} KB</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
