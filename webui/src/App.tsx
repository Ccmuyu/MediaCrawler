import { useState } from 'react'
import { Toaster } from 'sonner'
import { Sidebar } from '@/components/layout/Sidebar'
import { MainContent } from '@/components/layout/MainContent'
import { AuthorFooter } from '@/components/layout/AuthorFooter'
import { CrawlerConfigPanel } from '@/components/config/CrawlerConfigPanel'
import { EnvironmentCheck, isEnvChecked } from '@/components/env/EnvironmentCheck'
import { LicenseDisclaimer, isLicenseAccepted } from '@/components/license/LicenseDisclaimer'

function App() {
  const [licenseAccepted, setLicenseAccepted] = useState(() => isLicenseAccepted())
  const [envChecked, setEnvChecked] = useState(() => isEnvChecked())
  const [showDisclaimer, setShowDisclaimer] = useState(false)

  const handleEnvCheckComplete = () => {
    setEnvChecked(true)
  }

  const handleLicenseAccept = () => {
    setLicenseAccepted(true)
    setShowDisclaimer(false)
  }

  const handleShowDisclaimer = () => {
    setShowDisclaimer(true)
  }

  return (
    <div className="cyber-grid flex h-screen flex-col overflow-hidden">
      {(!licenseAccepted || showDisclaimer) && (
        <LicenseDisclaimer onAccept={handleLicenseAccept} />
      )}

      {licenseAccepted && !showDisclaimer && !envChecked && (
        <EnvironmentCheck onCheckComplete={handleEnvCheckComplete} />
      )}

      <Sidebar onShowDisclaimer={handleShowDisclaimer} />

      <div className="grid min-h-0 flex-1 grid-cols-1 grid-rows-[minmax(280px,1.05fr)_minmax(220px,0.95fr)] lg:grid-cols-[minmax(360px,420px)_minmax(0,1fr)] lg:grid-rows-1">
        <div className="flex h-full min-h-0 flex-col overflow-hidden border-b border-cyber-border-subtle bg-cyber-bg-panel lg:border-b-0 lg:border-r">
          <CrawlerConfigPanel />
        </div>
        <div className="flex min-h-0 flex-col p-3 sm:p-4 lg:p-5">
          <MainContent />
        </div>
      </div>

      <AuthorFooter />

      <Toaster
        position="top-right"
        toastOptions={{
          className: 'border border-cyber-border-subtle bg-cyber-bg-panel text-cyber-text-primary shadow-cyber-float',
        }}
      />
    </div>
  )
}

export default App
