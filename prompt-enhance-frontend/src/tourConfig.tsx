import type { StepType } from '@reactour/tour'

export const generateTourSteps = (setShowRightPanel: (show: boolean) => void): StepType[] => [
  {
    selector: window.innerWidth < 768 ? '.mobile-title' : '.main-title',
    content: (
      <div>
        <h3 style={{ margin: '0 0 8px 0', color: '#4a3728' }}>Welcome to Prompt Enhance!</h3>
        <p style={{ margin: 0, color: '#5d4a3a' }}>
          Transform your rough ideas into powerful, detailed prompts for any AI model.
        </p>
      </div>
    ),
  },
  {
    selector: '#task',
    content: (
      <div>
        <h3 style={{ margin: '0 0 8px 0', color: '#4a3728' }}>Define Your Goal</h3>
        <p style={{ margin: 0, color: '#5d4a3a' }}>
          Start by describing what you want to accomplish. This helps guide the enhancement.
        </p>
      </div>
    ),
  },
  {
    selector: '#prompt',
    content: (
      <div>
        <h3 style={{ margin: '0 0 8px 0', color: '#4a3728' }}>Your Prompt</h3>
        <p style={{ margin: 0, color: '#5d4a3a' }}>
          Paste your rough draft prompt here. Don't worry if it's messy — we'll enhance it!
        </p>
      </div>
    ),
  },
  {
    selector: '.web-search-section',
    content: (
      <div>
        <h3 style={{ margin: '0 0 8px 0', color: '#4a3728' }}>Web Search</h3>
        <p style={{ margin: 0, color: '#5d4a3a' }}>
          Enable this to gather real-time context from the web for more informed prompts.
        </p>
      </div>
    ),
  },
  {
    selector: '.prompt-style-section',
    resizeObservables: ['.prompt-style-section', '.prompt-style-content'],
    content: (
      <div>
        <h3 style={{ margin: '0 0 8px 0', color: '#4a3728' }}>Prompt Style</h3>
        <p style={{ margin: 0, color: '#5d4a3a' }}>
          Customize formatting, length, and prompting techniques.
        </p>
      </div>
    ),
    action: () => {
        const promptStyleSectionButton = document.querySelector('.prompt-style-header') as HTMLSelectElement
        if(promptStyleSectionButton){
            promptStyleSectionButton.click()
        }
    },
    actionAfter: () => {
        const promptStyleSectionButton = document.querySelector('.prompt-style-header') as HTMLSelectElement
        if(promptStyleSectionButton){
            promptStyleSectionButton.click()
        }
    }
  },
  {
    selector: '.model-selector',
    content: (
      <div>
        <h3 style={{ margin: '0 0 8px 0', color: '#4a3728' }}>Target Model</h3>
        <p style={{ margin: 0, color: '#5d4a3a' }}>
          Choose which AI model you're writing for. The prompt will be optimized accordingly.
        </p>
      </div>
    ),
  },
  {
    selector: '.enhance-btn',
    content: (
      <div>
        <h3 style={{ margin: '0 0 8px 0', color: '#4a3728' }}>Enhance!</h3>
        <p style={{ margin: 0, color: '#5d4a3a' }}>
          Click this button to transform your prompt using AI. The magic happens here.
        </p>
      </div>
    ),
  },
  {
    selector: '.enhanced-panel',
    content: (
      <div>
        <h3 style={{ margin: '0 0 8px 0', color: '#4a3728' }}>Enhanced Result</h3>
        <p style={{ margin: 0, color: '#5d4a3a' }}>
          Your polished prompt appears here. Copy it with one click or refine it further.
        </p>
      </div>
    ),
    action: () => setShowRightPanel(true),
  },
  {
    selector: window.innerWidth < 768 ? '.mobile-edit-bar' : '.edit-request-row',
    content: (
      <div>
        <h3 style={{ margin: '0 0 8px 0', color: '#4a3728' }}>Refine Your Prompt</h3>
        <p style={{ margin: 0, color: '#5d4a3a' }}>
          Not perfect? Request specific changes here and the AI will iterate on the result.
        </p>
      </div>
    ),
    action: () => setShowRightPanel(true),
    actionAfter: () => setShowRightPanel(false),
    resizeObservables: [window.innerWidth < 768 ? '.mobile-edit-bar' : '.edit-request-row']
  },
  {
    selector: window.innerWidth < 768 ? '.hamburger-btn' : '.sidebar',
    content: (
      <div>
        <h3 style={{ margin: '0 0 8px 0', color: '#4a3728' }}>History</h3>
        <p style={{ margin: 0, color: '#5d4a3a' }}>
          All your enhanced prompts are saved here. Click any entry to load it again.
        </p>
      </div>
    ),
  },
]

export const tourStyles = {
  popover: (base: object) => ({
    ...base,
    backgroundColor: '#f5efe6',
    borderRadius: '12px',
    boxShadow: '0 8px 32px rgba(74, 55, 40, 0.25)',
    border: '2px solid #b8956c',
    padding: '20px',
    maxWidth: '320px',
  }),
  maskArea: (base: object) => ({
    ...base,
    rx: 8,
  }),
  maskWrapper: (base: object) => ({
    ...base,
    color: 'rgba(74, 55, 40, 0.5)',
  }),
  badge: (base: object) => ({
    ...base,
    backgroundColor: '#b8956c',
    color: '#fff',
    fontWeight: 600,
  }),
  controls: (base: object) => ({
    ...base,
    marginTop: '16px',
  }),
  close: (base: object) => ({
    ...base,
    color: '#4a3728',
    width: '12px',
    height: '12px',
    right: '12px',
    top: '12px',
  }),
  arrow: (base: object) => ({
    ...base,
    // color: '#f5efe6',
  }),
  dot: (base: object, state?: { current?: boolean }) => ({
    ...base,
    backgroundColor: state?.current ? '#b8956c' : '#e8dcc8',
    border: 'none',
  }),
}

// Button styles for tour navigation
export const tourButtonStyles = {
  backgroundColor: '#b8956c',
  color: '#fff',
  border: 'none',
  borderRadius: '8px',
  padding: '8px 16px',
  fontWeight: 600,
  cursor: 'pointer',
  fontSize: '14px',
  transition: 'background-color 0.2s ease',
}
