import { Github } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useCrawlerStore } from '@/store/crawlerStore'
import { useCrawlerStatus } from '@/hooks/useCrawler'
import { LanguageSwitch } from './LanguageSwitch'
import { ThemeToggle } from './ThemeToggle'

interface SidebarProps {
  onShowDisclaimer?: () => void
}

export function Sidebar({ onShowDisclaimer }: SidebarProps) {
  const { t } = useTranslation()
  const status = useCrawlerStore((state) => state.status)

  useCrawlerStatus()

  const isRunning = status === 'running'

  return (
    <header className="z-10 flex h-16 shrink-0 items-center justify-between border-b border-cyber-border-subtle bg-cyber-bg-panel px-5 sm:px-6">
      <div className="flex min-w-0 items-center gap-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-md bg-cyber-neon-cyan font-serif text-sm text-cyber-bg-primary">
          M
        </div>
        <span className="font-serif text-[22px] leading-none tracking-tight text-cyber-text-primary">
          MediaCrawler
        </span>
        <span className="hidden items-center gap-2 rounded-full border border-cyber-border-subtle px-2.5 py-1 text-xs text-cyber-text-secondary sm:inline-flex">
          <span className={isRunning ? 'status-dot status-dot-online' : 'status-dot status-dot-offline'} />
          {isRunning ? t('status.running') : t('status.idle')}
        </span>
      </div>

      <div className="flex items-center gap-1 sm:gap-2">
        <button
          type="button"
          onClick={onShowDisclaimer}
          className="px-2 text-xs text-cyber-text-muted transition-colors hover:text-cyber-text-primary"
        >
          {t('sidebar.license')}
        </button>
        <a
          href="https://github.com/NanmiCoder/MediaCrawler"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex h-8 items-center gap-1.5 rounded-full px-2.5 text-xs text-cyber-text-secondary transition-colors hover:bg-cyber-bg-tertiary hover:text-cyber-text-primary"
        >
          <Github className="h-3.5 w-3.5" />
          <span className="hidden sm:inline">GitHub</span>
        </a>
        <ThemeToggle />
        <LanguageSwitch />
      </div>
    </header>
  )
}
