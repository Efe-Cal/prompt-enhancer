import { useEffect, useState } from 'react'
import './App.css'

const API_BASE_URL = 'http://localhost:8000'

interface SavedEntry {
  id: number
  task: string
  lazy_prompt: string
  enhanced_prompt: string
  created_at: string
}

function App() {
  const [task, setTask] = useState('')
  const [prompt, setPrompt] = useState('')
  const [enhancedPrompt, setEnhancedPrompt] = useState('')
  const [useWebSearch, setUseWebSearch] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedEntry, setSelectedEntry] = useState('')
  const [detailsOpen, setDetailsOpen] = useState(false)
  const [savedEntries, setSavedEntries] = useState<SavedEntry[]>()
  const [isLoading, setIsLoading] = useState(false)
  const [ws, setWs] = useState<WebSocket | null>(null)
  const [userQuestions, setUserQuestions] = useState<Array<string> | null>(null)
  const [userAnswers, setUserAnswers] = useState<string[]>([])
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  useEffect(() => { 
    handleRefresh()
  }, [])

  const handleEnhance = () => {
    setIsLoading(true)
    setEnhancedPrompt('')
    setErrorMessage(null)
    setUserQuestions(null)
    setUserAnswers([])
    
    // Generate task ID on client side
    const taskId = crypto.randomUUID()
        
    // Connect to WebSocket FIRST
    const websocket = new WebSocket(`ws://localhost:8000/ws/enhance/${taskId}/`)
    
    websocket.onopen = () => {
      console.log('WebSocket connected')
      
      // Send enhance request directly through WebSocket
      websocket.send(JSON.stringify({
        type: 'enhance',
        task,
        lazy_prompt: prompt,
        use_web_search: useWebSearch,
        additional_context_query: searchQuery,
      }))
      console.log('Enhance request sent via WebSocket')
    }
    
    websocket.onmessage = (event) => {
      console.log('WebSocket message received:', event.data)
      const data = JSON.parse(event.data)
      
      if (data.type === 'processing') {
        console.log('Enhancement processing started')
      } else if (data.type === 'user_question') {
        // Show dialog with user questions
        setUserQuestions(data.questions)
        setUserAnswers(new Array(data.questions.length).fill(''))
      } else if (data.type === 'task_complete') {
        // Task finished, display result
        console.log('Task complete, result length:', data.result?.length)
        setEnhancedPrompt(data.result)
        setIsLoading(false)
        websocket.close()
      } else if (data.type === 'task_error') {
        console.error('Task error:', data.error)
        setErrorMessage(data.error)
        setIsLoading(false)
        websocket.close()
      } else if (data.type === 'answer_received') {
        // User answers were received
        setUserQuestions(null)
        setUserAnswers([])
      }
    }
    
    websocket.onerror = (error) => {
      console.error('WebSocket error:', error)
      setIsLoading(false)
    }
    
    websocket.onclose = () => {
      console.log('WebSocket disconnected')
      setWs(null)
    }
    
    setWs(websocket)
  }

  const handleAnswerSubmit = () => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type: 'user_answer',
        answers: userAnswers
      }))
    }
  }

  const handleAnswerChange = (index: number, value: string) => {
    setUserAnswers(prev => {
      const updated = [...prev]
      updated[index] = value
      return updated
    })
  }

  const handleSave = () => {
    fetch(`${API_BASE_URL}/api/save/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        task,
        lazy_prompt: prompt,
        enhanced_prompt: enhancedPrompt,
      }),
    })
      .then(response => response.json())
      .then(data => {
        console.log('Entry saved:', data)
      })
      .catch(error => {
        console.error('Error saving entry:', error)
      }
    )
  }

  const handleLoad = () => {
    const entry = savedEntries?.find(e => e.id === Number(selectedEntry))
    if (entry) {
      setTask(entry.task)
      setPrompt(entry.lazy_prompt)
      setEnhancedPrompt(entry.enhanced_prompt)
    }
  }

  const handleRefresh = () => {
    fetch(`${API_BASE_URL}/api/prompts/`)
      .then(response => response.json())
      .then(data => {
        setSavedEntries(data.prompts)
        console.log('Fetched prompts:', data)
      })
      .catch(error => {
        console.error('Error fetching prompts:', error)
      })

  }

  return (
    <div className="app-container">
      {/* User Question Dialog */}
      {userQuestions && (
        <div className="dialog-overlay">
          <div className="dialog-box">
            <h3>Questions from AI</h3>
            {userQuestions.map((q, index) => (
              <div key={index} className="question-group">
                <p className="dialog-question">{q}</p>
                <input
                  type="text"
                  className="form-input"
                  placeholder="Your answer..."
                  value={userAnswers[index] || ''}
                  onChange={(e) => handleAnswerChange(index, e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && index === userQuestions.length - 1 && handleAnswerSubmit()}
                />
              </div>
            ))}
            <div className="dialog-actions">
              <button className="dialog-btn primary" onClick={handleAnswerSubmit}>
                Submit
              </button>
              <button 
                className="dialog-btn secondary" 
                onClick={() => setUserQuestions(null)}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Left Sidebar - History */}
      <aside className="sidebar">
        <h2 className="sidebar-title">History</h2>        
        <button className="refresh-btn" onClick={handleRefresh}>
          Refresh
        </button>

        <div className="saved-entries-section">
          <label className="saved-entries-label">Saved entries</label>
          <select 
            className="saved-entries-select"
            value={selectedEntry}
            onChange={(e) => setSelectedEntry(e.target.value)}
          >
            {savedEntries?.map(entry => (
              <option key={entry.id} value={entry.id}>
                {entry.task || 'Untitled'} ({entry.created_at})
              </option>
            ))}
          </select>

          <div className="load-section">
            <button className="load-btn" onClick={handleLoad}>
              Load
            </button>
            <span className="saved-count">{savedEntries?.length} saved</span>
          </div>
        </div>

        <div className="details-section">
          <button 
            className="details-toggle"
            onClick={() => setDetailsOpen(!detailsOpen)}
          >
            <span className={`details-arrow ${detailsOpen ? 'open' : ''}`}>›</span>
            Details
          </button>
          {detailsOpen && (
            <div className="details-content">
              {/* Details content would go here */}
            </div>
          )}
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        <h1 className="main-title">Prompt Enhance</h1>
        <p className="main-subtitle">Transform your ideas into powerful prompts</p>

        <div className="form-section">
          <label className="form-label">Task / Topic</label>
          <input
            type="text"
            className="form-input"
            placeholder="Describe the task"
            value={task}
            onChange={(e) => setTask(e.target.value)}
          />
        </div>

        <div className="form-section">
          <label className="form-label">Your Prompt</label>
          <textarea
            className="form-textarea"
            placeholder="Paste your prompt"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
          />
        </div>

        <div className="web-search-section">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={useWebSearch}
              onChange={(e) => setUseWebSearch(e.target.checked)}
            />
            <span>Use web search for context</span>
            <span className="info-icon" title="Enable web search to gather additional context">ⓘ</span>
          </label>
        </div>

        <div className="search-query-section">
          <input
            type="text"
            className="form-input"
            placeholder="Optional specific search query"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        {errorMessage && (
          <div className="error-message" style={{ color: 'red', marginTop: '10px', padding: '10px', border: '1px solid red', borderRadius: '4px', backgroundColor: '#ffe6e6' }}>
            {errorMessage}
          </div>
        )}

        <div className="actions-section">
          <button className="enhance-btn" onClick={handleEnhance}>
            Enhance
          </button>
          <button className="save-btn" onClick={handleSave}>
            Save
          </button>
          <span className="model-indicator">Model: gemini-3-flash-preview</span>
        </div>
      </main>

      {/* Right Panel - Enhanced Prompt */}
      <aside className="enhanced-panel">
        <h2 className="enhanced-title">Enhanced Prompt</h2>
        <pre className="enhanced-output">
          {isLoading ? (
            <div className="spinner-container">
              <div className="spinner"></div>
              <span>Enhancing your prompt...</span>
            </div>
          ) : (
            <code>{enhancedPrompt || 'Your enhanced prompt will appear here.'}</code>
          )}
        </pre>
      </aside>
    </div>
  )
}

export default App
