import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { CheckCircle, XCircle, Loader2, RefreshCw, AlertTriangle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { envApi, EnvCheckResult } from '@/lib/api'

const ENV_CHECK_KEY = 'mediacrawler_env_checked'

interface EnvironmentCheckProps {
  onCheckComplete: (success: boolean) => void
}

// 检查是否已经通过环境检测
export function isEnvChecked(): boolean {
  return localStorage.getItem(ENV_CHECK_KEY) === 'true'
}

// 清除环境检测状态
export function clearEnvCheck(): void {
  localStorage.removeItem(ENV_CHECK_KEY)
}

export function EnvironmentCheck({ onCheckComplete }: EnvironmentCheckProps) {
  const { t } = useTranslation('env')
  const [status, setStatus] = useState<'checking' | 'success' | 'error'>('checking')
  const [result, setResult] = useState<EnvCheckResult | null>(null)
  const [showDetails, setShowDetails] = useState(false)

  const checkEnvironment = async () => {
    setStatus('checking')
    setResult(null)
    try {
      const response = await envApi.check()
      setResult(response.data)
      if (response.data.success) {
        setStatus('success')
        // 存储到 localStorage
        localStorage.setItem(ENV_CHECK_KEY, 'true')
        // 成功后延迟关闭
        setTimeout(() => onCheckComplete(true), 1500)
      } else {
        setStatus('error')
      }
    } catch (error) {
      setResult({
        success: false,
        message: t('defaultError'),
        error: t('defaultErrorHint')
      })
      setStatus('error')
    }
  }

  useEffect(() => {
    checkEnvironment()
  }, [])

  const handleSkip = () => {
    localStorage.setItem(ENV_CHECK_KEY, 'true')
    onCheckComplete(false)
  }

  const handleRetry = () => {
    checkEnvironment()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#1C1917]/45 px-4 backdrop-blur-[2px]">
      <div className="relative w-full max-w-md rounded-2xl border border-cyber-border-subtle bg-cyber-bg-panel p-7 shadow-cyber-elevated">
        <div className="mb-5 flex items-center gap-3">
          <AlertTriangle className="h-5 w-5 text-cyber-neon-orange" />
          <h2 className="font-serif text-2xl text-cyber-text-primary">{t('title')}</h2>
        </div>

        <div className="mb-4 rounded-xl bg-cyber-bg-primary px-4 py-3.5">
          <div className="flex items-center gap-3">
            {status === 'checking' && (
              <>
                <Loader2 className="h-4 w-4 animate-spin text-cyber-text-secondary" />
                <span className="text-sm text-cyber-text-primary">{t('scanning')}</span>
              </>
            )}
            {status === 'success' && (
              <>
                <CheckCircle className="h-4 w-4 text-cyber-neon-green" />
                <span className="text-sm text-cyber-neon-green">{t('success', { message: result?.message })}</span>
              </>
            )}
            {status === 'error' && (
              <>
                <XCircle className="h-4 w-4 text-cyber-neon-pink" />
                <span className="text-sm text-cyber-neon-pink">{t('error', { message: result?.message })}</span>
              </>
            )}
          </div>

          {status === 'error' && result?.error && (
            <div className="mt-3">
              <button
                onClick={() => setShowDetails(!showDetails)}
                className="text-sm text-cyber-text-secondary underline-offset-4 hover:text-cyber-text-primary hover:underline"
              >
                {showDetails ? t('hideDetails') : t('showDetails')}
              </button>
              {showDetails && (
                <pre className="mt-2 overflow-x-auto whitespace-pre-wrap rounded-lg bg-[#171512] p-3 font-mono text-xs text-[#E7E1D6]">
                  {result.error}
                </pre>
              )}
            </div>
          )}
        </div>

        {status === 'error' && (
          <div className="mb-5 space-y-2 text-sm text-cyber-text-secondary">
            <p>{t('requirements')}</p>
            <ol className="list-decimal space-y-1 pl-5 text-cyber-text-muted">
              <li>{t('requirementsList.1')}</li>
              <li>{t('requirementsList.2')}</li>
              <li>{t('requirementsList.3')}</li>
            </ol>
          </div>
        )}

        <div className="flex gap-3">
          {status === 'error' && (
            <>
              <Button variant="outline" className="flex-1" onClick={handleSkip}>
                {t('skipCheck')}
              </Button>
              <Button className="flex-1" onClick={handleRetry}>
                <RefreshCw className="h-4 w-4" />
                {t('retryCheck')}
              </Button>
            </>
          )}
          {status === 'checking' && (
            <Button variant="outline" className="w-full" onClick={handleSkip}>
              {t('skipCheck')}
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}
