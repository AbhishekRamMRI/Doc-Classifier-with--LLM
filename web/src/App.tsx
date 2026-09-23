import { useRef, useState } from 'react'
import type { DocumentResult } from './types'

const API_URL = '/api/classify'

function App() {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [contractorId, setContractorId] = useState('')
  const [results, setResults] = useState<DocumentResult[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files ? Array.from(e.target.files) : []
    setSelectedFiles(files)
    setResults(null)
    setError(null)
  }

  const handleClassify = async () => {
    if (selectedFiles.length === 0) {
      setError('Please choose at least one PDF file first.')
      return
    }

    setIsLoading(true)
    setError(null)
    setResults(null)

    const formData = new FormData()
    selectedFiles.forEach((file) => formData.append('files', file))
    if (contractorId.trim()) {
      formData.append('contractor_id', contractorId.trim())
    }

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const text = await response.text()
        throw new Error(`Server error (${response.status}): ${text}`)
      }

      const data: DocumentResult[] = await response.json()
      setResults(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error occurred.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleReset = () => {
    setSelectedFiles([])
    setResults(null)
    setError(null)
    setContractorId('')
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  return (
    <div className="page">
      <header className="header">
        <h1>Doc Classifier</h1>
        <p>Upload business-document PDFs and classify them with an LLM.</p>
      </header>

      <section className="card">
        <label className="field">
          <span>PDF file(s)</span>
          <input
            ref={fileInputRef}
            type="file"
            accept="application/pdf"
            multiple
            onChange={handleFileChange}
          />
        </label>

        <label className="field">
          <span>Contractor ID (optional)</span>
          <input
            type="text"
            placeholder="e.g. CN-4821"
            value={contractorId}
            onChange={(e) => setContractorId(e.target.value)}
          />
        </label>

        {selectedFiles.length > 0 && (
          <ul className="file-list">
            {selectedFiles.map((f) => (
              <li key={f.name}>{f.name}</li>
            ))}
          </ul>
        )}

        <div className="actions">
          <button
            className="primary"
            onClick={handleClassify}
            disabled={isLoading || selectedFiles.length === 0}
          >
            {isLoading ? 'Classifying…' : 'Classify'}
          </button>
          <button className="secondary" onClick={handleReset} disabled={isLoading}>
            Reset
          </button>
        </div>

        {error && <p className="error">{error}</p>}
      </section>

      {results && (
        <section className="card">
          <h2>Results</h2>
          {results.map((r, i) => (
            <div key={i} className={`result ${r.document_type === 'error' ? 'result-error' : ''}`}>
              <pre>
                {JSON.stringify(
                  {
                    document_type: r.document_type,
                    document_type_confidence: r.document_type_confidence,
                    file_name: r.file_name,
                  },
                  null,
                  2,
                )}
              </pre>
            </div>
          ))}
        </section>
      )}
    </div>
  )
}

export default App
