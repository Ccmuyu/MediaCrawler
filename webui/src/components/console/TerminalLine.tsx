import { cn } from '@/lib/utils'
import type { LogEntry } from '@/types/crawler'

interface TerminalLineProps {
  log: LogEntry
}

const levelConfig: Record<string, { text: string; mark: string }> = {
  info: { text: 'text-[#E7E1D6]', mark: 'text-[#C4B59A]' },
  success: { text: 'text-[#C9DDD0]', mark: 'text-[#8FBF9F]' },
  warning: { text: 'text-[#F0E2CC]', mark: 'text-[#E0B07A]' },
  error: { text: 'text-[#F3D4D0]', mark: 'text-[#E09A92]' },
  debug: { text: 'text-[#A39B90]', mark: 'text-[#8C857A]' },
}

const levelIcons: Record<string, string> = {
  info: 'INFO',
  success: 'OK',
  warning: 'WARN',
  error: 'ERR',
  debug: 'DBG',
}

export function TerminalLine({ log }: TerminalLineProps) {
  const config = levelConfig[log.level] || levelConfig.info

  return (
    <div className="flex gap-3 rounded px-1 py-0.5 font-mono text-xs leading-relaxed hover:bg-white/[0.03]">
      <span className="w-[72px] shrink-0 text-[#6F675E]">{log.timestamp}</span>
      <span className={cn('w-12 shrink-0', config.mark)}>{levelIcons[log.level]}</span>
      <span className={cn('min-w-0 break-all', config.text)}>{log.message}</span>
    </div>
  )
}
