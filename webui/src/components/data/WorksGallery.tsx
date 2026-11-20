import { useEffect, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { ArrowLeft, ChevronLeft, ChevronRight, Play } from 'lucide-react'
import { dataApi, type DataCreator, type WorkItem } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent } from '@/components/ui/dialog'
import { useVideoSlot } from './useVideoSlot'
import type { DataFile } from '@/types/crawler'

const PAGE_SIZE = 24

interface WorksGalleryProps {
  file?: DataFile
  creator?: DataCreator
  onBack: () => void
}

export function WorksGallery({ file, creator, onBack }: WorksGalleryProps) {
  const { t } = useTranslation('data')
  const [offset, setOffset] = useState(0)
  const [selectedGlobal, setSelectedGlobal] = useState<number | null>(null)
  const title = creator?.nickname || file?.name || ''

  const { data, isLoading, error } = useQuery({
    queryKey: creator
      ? ['works', 'creator', creator.platform, creator.creator_id, offset]
      : ['works', file?.path, offset],
    queryFn: async () => {
      if (creator) {
        const { data } = await dataApi.getCreatorWorks(creator.platform, creator.creator_id, offset, PAGE_SIZE)
        return data
      }
      const { data } = await dataApi.getWorks(file?.path || '', offset, PAGE_SIZE)
      return data
    },
  })

  const total = data?.total ?? 0
  const page = Math.floor(offset / PAGE_SIZE) + 1
  const pages = Math.max(1, Math.ceil(total / PAGE_SIZE))
  const localIndex = selectedGlobal == null ? -1 : selectedGlobal - offset
  const selected = data && localIndex >= 0 && localIndex < data.items.length
    ? data.items[localIndex]
    : null

  const stepSelection = (delta: number) => {
    if (selectedGlobal == null) return
    const next = selectedGlobal + delta
    if (next < 0 || next >= total) return
    setSelectedGlobal(next)
    const nextOffset = Math.floor(next / PAGE_SIZE) * PAGE_SIZE
    if (nextOffset !== offset) setOffset(nextOffset)
  }

  return (
    <div className="relative flex h-full min-h-0 min-w-0 flex-col">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div className="flex min-w-0 items-center gap-2">
          <Button variant="outline" size="sm" onClick={onBack}>
            <ArrowLeft className="h-3.5 w-3.5" />
            {t('works.back')}
          </Button>
          <h2 className="truncate font-serif text-lg text-cyber-text-primary" title={title}>
            {title}
          </h2>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-cyber-text-muted">
            {t('works.page', { page, pages, total })}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={offset === 0}
            onClick={() => setOffset((current) => Math.max(0, current - PAGE_SIZE))}
          >
            {t('works.prev')}
          </Button>
          <Button
            variant="outline"
            size="sm"
            disabled={offset + PAGE_SIZE >= total}
            onClick={() => setOffset((current) => current + PAGE_SIZE)}
          >
            {t('works.next')}
          </Button>
        </div>
      </div>

      {isLoading ? (
        <div className="flex flex-1 items-center justify-center text-sm text-cyber-text-muted">
          {t('works.loading')}
        </div>
      ) : error ? (
        <div className="flex flex-1 items-center justify-center text-sm text-cyber-neon-pink">
          {t('works.error')}
        </div>
      ) : !data || data.items.length === 0 ? (
        <div className="flex flex-1 items-center justify-center text-sm text-cyber-text-muted">
          {t('works.empty')}
        </div>
      ) : (
        <div className="min-h-0 min-w-0 flex-1 overflow-x-hidden overflow-y-auto">
          <div className="grid grid-cols-[repeat(auto-fill,minmax(200px,1fr))] items-start gap-3">
          {data.items.map((item, index) => (
            <WorkCard
              key={`${item.id}-${offset + index}`}
              item={item}
              onOpen={() => setSelectedGlobal(offset + index)}
            />
          ))}
          </div>
        </div>
      )}

      <WorkLightbox
        open={selectedGlobal != null}
        item={selected}
        position={selectedGlobal == null ? 0 : selectedGlobal + 1}
        total={total}
        canPrev={selectedGlobal != null && selectedGlobal > 0}
        canNext={selectedGlobal != null && selectedGlobal + 1 < total}
        onClose={() => setSelectedGlobal(null)}
        onStep={stepSelection}
      />
    </div>
  )
}

