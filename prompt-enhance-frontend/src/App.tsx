import { useEffect, useState } from 'react'
import './App.css'
import { Analytics } from '@vercel/analytics/react'


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

  const [savedEntries, setSavedEntries] = useState<SavedEntry[]>()
  const [isLoading, setIsLoading] = useState(false)
  const [ws, setWs] = useState<WebSocket | null>(null)
  const [userQuestions, setUserQuestions] = useState<Array<string> | null>(null)
  const [userAnswers, setUserAnswers] = useState<string[]>([])
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  // Prompt style options
  const [promptStyleOpen, setPromptStyleOpen] = useState(false)
  const [promptFormatting, setPromptFormatting] = useState<'Any' | 'Markdown' | 'XML' |'Plain Text'>('Any')
  const [promptLength, setPromptLength] = useState<'Concise' | 'Detailed' | 'Comprehensive'>('Detailed')
  const [promptTechnique, setPromptTechnique] = useState<'Any' | 'Zero-Shot' | 'Few-Shot' | 'Chain-of-Thought'>('Any')

  useEffect(() => {
    handleRefresh()
  }, [])

  const [models, setModels] = useState<string[]>([])
  const [targetModel, setTargetModel] = useState<string>('')
  const [isReasoningNative, setIsReasoningNative] = useState<boolean>(false)

  const formatModelName = (name: string) => {
    // take the part after "/"
    return name.split('/').pop() || name
  }

  useEffect(() => {
    fetch('/hackclub-api/proxy/v1/models')
      .then(res => res.json())
      .then(data => {
        let fetchedModels: string[] = []
        if (Array.isArray(data)) {
          fetchedModels = data.map((m: any) => formatModelName(m.id))
        } else if (data.data && Array.isArray(data.data)) {
          fetchedModels = data.data.map((m: any) => formatModelName(m.id))
        }
        setModels(fetchedModels)
      })
      .catch(err => console.error('Failed to fetch models:', err))
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
    const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'
    const websocket = new WebSocket(`${wsUrl}/ws/enhance/${taskId}/`)

    websocket.onopen = () => {
      console.log('WebSocket connected')

      // Send enhance request directly through WebSocket
      websocket.send(JSON.stringify({
        type: 'enhance',
        task,
        lazy_prompt: prompt,
        use_web_search: useWebSearch,
        additional_context_query: searchQuery,
        target_model: targetModel,
        is_reasoning_native: isReasoningNative,
        prompt_style: {
          formatting: promptFormatting,
          length: promptLength,
          technique: promptTechnique
        }
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
        saveToLocalStorage(task, prompt, data.result)
        setIsLoading(false)
        setErrorMessage(data.is_fallback ? "Using fallback model due to HCAI service downtime." : null)
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

  const saveToLocalStorage = (currentTask: string, currentPrompt: string, result: string) => {
    const newEntry: SavedEntry = {
      id: Date.now(),
      task: currentTask,
      lazy_prompt: currentPrompt,
      enhanced_prompt: result,
      created_at: new Date().toLocaleString()
    }

    const existingEntries = JSON.parse(localStorage.getItem('saved_prompts') || '[]')
    const updatedEntries = [newEntry, ...existingEntries]
    localStorage.setItem('saved_prompts', JSON.stringify(updatedEntries))
    setSavedEntries(updatedEntries)
    console.log('Auto-saved to local storage:', newEntry)
  }

  const handleLoad = (id: number) => {
    const entry = savedEntries?.find(e => e.id === id)
    if (entry) {
      setTask(entry.task)
      setPrompt(entry.lazy_prompt)
      setEnhancedPrompt(entry.enhanced_prompt)
      setSelectedEntry(String(id))
    }
  }

  const handleDelete = (id: number, e: React.MouseEvent) => {
    e.stopPropagation()
    const updatedEntries = savedEntries?.filter(entry => entry.id !== id) || []
    setSavedEntries(updatedEntries)
    localStorage.setItem('saved_prompts', JSON.stringify(updatedEntries))
    if (selectedEntry === String(id)) {
      setSelectedEntry('')
    }
  }

  const handleRefresh = () => {
    const stored = localStorage.getItem('saved_prompts')
    if (stored) {
      setSavedEntries(JSON.parse(stored))
    }
  }

  const handleQuestionCancel = () => {
    setUserQuestions(null)
    setUserAnswers([])
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type: 'user_answer',
        answers: "CANCEL"
      }))
    }
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
                  onKeyDown={(e) => e.key === 'Enter' && index === userQuestions.length - 1 && handleAnswerSubmit()}
                />
              </div>
            ))}
            <div className="dialog-actions">
              <button className="dialog-btn primary" onClick={handleAnswerSubmit}>
                Submit
              </button>
              <button
                className="dialog-btn secondary"
                onClick={handleQuestionCancel}
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
        {/* Refresh button removed for auto-refresh */}

        <div className="saved-entries-section">
          <div className="saved-list">
            {savedEntries?.map(entry => (
              <div key={entry.id} className={`saved-item ${selectedEntry === String(entry.id) ? 'active' : ''}`}>
                <button
                  className="saved-item-main"
                  onClick={() => handleLoad(entry.id)}
                >
                  <span className="saved-item-title">{entry.task || 'Untitled'}</span>
                  <span className="saved-item-date">{entry.created_at}</span>
                </button>
                <button
                  className="saved-item-delete"
                  onClick={(e) => handleDelete(entry.id, e)}
                  title="Delete"
                >
                  ×
                </button>
              </div>
            ))}
            {(!savedEntries || savedEntries.length === 0) && (
              <div className="empty-history">No saved prompts yet</div>
            )}
          </div>
        </div>


      </aside>

      {/* Main Content */}
      <main className="main-content">
        <h1 className="main-title">Prompt Enhance</h1>
        <p className="main-subtitle">Transform your ideas into powerful prompts</p>

        <div className="form-section">
          <label className="form-label">Task / Goal</label>
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

        {/* Collapsible Prompt Style Section */}
        <div className="prompt-style-section">
          <button
            className="prompt-style-header"
            onClick={() => setPromptStyleOpen(!promptStyleOpen)}
          >
            <span>Prompt Style</span>
            <span className={`chevron ${promptStyleOpen ? 'open' : ''}`}>▼</span>
          </button>
          {promptStyleOpen && (
            <div className="prompt-style-content">
              <div className="style-option">
                <label className="style-label">Formatting</label>
                <div className="toggle-group">
                  <button
                    className={`toggle-btn ${promptFormatting === 'Any' ? 'active' : ''}`}
                    onClick={() => setPromptFormatting('Any')}
                  >
                    Any
                  </button>
                  <button
                    className={`toggle-btn ${promptFormatting === 'Markdown' ? 'active' : ''}`}
                    onClick={() => setPromptFormatting('Markdown')}
                  >
                    Markdown
                  </button>
                  <button
                    className={`toggle-btn ${promptFormatting === 'XML' ? 'active' : ''}`}
                    onClick={() => setPromptFormatting('XML')}
                  >
                    XML
                  </button>
                  <button
                    className={`toggle-btn ${promptFormatting === 'Plain Text' ? 'active' : ''}`}
                    onClick={() => setPromptFormatting('Plain Text')}
                  >
                    Plain Text
                  </button>
                </div>
              </div>
              <div className="style-option">
                <label className="style-label">Length</label>
                <div className="toggle-group">
                  <button
                    className={`toggle-btn ${promptLength === 'Concise' ? 'active' : ''}`}
                    onClick={() => setPromptLength('Concise')}
                  >
                    Concise
                  </button>
                  <button
                    className={`toggle-btn ${promptLength === 'Detailed' ? 'active' : ''}`}
                    onClick={() => setPromptLength('Detailed')}
                  >
                    Detailed
                  </button>
                  <button
                    className={`toggle-btn ${promptLength === 'Comprehensive' ? 'active' : ''}`}
                    onClick={() => setPromptLength('Comprehensive')}
                  >
                    Comprehensive
                  </button>
                </div>
              </div>
              <div className="style-option">
                <label className="style-label">Technique</label>
                <div className="toggle-group">
                  <button
                    className={`toggle-btn ${promptTechnique === 'Any' ? 'active' : ''}`}
                    onClick={() => setPromptTechnique('Any')}
                  >
                    Any
                  </button>
                  <button
                    className={`toggle-btn ${promptTechnique === 'Zero-Shot' ? 'active' : ''}`}
                    onClick={() => setPromptTechnique('Zero-Shot')}
                  >
                    Zero-shot
                  </button>
                  <button
                    className={`toggle-btn ${promptTechnique === 'Few-Shot' ? 'active' : ''}`}
                    onClick={() => setPromptTechnique('Few-Shot')}
                  >
                    Few-shot
                  </button>
                  <button
                    className={`toggle-btn ${promptTechnique === 'Chain-of-Thought' ? 'active' : ''}`}
                    onClick={() => setPromptTechnique('Chain-of-Thought')}
                  >
                    Chain-of-Thought
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        {errorMessage && (
          <div className="error-message" style={{ color: 'red', marginTop: '10px', marginBottom: '10px', padding: '10px', border: '1px solid red', borderRadius: '4px', backgroundColor: '#ffe6e6' }}>
            {errorMessage}
          </div>
        )}

        <div className="actions-section">
          <button className="enhance-btn" onClick={handleEnhance}>
            Enhance
          </button>

          <div className="model-selector">
            <input
              type="text"
              list="models-list"
              value={targetModel}
              onChange={(e) => setTargetModel(e.target.value)}
              className="form-input model-input"
              placeholder="Target Model (e.g. gpt-5)"
            />
            <datalist id="models-list">
              {models.map(model => (
                <option key={model} value={model} />
              ))}
            </datalist>
            <label className="reasoning-native-label">
              <input
                type="checkbox"
                checked={isReasoningNative}
                onChange={(e) => setIsReasoningNative(e.target.checked)}
              />
              <span>Reasoning Native</span>
              <span className="info-icon" title="Enable if the target model has native reasoning capabilities (e.g., o1, o3, Gemini-2.5-Flash-Thinking). This skips Chain-of-Thought prompting.">ⓘ</span>
            </label>
          </div>
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
      <Analytics />
    </div>
  )
}

export default App
