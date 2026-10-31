import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { FileJson, FileSpreadsheet, FileText, Download, Eye } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { dataApi } from '@/lib/api'
import { formatFileSize, formatDateTime } from '@/lib/utils'
import { DataPreviewDialog } from './preview/DataPreviewDialog'
import type { DataFile } from '@/types/crawler'

interface FileCardProps {
  file: DataFile
}

const fileIcons: Record<string, typeof FileJson> = {
  json: FileJson,
  csv: FileSpreadsheet,
  xlsx: FileSpreadsheet,
  xls: FileSpreadsheet,
}

const fileStyles: Record<string, { icon: string; badge: string }> = {
  json: {
    icon: 'text-cyber-neon-yellow',
    badge: 'border-transparent bg-cyber-neon-yellow/10 text-cyber-neon-yellow'
  },
  csv: {
    icon: 'text-cyber-neon-green',
    badge: 'border-transparent bg-cyber-neon-green/10 text-cyber-neon-green'
  },
  xlsx: {
    icon: 'text-cyber-text-secondary',
    badge: 'border-transparent bg-cyber-bg-tertiary text-cyber-text-secondary'
  },
  xls: {
    icon: 'text-cyber-text-secondary',
    badge: 'border-transparent bg-cyber-bg-tertiary text-cyber-text-secondary'
  },
}

export function FileCard({ file }: FileCardProps) {
  const { t } = useTranslation('data')
  const [previewOpen, setPreviewOpen] = useState(false)

  const Icon = fileIcons[file.type] || FileText
  const styles = fileStyles[file.type] || {
    icon: 'text-cyber-text-muted',
    badge: 'border-transparent bg-cyber-bg-tertiary text-cyber-text-secondary'
  }

  // 检查是否支持预览
  const isPreviewable = ['json', 'csv', 'xlsx', 'xls'].includes(file.type.toLowerCase())

  const handleDownload = () => {
    const url = dataApi.getDownloadUrl(file.path)
    window.open(url, '_blank')
  }

  return (
    <>
      <Card className="group">
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <div className={`rounded-lg bg-cyber-bg-primary p-2 ${styles.icon}`}>
              <Icon className="h-5 w-5" />
            </div>
            <div className="min-w-0 flex-1">
              <h3 className="truncate text-sm text-cyber-text-primary" title={file.name}>
                {file.name}
              </h3>
              <p className="mt-1 text-xs text-cyber-text-muted">
                {formatFileSize(file.size)}
                {file.record_count !== null && (
                  <span> · {t('file.entries', { count: file.record_count })}</span>
                )}
              </p>
              <p className="mt-1 text-xs text-cyber-text-muted">
                {formatDateTime(file.modified_at)}
              </p>
            </div>
          </div>

          <div className="mt-3 flex items-center justify-between border-t border-cyber-border-subtle pt-3">
            <Badge variant="outline" className={styles.badge}>
              {file.type.toUpperCase()}
            </Badge>
            <div className="flex gap-1">
              {isPreviewable && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setPreviewOpen(true)}
                >
                  <Eye className="h-3 w-3" />
                  {t('file.preview')}
                </Button>
              )}
              <Button
                variant="ghost"
                size="sm"
                onClick={handleDownload}
              >
                <Download className="h-3 w-3" />
                {t('file.extract')}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 预览对话框 */}
      {isPreviewable && (
        <DataPreviewDialog
          file={file}
          open={previewOpen}
          onOpenChange={setPreviewOpen}
        />
      )}
    </>
  )
}
