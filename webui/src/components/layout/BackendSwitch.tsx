import { useCallback, useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Loader2 } from 'lucide-react'

type BackendError = 'uv_not_found' | 'start_timeout' | 'start_failed' | 'stop_failed'

type BackendStatus = {
  available: boolean
  running: boolean
  starting: boolean
  stopping: boolean
  error: BackendError | null
  detail: string | null
}

const emptyStatus: BackendStatus = {
  available: false,
  running: false,
  starting: false,
  stopping: false,
  error: null,
  detail: null,
}

async function readStatus(): Promise<BackendStatus> {
  try {
    const response = await fetch('/dev/backend')
    if (!response.ok) return emptyStatus
    const body = (await response.json()) as Omit<BackendStatus, 'available'>
    if (typeof body.running !== 'boolean') return emptyStatus
    return { ...body, available: true }
  } catch {
    return emptyStatus
  }
}

async function sendAction(action: 'start' | 'stop'): Promise<BackendStatus> {
  const response = await fetch(`/dev/backend/${action}`, { method: 'POST' })
  const body = (await response.json()) as Omit<BackendStatus, 'available'>
  return { ...body, available: true }
}

interface BackendSwitchProps {
  onRunningChange?: (running: boolean) => void
}

export function BackendSwitch({ onRunningChange }: BackendSwitchProps) {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const [status, setStatus] = useState<BackendStatus>(emptyStatus)
  const [pending, setPending] = useState<'start' | 'stop' | null>(null)
  const wasRunning = useRef(false)

  const refresh = useCallback(async () => {
    const next = await readStatus()
    setStatus(next)
    return next
  }, [])

  useEffect(() => {
    void refresh()
    const timer = window.setInterval(() => {
      void refresh()
    }, 3000)
    return () => window.clearInterval(timer)
  }, [refresh])

  useEffect(() => {
    if (status.running && !wasRunning.current) {
      void queryClient.invalidateQueries({ queryKey: ['platforms'] })
      void queryClient.invalidateQueries({ queryKey: ['configOptions'] })
      void queryClient.invalidateQueries({ queryKey: ['crawlerStatus'] })
    }
    wasRunning.current = status.running
  }, [queryClient, status.running])

  if (!status.available && !pending) return null

  const busy = pending !== null || status.starting || status.stopping
  const running = pending === 'start' ? false : pending === 'stop' ? true : status.running
  const label = pending === 'start' || status.starting
    ? t('backend.starting')
    : pending === 'stop' || status.stopping
      ? t('backend.stopping')
      : running
        ? t('backend.running')
        : t('backend.stopped')

  const toggle = async () => {
    if (busy) return
    const action = running ? 'stop' : 'start'
    setPending(action)
    try {
      const next = await sendAction(action)
      setStatus(next)
      if (next.error) {
        toast.error(t(`backend.${next.error}`), {
          description: next.detail ? next.detail.slice(-300) : undefined,
        })
      } else if (next.running) {
        onRunningChange?.(true)
      } else {
        onRunningChange?.(false)
      }
    } catch {
      toast.error(t(action === 'start' ? 'backend.start_failed' : 'backend.stop_failed'))
    } finally {
      setPending(null)
      void refresh()
    }
  }

  return (
    <button
      type="button"
      role="switch"
      aria-checked={running}
      aria-label={t('backend.label')}
      disabled={busy}
      onClick={() => void toggle()}
      className="inline-flex h-8 items-center gap-2 rounded-full border border-cyber-border-subtle bg-cyber-bg-primary px-2.5 text-xs text-cyber-text-secondary transition-colors hover:text-cyber-text-primary disabled:cursor-wait disabled:opacity-70"
    >
      <span className="hidden sm:inline">{t('backend.label')}</span>
      <span
        className={`relative h-4 w-7 shrink-0 rounded-full transition-colors ${
          running ? 'bg-cyber-neon-green' : 'bg-cyber-bg-tertiary'
        }`}
      >
        <span
          className={`absolute top-0.5 h-3 w-3 rounded-full bg-cyber-bg-panel shadow-sm transition-all ${
            running ? 'left-3.5' : 'left-0.5'
          }`}
        />
      </span>
      {busy ? <Loader2 className="h-3 w-3 animate-spin" /> : null}
      <span className="text-cyber-text-muted">{label}</span>
    </button>
  )
}