function captureVideoFrame(video: HTMLVideoElement, setPoster: (value: string) => void) {
  if (!video.videoWidth || !video.videoHeight) return
  if (video.currentTime < 0.05 && video.duration > 0.2) return
  const width = Math.min(480, video.videoWidth)
  const height = Math.max(1, Math.round(video.videoHeight * (width / video.videoWidth)))
  const canvas = document.createElement('canvas')
  canvas.width = width
  canvas.height = height
  const context = canvas.getContext('2d')
  if (!context) return
  context.drawImage(video, 0, 0, width, height)
  video.pause()
  try {
    setPoster(canvas.toDataURL('image/jpeg', 0.72))
  } catch {
    // 画布读不出来时继续留着这个视频元素
  }
}

function WorkCard({ item, onOpen }: { item: WorkItem; onOpen: () => void }) {
  const { t } = useTranslation('data')
  const picture = item.cover || item.images[0] || null
  const frameOnly = !picture && Boolean(item.video)
  const rootRef = useRef<HTMLButtonElement>(null)
  const [visible, setVisible] = useState(false)
  const [poster, setPoster] = useState<string | null>(null)
  const showFrame = useVideoSlot(frameOnly && visible && !poster)

  useEffect(() => {
    if (!frameOnly || !rootRef.current) return
    const node = rootRef.current
    const observer = new IntersectionObserver(
      ([entry]) => setVisible(entry.isIntersecting),
      { rootMargin: '40px' },
    )
    observer.observe(node)
    return () => observer.disconnect()
  }, [frameOnly])

  return (
    <button
      ref={rootRef}
      type="button"
      onClick={onOpen}
      className="mb-3 block w-full break-inside-avoid overflow-hidden rounded-xl border border-cyber-border-subtle bg-cyber-bg-panel text-left"
    >
      {picture ? (
        <img
          src={dataApi.getMediaUrl(picture)}
          alt=""
          className="max-h-[480px] w-full object-cover"
        />
      ) : frameOnly ? (
        <div className="relative aspect-[3/4] bg-cyber-bg-primary">
          {poster ? (
            <img src={poster} alt="" className="h-full w-full object-cover" />
          ) : showFrame && item.video ? (
            <video
              muted
              playsInline
              preload="metadata"
              src={`${dataApi.getMediaUrl(item.video)}#t=0.1`}
              className="h-full w-full object-cover"
              onLoadedData={(event) => {
                const video = event.currentTarget
                if (video.currentTime < 0.1) {
                  video.currentTime = 0.1
                  return
                }
                captureVideoFrame(video, setPoster)
              }}
              onSeeked={(event) => captureVideoFrame(event.currentTarget, setPoster)}
            />
          ) : null}
          <Play className="absolute left-1/2 top-1/2 h-8 w-8 -translate-x-1/2 -translate-y-1/2 text-white/80" />
        </div>
      ) : (
        <div className="flex aspect-[3/4] items-end bg-cyber-bg-primary p-3">
          <span className="rounded-full bg-cyber-bg-tertiary px-2 py-0.5 text-[10px] text-cyber-text-secondary">
            {t('works.notDownloaded')}
          </span>
        </div>
      )}
      <div className="space-y-1 p-3">
        <p className="line-clamp-2 text-sm text-cyber-text-primary">{item.title || item.id}</p>
        <p className="truncate text-xs text-cyber-text-muted">
          {item.author}
          {item.stats.liked ? ` · ${t('works.liked', { count: item.stats.liked })}` : ''}
        </p>
      </div>
    </button>
  )
}

