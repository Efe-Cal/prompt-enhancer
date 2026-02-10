import { TourProvider } from '@reactour/tour'
import App from './App'
import { generateTourSteps, tourStyles } from './tourConfig'
import { useState } from 'react'


export function Root() {
  const handleTourClose = () => {
    localStorage.setItem('tourCompleted', 'true')
  }

  const [showRightPanel, setShowRightPanel] = useState(false)

//   const newTourSteps = tourSteps.map(step => {
//     if (step.selector === ".enhanced-panel") {
//         return {
//             ...step,
//             action: () => rightPanelTourStart({setShow: setShowRightPanel})
//         }
//     }
//     else if (step.selector === ".edit-request-row") {
//         return {
//             ...step,
//             action: () => rightPanelTourStart({setShow: setShowRightPanel}),
//             actionAfter: () => rightPanelTourEnd({setShow: setShowRightPanel})
//         }
//     }
//     return step
//   })

  return (
    <TourProvider
      steps={generateTourSteps(setShowRightPanel)}
      styles={tourStyles}
      onClickClose={({ setIsOpen }) => {
        setIsOpen(false)
        handleTourClose()
        setShowRightPanel(false)
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
