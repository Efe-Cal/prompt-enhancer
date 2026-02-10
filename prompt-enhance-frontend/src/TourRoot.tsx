import { TourProvider } from '@reactour/tour'
import App from './App'
import { tourSteps, tourStyles } from './tourConfig'
import { useState } from 'react'

function rightPanelTourStart({setShow}: {setShow: (show: boolean) => void}) {
    setShow(true)
    // put data to be implemented
}

function rightPanelTourEnd({setShow}: {setShow: (show: boolean) => void}) {
    setShow(false)
    // put data to be implemented
}


export function Root() {
  const handleTourClose = () => {
    localStorage.setItem('tourCompleted', 'true')
  }

  const [showRightPanel, setShowRightPanel] = useState(false)

  const newTourSteps = tourSteps.map(step => {
    if (step.selector === ".enhanced-panel") {
        return {
            ...step,
            action: () => rightPanelTourStart({setShow: setShowRightPanel})
        }
    }
    else if (step.selector === ".edit-request-row") {
        return {
            ...step,
            action: () => rightPanelTourStart({setShow: setShowRightPanel}),
            actionAfter: () => rightPanelTourEnd({setShow: setShowRightPanel})
        }
    }
    return step
  })

  return (
    <TourProvider
      steps={newTourSteps}
      styles={tourStyles}
      onClickClose={({ setIsOpen }) => {
        setIsOpen(false)
        handleTourClose()
        // setShowRightPanel(false)
      }}
      padding={{ mask: 8, popover: [8, 12] }}
      showBadge={true}
      showDots={true}
      showNavigation={true}
      scrollSmooth={true}
    >
      <App showRightPanel={showRightPanel} />
    </TourProvider>
  )
}
