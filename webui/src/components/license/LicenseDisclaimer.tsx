import { useTranslation } from 'react-i18next'
import { ShieldAlert, ExternalLink } from 'lucide-react'
import { Button } from '@/components/ui/button'

const LICENSE_KEY = 'mediacrawler_license_accepted'

// 检查是否已经接受协议
export function isLicenseAccepted(): boolean {
  return localStorage.getItem(LICENSE_KEY) === 'true'
}

// 清除协议接受状态
export function clearLicenseAccepted(): void {
  localStorage.removeItem(LICENSE_KEY)
}

interface LicenseDisclaimerProps {
  onAccept: () => void
}

export function LicenseDisclaimer({ onAccept }: LicenseDisclaimerProps) {
  const { t } = useTranslation('license')

  const handleConfirm = () => {
    localStorage.setItem(LICENSE_KEY, 'true')
    onAccept()
  }

  const handleDecline = () => {
    // 尝试关闭当前标签页（不会关闭整个浏览器，只关闭当前tab）
    try {
      // 方式1: 直接关闭当前标签页
      window.close()

      // 方式2: 将当前标签页导航到空白页
      setTimeout(() => {
        window.location.href = 'about:blank'
      }, 100)
    } catch {
      // 忽略错误
    }

    // 如果无法关闭（浏览器安全限制），显示拒绝访问页面
    setTimeout(() => {
      document.body.innerHTML = `
        <div style="
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          height: 100vh;
          background: #F3F0EA;
          color: #1C1917;
          font-family: 'Noto Sans SC', 'PingFang SC', sans-serif;
          text-align: center;
          padding: 20px;
        ">
          <div style="font-size: 28px; font-weight: 500; margin-bottom: 12px; font-family: 'Noto Serif SC', serif;">访问已拒绝</div>
          <div style="font-size: 14px; color: #8A8378;">您未同意使用条款，请关闭此标签页</div>
        </div>
      `
    }, 200)
  }

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center overflow-y-auto bg-[#1C1917]/45 px-4 py-8 backdrop-blur-[2px]">
      <div className="relative w-full max-w-xl rounded-2xl border border-cyber-border-subtle bg-cyber-bg-panel p-8 shadow-cyber-elevated">
        <div className="mb-6 flex items-start gap-3">
          <ShieldAlert className="mt-1 h-5 w-5 shrink-0 text-cyber-neon-orange" />
          <div>
            <h2 className="font-serif text-2xl text-cyber-text-primary">{t('title')}</h2>
            <p className="mt-2 text-sm text-cyber-text-secondary">{t('warning')}</p>
          </div>
        </div>

        <ol className="mb-6 space-y-3 text-sm leading-relaxed text-cyber-text-primary">
          <li className="flex gap-3"><span className="font-serif text-cyber-text-muted">01</span><span>{t('content.line1')}</span></li>
          <li className="flex gap-3"><span className="font-serif text-cyber-text-muted">02</span><span>{t('content.line2')}</span></li>
          <li className="flex gap-3"><span className="font-serif text-cyber-text-muted">03</span><span>{t('content.line3')}</span></li>
          <li className="flex gap-3"><span className="font-serif text-cyber-text-muted">04</span><span>{t('content.line4')}</span></li>
        </ol>

        <a
          href="https://github.com/NanmiCoder/MediaCrawler/blob/main/LICENSE"
          target="_blank"
          rel="noopener noreferrer"
          className="mb-6 inline-flex items-center gap-1.5 text-sm text-cyber-text-secondary underline-offset-4 hover:text-cyber-text-primary hover:underline"
        >
          <ExternalLink className="h-4 w-4" />
          {t('license')}
        </a>

        <div className="flex gap-3">
          <Button onClick={handleDecline} variant="outline" className="flex-1">
            {t('decline')}
          </Button>
          <Button onClick={handleConfirm} className="flex-1">
            {t('confirm')}
          </Button>
        </div>
      </div>
    </div>
  )
}
