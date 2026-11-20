import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { FolderOpen, RefreshCw, UserRound, Eye } from 'lucide-react'
import { dataApi, type DataCreator } from '@/lib/api'
import { FileCard } from './FileCard'
import { WorksGallery } from './WorksGallery'
import type { DataFile } from '@/types/crawler'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'

const CRAWL_MODES = ['creator', 'search', 'detail'] as const

function extractMode(file: DataFile): string {
  const folder = file.path.split(/[/\\]/)[1]?.toLowerCase()
  if (folder && (CRAWL_MODES as readonly string[]).includes(folder)) {
    return folder
  }
  const prefix = file.name.split('_')[0]?.toLowerCase()
  if (prefix && (CRAWL_MODES as readonly string[]).includes(prefix)) {
    return prefix
  }
  return 'other'
}

const PLATFORM_LABEL: Record<string, string> = {
  dy: 'Douyin',
  xhs: 'Xiaohongshu',
  ks: 'Kuaishou',
  bili: 'Bilibili',
  wb: 'Weibo',
}

function CreatorCard({ creator, onOpen }: { creator: DataCreator; onOpen: (creator: DataCreator) => void }) {
  const { t } = useTranslation('data')
  return (
    <Card
      role="button"
      tabIndex={0}
      className="cursor-pointer"
      onClick={() => onOpen(creator)}
      onKeyDown={(event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault()
          onOpen(creator)
        }
      }}
    >
      <CardContent className="p-4">
        <div className="flex items-start gap-3">
          {creator.avatar ? (
            <img
              src={dataApi.getMediaUrl(creator.avatar)}
              alt=""
              className="h-9 w-9 rounded-lg object-cover"
            />
          ) : (
            <div className="rounded-lg bg-cyber-bg-primary p-2 text-cyber-neon-cyan">
              <UserRound className="h-5 w-5" />
            </div>
          )}
          <div className="min-w-0 flex-1">
            <h3 className="truncate text-sm text-cyber-text-primary" title={creator.nickname}>
              {creator.nickname}
            </h3>
            <p className="mt-1 text-xs text-cyber-text-muted">
              {t('file.entries', { count: creator.work_count })}
            </p>
          </div>
        </div>
        <div className="mt-3 flex items-center justify-between border-t border-cyber-border-subtle pt-3">
          <Badge variant="outline">{PLATFORM_LABEL[creator.platform] || creator.platform}</Badge>
          <Button variant="ghost" size="sm" tabIndex={-1}>
            <Eye className="h-3 w-3" />
            {t('file.works')}
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

export function DataExplorer() {
  const { t } = useTranslation('data')
  const [activeTab, setActiveTab] = useState<string>('all')
  const [worksFile, setWorksFile] = useState<DataFile | null>(null)
  const [worksCreator, setWorksCreator] = useState<DataCreator | null>(null)

  const openWorks = (file: DataFile) => {
    setWorksFile(file)
  }

  const closeWorks = () => {
    setWorksFile(null)
    setWorksCreator(null)
  }

  const { data, isLoading, refetch, isRefetching } = useQuery({
    queryKey: ['dataFiles'],
    queryFn: async () => {
      const { data } = await dataApi.getFiles()
      return data.files
    },
  })
  const creatorsQuery = useQuery({
    queryKey: ['dataCreators'],
    queryFn: async () => {
      const { data } = await dataApi.getCreators()
      return data.creators
    },
  })

  const files = data || []
  const creators = creatorsQuery.data || []

  const groupedFiles = useMemo(() => {
    const grouped: Record<string, typeof files> = {}
    files.forEach(file => {
      const mode = extractMode(file)
      if (!grouped[mode]) grouped[mode] = []
      grouped[mode].push(file)
    })
    return grouped
  }, [files])

  const modes = CRAWL_MODES.filter(mode => mode === 'creator' ? creators.length > 0 : (groupedFiles[mode]?.length ?? 0) > 0)
  const showCreators = activeTab === 'all' || activeTab === 'creator'
  const displayFiles = activeTab === 'all' ? files : activeTab === 'creator' ? [] : (groupedFiles[activeTab] || [])
  const visibleCount = (showCreators ? creators.length : 0) + displayFiles.length

  if (worksCreator) {
    return <WorksGallery creator={worksCreator} onBack={closeWorks} />
  }

  if (worksFile) {
    return <WorksGallery file={worksFile} onBack={closeWorks} />
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <h2 className="font-serif text-xl text-cyber-text-primary">
            {t('explorer.title')}
          </h2>
          <Badge variant="default">
            {t('explorer.records', { count: visibleCount })}
          </Badge>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            refetch()
            creatorsQuery.refetch()
          }}
          disabled={isRefetching || creatorsQuery.isRefetching}
        >
          <RefreshCw className={`w-4 h-4 ${isRefetching ? 'animate-spin' : ''}`} />
          {t('explorer.rescan')}
        </Button>
      </div>

      {/* Category Tabs */}
      {(files.length > 0 || creators.length > 0) && (
        <div className="flex items-center gap-2 mb-4 flex-wrap">
          <button
            onClick={() => setActiveTab('all')}
            className={`rounded-full px-3 py-1.5 text-xs transition-colors ${
              activeTab === 'all'
                ? 'bg-cyber-neon-cyan text-cyber-bg-primary'
                : 'bg-cyber-bg-tertiary text-cyber-text-secondary hover:text-cyber-text-primary'
            }`}
          >
            {t('explorer.allCategories')} ({files.length + creators.length})
          </button>
          {modes.map(mode => (
            <button
              key={mode}
              onClick={() => setActiveTab(mode)}
              className={`rounded-full px-3 py-1.5 text-xs transition-colors ${
                activeTab === mode
                  ? 'bg-cyber-neon-cyan text-cyber-bg-primary'
                  : 'bg-cyber-bg-tertiary text-cyber-text-secondary hover:text-cyber-text-primary'
              }`}
            >
              {t(`explorer.mode.${mode}`)} ({mode === 'creator' ? creators.length : (groupedFiles[mode]?.length ?? 0)})
            </button>
          ))}
          {(groupedFiles.other?.length ?? 0) > 0 && (
            <button
              onClick={() => setActiveTab('other')}
              className={`rounded-full px-3 py-1.5 text-xs transition-colors ${
                activeTab === 'other'
                  ? 'bg-cyber-neon-cyan text-cyber-bg-primary'
                  : 'bg-cyber-bg-tertiary text-cyber-text-secondary hover:text-cyber-text-primary'
              }`}
            >
              {t('explorer.mode.other')} ({groupedFiles.other.length})
            </button>
          )}
        </div>
      )}

      {isLoading || creatorsQuery.isLoading ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-sm text-cyber-text-muted">
            {t('explorer.loading')}
          </div>
        </div>
      ) : files.length === 0 && creators.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center text-center">
          <FolderOpen className="mb-4 h-8 w-8 text-cyber-text-muted" />
          <h3 className="mb-2 font-serif text-lg text-cyber-text-primary">
            {t('explorer.noData')}
          </h3>
          <p className="max-w-md text-sm text-cyber-text-muted">
            {t('explorer.noDataHint')}
          </p>
        </div>
      ) : (
        <div className="min-h-0 flex-1 overflow-auto">
          {showCreators && creators.length > 0 && (
            <div className="mb-6">
              <h3 className="mb-3 text-sm text-cyber-text-secondary">
                {t('explorer.creators')} ({creators.length})
              </h3>
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                {creators.map((creator) => (
                  <CreatorCard
                    key={`${creator.platform}/${creator.creator_id}`}
                    creator={creator}
                    onOpen={setWorksCreator}
                  />
                ))}
              </div>
            </div>
          )}
          {displayFiles.length > 0 && (
            <div className="grid grid-cols-1 content-start gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {displayFiles.map((file) => (
                <FileCard key={file.path} file={file} onOpenWorks={openWorks} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
