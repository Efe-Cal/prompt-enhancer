import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import './App.css'
import { Analytics } from '@vercel/analytics/react'


interface SavedEntry {
  id: number
  task: string
  lazy_prompt: string
  enhanced_prompt: string
  created_at: string,
  task_id: string
}

function App() {
  const [goal, setGoal] = useState('')
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
  const [originalEnhancedPrompt, setOriginalEnhancedPrompt] = useState('')
  const [copySuccess, setCopySuccess] = useState(false)
  const [lastTaskId, setLastTaskId] = useState<string | null>(null)

  const enhancedTextareaRef = useRef<HTMLTextAreaElement | null>(null)

  const resizeEnhancedTextarea = () => {
    const textarea = enhancedTextareaRef.current
    if (!textarea) return

    // Reset first so shrinking works as well.
    textarea.style.height = 'auto'

    const maxHeightPx = Math.floor(window.innerHeight * 0.8)
    const nextHeightPx = Math.min(textarea.scrollHeight, maxHeightPx)

    textarea.style.height = `${nextHeightPx}px`
    textarea.style.overflowY = textarea.scrollHeight > maxHeightPx ? 'auto' : 'hidden'
  }

  // Prompt style options
  const [promptStyleOpen, setPromptStyleOpen] = useState(false)
  const [promptFormatting, setPromptFormatting] = useState<'Any' | 'Markdown' | 'XML' |'Plain Text'>('Any')
  const [promptLength, setPromptLength] = useState<'Concise' | 'Detailed' | 'Comprehensive'>('Detailed')
  const [promptTechnique, setPromptTechnique] = useState<'Any' | 'Zero-Shot' | 'Few-Shot' | 'Chain-of-Thought'>('Any')

  // Mobile menu state
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  // Edit request state
  const [editRequest, setEditRequest] = useState('')
  const [isEditLoading, setIsEditLoading] = useState(false)

  useEffect(() => {
    handleRefresh()
  }, [])

  useLayoutEffect(() => {
    if (!enhancedPrompt || isLoading) return
    resizeEnhancedTextarea()
  }, [enhancedPrompt, isLoading])

  useEffect(() => {
    if (!enhancedPrompt || isLoading) return
    const onResize = () => resizeEnhancedTextarea()
    window.addEventListener('resize', onResize)
    return () => window.removeEventListener('resize', onResize)
  }, [enhancedPrompt, isLoading])

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
        task: goal,
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
        setOriginalEnhancedPrompt(data.result)
        setLastTaskId(taskId)
        saveToLocalStorage(goal, prompt, data.result, taskId)
        requestAnimationFrame(() => resizeEnhancedTextarea())
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

  const handleEditRequest = () => {
    if (!editRequest.trim() || !enhancedPrompt) return

    console.log('Submitting edit request:', editRequest)
    setIsEditLoading(true)

    // Generate task ID on client side
    const taskId = crypto.randomUUID()

    const enhancementTaskId = savedEntries?.find(e => e.id === parseInt(selectedEntry))?.task_id || lastTaskId

    // Connect to WebSocket
    const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'
    const websocket = new WebSocket(`${wsUrl}/ws/edit/${taskId}/`)

    websocket.onopen = () => {
      console.log('WebSocket connected for edit request')

      // Send edit request through WebSocket
      websocket.send(JSON.stringify({
        type: 'edit_request',
        current_prompt: enhancedPrompt,
        edit_instructions: editRequest,
        target_model: targetModel,
        is_reasoning_native: isReasoningNative,
        prompt_style: {
          formatting: promptFormatting,
          length: promptLength,
          technique: promptTechnique
        },
        enhancement_task_id: enhancementTaskId
      }))
      console.log('Edit request sent via WebSocket')
    }

    websocket.onmessage = (event) => {
      console.log('WebSocket message received:', event.data)
      const data = JSON.parse(event.data)

      if (data.type === 'processing') {
        console.log('Edit processing started')
      } else if (data.type === 'task_complete') {
        console.log('Edit complete, result length:', data.result?.length)
        setEnhancedPrompt(data.result)
        setOriginalEnhancedPrompt(data.result)
        setEditRequest('')
        requestAnimationFrame(() => resizeEnhancedTextarea())
        setIsEditLoading(false)
        setErrorMessage(data.is_fallback ? "Using fallback model due to HCAI service downtime." : null)
        websocket.close()
      } else if (data.type === 'user_question') {
        // Show dialog with user questions
        setUserQuestions(data.questions)
        setUserAnswers(new Array(data.questions.length).fill(''))
      } else if (data.type === 'task_error') {
        console.error('Edit error:', data.error)
        setErrorMessage(data.error)
        setIsEditLoading(false)
        websocket.close()
      }
    }

    websocket.onerror = (error) => {
      console.error('WebSocket error:', error)
      setIsEditLoading(false)
    }

    websocket.onclose = () => {
      console.log('WebSocket disconnected')
    }
  }

  const saveToLocalStorage = (currentTask: string, currentPrompt: string, result: string, taskId: string) => {
    const newEntry: SavedEntry = {
      id: Date.now(),
      task: currentTask,
      lazy_prompt: currentPrompt,
      enhanced_prompt: result,
      created_at: new Date().toLocaleString(),
      task_id: taskId
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
      setGoal(entry.task)
      setPrompt(entry.lazy_prompt)
      setEnhancedPrompt(entry.enhanced_prompt)
      setOriginalEnhancedPrompt(entry.enhanced_prompt)
      setSelectedEntry(String(id))
    }
  }

  const handleCopyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(enhancedPrompt)
      setCopySuccess(true)
      setTimeout(() => setCopySuccess(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  const handleSaveChanges = () => {
    if (!selectedEntry) return
    const id = parseInt(selectedEntry)
    const updatedEntries = savedEntries?.map(entry => 
      entry.id === id 
        ? { ...entry, enhanced_prompt: enhancedPrompt }
        : entry
    ) || []
    setSavedEntries(updatedEntries)
    localStorage.setItem('saved_prompts', JSON.stringify(updatedEntries))
    setOriginalEnhancedPrompt(enhancedPrompt)
  }

  const isEnhancedPromptModified = enhancedPrompt !== originalEnhancedPrompt && enhancedPrompt !== ''

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

      {/* Mobile Header */}
      <header className="mobile-header">
        <button 
          className="hamburger-btn"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          aria-label="Toggle menu"
        >
          <span className={`hamburger-icon ${mobileMenuOpen ? 'open' : ''}`}></span>
        </button>
        <h1 className="mobile-title">Prompt Enhance</h1>
      </header>

      {/* Mobile overlay */}
      {mobileMenuOpen && (
        <div 
          className="mobile-overlay" 
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      {/* Left Sidebar - History */}
      <aside className={`sidebar ${mobileMenuOpen ? 'open' : ''}`}>
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

        <button 
          className="sidebar-close-btn"
          onClick={() => setMobileMenuOpen(false)}
        >
          Close
        </button>
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
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
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
        <div className="enhanced-output-container">
          {enhancedPrompt && !isLoading && (
            <div className="enhanced-output-actions">
              <button 
                className="action-btn copy-btn" 
                onClick={handleCopyToClipboard}
                title="Copy to clipboard"
              >
                {copySuccess ? '✓ Copied' : <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="#ffffff"><g fill="none" stroke="#ffffff" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"><path d="M18.327 7.286h-8.044a1.932 1.932 0 0 0-1.925 1.938v10.088c0 1.07.862 1.938 1.925 1.938h8.044a1.932 1.932 0 0 0 1.925-1.938V9.224c0-1.07-.862-1.938-1.925-1.938"/><path d="M15.642 7.286V4.688c0-.514-.203-1.007-.564-1.37a1.918 1.918 0 0 0-1.361-.568H5.673c-.51 0-1 .204-1.36.568a1.945 1.945 0 0 0-.565 1.37v10.088c0 .514.203 1.007.564 1.37c.361.364.85.568 1.361.568h2.685"/></g></svg>}
              </button>
              {isEnhancedPromptModified && selectedEntry && (
                <button 
                  className="action-btn save-btn" 
                  onClick={handleSaveChanges}
                  title="Save changes"
                >
                  {/* Save icon (floppy disk) */}
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="#ffffff"><g fill="none" stroke="#ffffff" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"><path d="M21.25 9.16v7.987a4.1 4.1 0 0 1-1.204 2.901a4.113 4.113 0 0 1-2.906 1.202H6.86a4.113 4.113 0 0 1-2.906-1.202a4.1 4.1 0 0 1-1.204-2.901V6.853a4.1 4.1 0 0 1 1.204-2.901A4.113 4.113 0 0 1 6.86 2.75h8.35a3.004 3.004 0 0 1 2.25.998l3 3.415c.501.545.783 1.256.79 1.997"/><path d="M7 21.22v-5.241a1.995 1.995 0 0 1 2-1.997h6a2.002 2.002 0 0 1 2 1.997v5.241M15.8 2.81v4.183a1.526 1.526 0 0 1-1.52 1.528H9.72A1.531 1.531 0 0 1 8.2 6.993V2.75m1.946 15.108h3.708"/></g></svg>
                </button>
              )}
            </div>
          )}
          {isLoading ? (
            <pre className="enhanced-output">
              <div className="spinner-container">
                <div className="spinner"></div>
                <span>Enhancing your prompt...</span>
              </div>
            </pre>
          ) : 
            enhancedPrompt ? (
            <textarea
              className="enhanced-output enhanced-output-editable"
              value={enhancedPrompt}
              onChange={(e) => setEnhancedPrompt(e.target.value)}
              ref={enhancedTextareaRef}
            />
          ) : (
            <pre className="enhanced-output">
              Your enhanced prompt will appear here.
            </pre>
          )}
        </div>

        {/* Desktop Edit Request Input */}
        {enhancedPrompt && !isLoading && (
          <div className="edit-request-row">
            <input
              type="text"
              className="edit-request-input"
              placeholder="Request edits to the prompt..."
              value={editRequest}
              onChange={(e) => setEditRequest(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleEditRequest()}
              disabled={isEditLoading}
            />
            <button
              className={`edit-request-btn ${editRequest.trim() ? 'active' : ''}`}
              onClick={handleEditRequest}
              disabled={isEditLoading || !editRequest.trim()}
              title="Send edit request"
            >
              {isEditLoading ? (
                <div className="edit-spinner"></div>
              ) : (
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="22" y1="2" x2="11" y2="13"></line>
                  <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                </svg>
              )}
            </button>
          </div>
        )}
      </aside>

      {/* Mobile Sticky Edit Bar */}
      {enhancedPrompt && !isLoading && (
        <div className="mobile-edit-bar">
          <input
            type="text"
            className="mobile-edit-input"
            placeholder="Request edits..."
            value={editRequest}
            onChange={(e) => setEditRequest(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleEditRequest()}
            disabled={isEditLoading}
          />
          <button
            className={`mobile-edit-btn ${editRequest.trim() ? 'active' : ''}`}
            onClick={handleEditRequest}
            disabled={isEditLoading || !editRequest.trim()}
            title="Send edit request"
          >
            {isEditLoading ? (
              <div className="edit-spinner"></div>
            ) : (
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="22" y1="2" x2="11" y2="13"></line>
                <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
              </svg>
            )}
          </button>
        </div>
      )}

      <Analytics />
    </div>
  )
}

export default App