function WorkLightbox({
  open,
  item,
  position,
  total,
  canPrev,
  canNext,
  onClose,
  onStep,
}: {
  open: boolean
  item: WorkItem | null
  position: number
  total: number
  canPrev: boolean
  canNext: boolean
  onClose: () => void
  onStep: (delta: number) => void
}) {
  const { t } = useTranslation('data')

  useEffect(() => {
    if (!open) return
    const onKey = (event: KeyboardEvent) => {
      if (event.target instanceof HTMLVideoElement) return
      if (event.key === 'ArrowLeft' && canPrev) {
        event.preventDefault()
        onStep(-1)
      }
      if (event.key === 'ArrowRight' && canNext) {
        event.preventDefault()
        onStep(1)
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, canPrev, canNext, onStep])

  return (
    <Dialog open={open} onOpenChange={(value) => { if (!value) onClose() }}>
      <DialogContent className="h-[calc(100vh-1rem)] w-[calc(100vw-1rem)] max-w-none gap-0 overflow-hidden !bg-cyber-bg-panel/55 p-0 backdrop-blur-md">
        <div className="flex h-full min-h-0 flex-col md:flex-row">
          <div className="relative flex min-h-[240px] min-w-0 flex-1 items-center justify-center bg-black/20">
            <button
              type="button"
              aria-label={t('works.prevItem')}
              disabled={!canPrev}
              className="absolute left-3 top-1/2 z-10 -translate-y-1/2 rounded-full bg-cyber-bg-panel/80 p-2 disabled:opacity-30"
              onClick={() => onStep(-1)}
            >
              <ChevronLeft className="h-5 w-5" />
            </button>
            <button
              type="button"
              aria-label={t('works.nextItem')}
              disabled={!canNext}
              className="absolute right-3 top-1/2 z-10 -translate-y-1/2 rounded-full bg-cyber-bg-panel/80 p-2 disabled:opacity-30"
              onClick={() => onStep(1)}
            >
              <ChevronRight className="h-5 w-5" />
            </button>
            {item ? <WorkStage key={item.id} item={item} /> : (
              <p className="text-sm text-cyber-text-muted">{t('works.loading')}</p>
            )}
          </div>
          <aside className="w-full shrink-0 space-y-3 overflow-auto border-cyber-border-subtle bg-cyber-bg-panel/35 p-4 md:w-80 md:border-l">
            {item && (
              <>
                <p className="text-xs text-cyber-text-muted">{position} / {total}</p>
                <h3 className="font-serif text-lg text-cyber-text-primary">{item.title || item.id}</h3>
                {item.author && <p className="text-sm text-cyber-text-secondary">{item.author}</p>}
                <p className="text-xs text-cyber-text-muted">
                  {[
                    item.stats.liked ? t('works.liked', { count: item.stats.liked }) : '',
                    item.stats.comment ? t('works.comment', { count: item.stats.comment }) : '',
                    item.stats.collected ? t('works.collected', { count: item.stats.collected }) : '',
                  ].filter(Boolean).join(' · ')}
                </p>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" disabled={!canPrev} onClick={() => onStep(-1)}>
                    {t('works.prevItem')}
                  </Button>
                  <Button variant="outline" size="sm" disabled={!canNext} onClick={() => onStep(1)}>
                    {t('works.nextItem')}
                  </Button>
                </div>
                {item.source_url && (
                  <a
                    href={item.source_url}
                    target="_blank"
                    rel="noreferrer"
                    className="block text-sm text-cyber-text-primary underline-offset-4 hover:underline"
                  >
                    {t('works.openSource')}
                  </a>
                )}
              </>
            )}
          </aside>
        </div>
      </DialogContent>
    </Dialog>
  )
}

function WorkStage({ item }: { item: WorkItem }) {
  const { t } = useTranslation('data')
  const pictures = item.images.length > 0
    ? item.images
    : item.video
      ? []
      : item.cover
        ? [item.cover]
        : []
  const [imageIndex, setImageIndex] = useState(0)
  const [videoPath, setVideoPath] = useState(item.video)
  const picture = pictures[imageIndex]
  const showVideo = Boolean(videoPath) && pictures.length === 0

  return (
    <div className="flex h-full w-full items-center justify-center">
      {showVideo && videoPath ? (
        <video
          key={videoPath}
          controls
          autoPlay
          src={dataApi.getMediaUrl(videoPath)}
          className="max-h-full max-w-full"
        />
      ) : picture ? (
        <img src={dataApi.getMediaUrl(picture)} alt="" className="max-h-full max-w-full object-contain" />
      ) : (
        <p className="px-6 text-sm text-cyber-text-muted">{t('works.noLocal')}</p>
      )}
      {pictures.length > 1 && (
        <div className="absolute bottom-3 left-1/2 flex -translate-x-1/2 gap-2">
          <button
            type="button"
            className="rounded-full bg-cyber-bg-panel/80 p-2"
            onClick={() => setImageIndex((current) => (current - 1 + pictures.length) % pictures.length)}
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
          <button
            type="button"
            className="rounded-full bg-cyber-bg-panel/80 p-2"
            onClick={() => setImageIndex((current) => (current + 1) % pictures.length)}
          >
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      )}
      {item.videos.length > 1 && (
        <div className="absolute bottom-3 right-16 flex max-w-[40%] flex-wrap justify-end gap-1">
          {item.videos.map((video) => (
            <Button
              key={video.path}
              variant={video.path === videoPath ? 'default' : 'outline'}
              size="sm"
              onClick={() => setVideoPath(video.path)}
            >
              {video.stem}
            </Button>
          ))}
        </div>
      )}
    </div>
  )
}
