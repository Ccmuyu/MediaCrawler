import { useState, useEffect, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { ChevronDown, ChevronUp, Trash2, RefreshCw } from 'lucide-react'
import { TerminalLine } from './TerminalLine'
import { useCrawlerStore } from '@/store/crawlerStore'
import { Button } from '@/components/ui/button'
import { DataExplorerDialog } from '@/components/data/DataExplorerDialog'

export function Terminal() {
  const { t } = useTranslation('terminal')
  const [isCollapsed, setIsCollapsed] = useState(false)
  const logs = useCrawlerStore((state) => state.logs)
  const clearLogs = useCrawlerStore((state) => state.clearLogs)
  const restoreLogs = useCrawlerStore((state) => state.restoreLogs)
  const clearedAfterLogId = useCrawlerStore((state) => state.clearedAfterLogId)
  const status = useCrawlerStore((state) => state.status)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollRef.current && !isCollapsed) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [logs, isCollapsed])

  const statusLabel =
    status === 'running'
      ? t('header.active')
      : status === 'idle'
        ? t('footer.awaiting')
        : status

  return (
    <div className={`flex min-h-0 flex-col overflow-hidden rounded-2xl border border-[#2A2724] bg-[#171512] shadow-cyber-float transition-all duration-300 ${isCollapsed ? 'h-12 shrink-0' : 'h-full flex-1'}`}>
      <div className="flex shrink-0 items-center justify-between border-b border-white/10 bg-[#201E1B] px-4 py-3">
        <div className="flex items-center gap-3">
          <span className="font-serif text-base text-[#E7E1D6]">{t('header.title')}</span>
          <span className="text-xs text-[#8C857A]">{t('header.entries', { count: logs.length })}</span>
          {status === 'running' && (
            <span className="inline-flex items-center gap-1.5 text-xs text-[#8FBF9F]">
              <span className="h-1.5 w-1.5 rounded-full bg-[#8FBF9F]" />
              {t('header.active')}
            </span>
          )}
        </div>

        <div className="flex items-center gap-1">
          <DataExplorerDialog />

          {clearedAfterLogId !== null && (
            <Button
              variant="ghost"
              size="sm"
              onClick={restoreLogs}
              className="h-8 w-8 px-0 text-[#A39B90] hover:bg-white/5 hover:text-[#E7E1D6]"
              title={t('header.restore')}
            >
              <RefreshCw className="h-4 w-4" />
            </Button>
          )}

          <Button
            variant="ghost"
            size="sm"
            onClick={clearLogs}
            disabled={logs.length === 0}
            className="h-8 w-8 px-0 text-[#A39B90] hover:bg-white/5 hover:text-[#E7E1D6] disabled:opacity-30"
            title={t('header.clear')}
          >
            <Trash2 className="h-4 w-4" />
          </Button>

          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="h-8 w-8 px-0 text-[#A39B90] hover:bg-white/5 hover:text-[#E7E1D6]"
          >
            {isCollapsed ? <ChevronDown className="h-4 w-4" /> : <ChevronUp className="h-4 w-4" />}
          </Button>
        </div>
      </div>

      {!isCollapsed && (
        <>
          <div
            ref={scrollRef}
            className="terminal-scroll min-h-0 flex-1 overflow-auto bg-[#171512] p-5 font-mono text-[13px]"
          >
            {logs.length === 0 ? (
              <div className="flex h-full min-h-[140px] items-center">
                <div>
                  <p className="font-serif text-3xl text-[#E7E1D6]">{t('banner.systemInit')}</p>
                  <p className="mt-3 max-w-sm text-sm leading-relaxed text-[#A39B90]">{t('banner.configHint')}</p>
                </div>
              </div>
            ) : (
              <div className="space-y-1">
                {logs.map((log) => (
                  <TerminalLine key={log.id} log={log} />
                ))}
              </div>
            )}

            {status === 'running' && (
              <div className="mt-3 flex items-center gap-2 text-[#8FBF9F]">
                <span>›</span>
                <span className="inline-block h-4 w-1.5 bg-[#8FBF9F] cursor-blink" />
              </div>
            )}
          </div>

          <div className="flex shrink-0 items-center justify-end border-t border-white/10 bg-[#201E1B] px-4 py-2">
            <span className="text-[11px] tracking-[0.16em] text-[#8C857A]">{statusLabel}</span>
          </div>
        </>
      )}
    </div>
  )
}
