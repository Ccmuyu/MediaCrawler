import type { ReactNode, KeyboardEvent } from 'react'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Play, Square, X } from 'lucide-react'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import { Checkbox } from '@/components/ui/checkbox'
import { Button } from '@/components/ui/button'
import { useCrawlerStore } from '@/store/crawlerStore'
import { usePlatforms, useConfigOptions, useStartCrawler, useStopCrawler } from '@/hooks/useCrawler'
import { ParsedIdList } from './ParsedIdList'

const areaClass =
  'min-h-[92px] w-full rounded-lg border border-cyber-border-DEFAULT bg-cyber-bg-primary px-3 py-2.5 text-sm leading-relaxed text-cyber-text-primary placeholder:text-cyber-text-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyber-text-primary/10 disabled:cursor-not-allowed disabled:opacity-50'

type SectionProps = {
  index: string
  title: string
  description: string
  children: ReactNode
}

function Section({ index, title, description, children }: SectionProps) {
  return (
    <section className="border-t border-cyber-border-subtle pt-7 first:border-t-0 first:pt-0">
      <header className="mb-4 flex items-baseline justify-between gap-4">
        <div>
          <h2 className="font-serif text-lg text-cyber-text-primary">{title}</h2>
          <p className="mt-0.5 text-xs text-cyber-text-muted">{description}</p>
        </div>
        <span className="font-mono text-[11px] tracking-[0.18em] text-cyber-text-muted">{index}</span>
      </header>
      <div className="space-y-4">{children}</div>
    </section>
  )
}

type FieldProps = {
  label: string
  hint?: string
  children: ReactNode
}

function Field({ label, hint, children }: FieldProps) {
  return (
    <div className="space-y-2">
      <div className="space-y-1">
        <Label>{label}</Label>
        {hint ? <p className="text-xs leading-relaxed text-cyber-text-muted">{hint}</p> : null}
      </div>
      {children}
    </div>
  )
}

type KeywordInputProps = {
  value: string
  onChange: (value: string) => void
  placeholder?: string
  disabled?: boolean
}

function KeywordInput({ value, onChange, placeholder, disabled }: KeywordInputProps) {
  const [inputValue, setInputValue] = useState('')
  const keywords = value ? value.split(',').map((k) => k.trim()).filter(Boolean) : []

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      const trimmed = inputValue.trim()
      if (trimmed && !keywords.includes(trimmed)) {
        onChange([...keywords, trimmed].join(','))
        setInputValue('')
      }
    }
  }

  const removeKeyword = (keywordToRemove: string) => {
    onChange(keywords.filter((k) => k !== keywordToRemove).join(','))
  }

  return (
    <div className="space-y-2">
      <Input
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled}
      />
      {keywords.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {keywords.map((keyword) => (
            <span
              key={keyword}
              className="inline-flex items-center gap-1.5 rounded-full bg-cyber-bg-tertiary px-2.5 py-1 text-xs text-cyber-text-primary"
            >
              {keyword}
              {!disabled && (
                <button
                  type="button"
                  onClick={() => removeKeyword(keyword)}
                  className="text-cyber-text-muted transition-colors hover:text-cyber-text-primary"
                >
                  <X className="h-3 w-3" />
                </button>
              )}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

function OptionRow({
  checked,
  onCheckedChange,
  disabled,
  title,
  hint,
}: {
  checked: boolean
  onCheckedChange: (checked: boolean) => void
  disabled?: boolean
  title: string
  hint?: string
}) {
  return (
    <div className="flex items-start gap-3 rounded-lg px-1 py-2 transition-colors hover:bg-cyber-bg-primary">
      <Checkbox checked={checked} onCheckedChange={onCheckedChange} disabled={disabled} className="mt-0.5" />
      <span className="min-w-0">
        <span className="block text-sm text-cyber-text-primary">{title}</span>
        {hint ? <span className="mt-0.5 block text-xs leading-relaxed text-cyber-text-muted">{hint}</span> : null}
      </span>
    </div>
  )
}

export function CrawlerConfigPanel() {
  const { t } = useTranslation('config')
  const config = useCrawlerStore((state) => state.config)
  const updateConfig = useCrawlerStore((state) => state.updateConfig)
  const status = useCrawlerStore((state) => state.status)

  const { data: platforms } = usePlatforms()
  const { data: options } = useConfigOptions()
  const { mutate: startCrawler, isPending: isStarting } = useStartCrawler()
  const { mutate: stopCrawler, isPending: isStopping } = useStopCrawler()

  const isDisabled = status === 'running' || status === 'stopping'
  const isRunning = status === 'running'
  const isBusy = isStarting || isStopping || status === 'stopping'

  return (
    <div className="flex h-full flex-col">
      <div className="min-h-0 flex-1 overflow-y-auto px-6 py-6">
        <div className="mb-7">
          <p className="text-xs text-cyber-text-muted">{t('panel.eyebrow')}</p>
          <h1 className="mt-1 font-serif text-[28px] leading-none text-cyber-text-primary">{t('panel.title')}</h1>
        </div>

        <div className="space-y-7">
          <Section
            index="01"
            title={t('section.targetMatrix.title')}
            description={t('section.targetMatrix.description')}
          >
            <Field label={t('field.platform')}>
              <Select
                value={config.platform}
                onValueChange={(value) => updateConfig({ platform: value })}
                disabled={isDisabled}
              >
                <SelectTrigger>
                  <SelectValue placeholder={t('field.platformPlaceholder')} />
                </SelectTrigger>
                <SelectContent>
                  {platforms?.map((platform) => (
                    <SelectItem key={platform.value} value={platform.value}>
                      {platform.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </Field>

            <div className="grid grid-cols-2 gap-3">
              <Field label={t('field.crawlType')}>
                <Select
                  value={config.crawler_type}
                  onValueChange={(value) => updateConfig({ crawler_type: value })}
                  disabled={isDisabled}
                >
                  <SelectTrigger>
                    <SelectValue placeholder={t('field.crawlTypePlaceholder')} />
                  </SelectTrigger>
                  <SelectContent>
                    {options?.crawler_types.map((type) => (
                      <SelectItem key={type.value} value={type.value}>
                        {type.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </Field>

              <Field label={t('field.startPage')}>
                <Input
                  type="number"
                  min={1}
                  value={config.start_page}
                  onChange={(e) => updateConfig({ start_page: parseInt(e.target.value) || 1 })}
                  disabled={isDisabled}
                />
              </Field>
            </div>

            {config.crawler_type === 'search' && (
              <Field label={t('field.keywords')} hint={t('field.keywordsHint')}>
                <KeywordInput
                  placeholder={t('field.keywordsPlaceholder')}
                  value={config.keywords}
                  onChange={(keywords) => updateConfig({ keywords })}
                  disabled={isDisabled}
                />
              </Field>
            )}

            {config.crawler_type === 'detail' && (
              <Field label={t('field.specifiedIds')} hint={t('field.specifiedIdsHint')}>
                <textarea
                  value={config.specified_ids}
                  onChange={(e) => updateConfig({ specified_ids: e.target.value })}
                  disabled={isDisabled}
                  placeholder={t(`field.specifiedIdsPlaceholder.${config.platform}`, t('field.specifiedIdsPlaceholder.default'))}
                  className={`${areaClass} font-mono text-xs`}
                />
                <ParsedIdList
                  value={config.specified_ids}
                  platform={config.platform}
                  type="detail"
                  disabled={isDisabled}
                />
                {config.platform === 'xhs' && (
                  <div className="rounded-lg bg-cyber-neon-orange/10 px-3 py-2.5 text-xs leading-relaxed text-cyber-text-secondary">
                    {t('warning.xhsToken')}
                  </div>
                )}
              </Field>
            )}

            {config.crawler_type === 'creator' && (
              <Field label={t('field.creatorIds')} hint={t('field.creatorIdsHint')}>
                <textarea
                  value={config.creator_ids}
                  onChange={(e) => updateConfig({ creator_ids: e.target.value })}
                  disabled={isDisabled}
                  placeholder={t(`field.creatorIdsPlaceholder.${config.platform}`, t('field.creatorIdsPlaceholder.default'))}
                  className={`${areaClass} font-mono text-xs`}
                />
                <ParsedIdList
                  value={config.creator_ids}
                  platform={config.platform}
                  type="creator"
                  disabled={isDisabled}
                />
                {config.platform === 'xhs' && (
                  <div className="rounded-lg bg-cyber-neon-orange/10 px-3 py-2.5 text-xs leading-relaxed text-cyber-text-secondary">
                    {t('warning.xhsToken')}
                  </div>
                )}
              </Field>
            )}
          </Section>

          <Section
            index="02"
            title={t('section.authMatrix.title')}
            description={t('section.authMatrix.description')}
          >
            <Field label={t('field.loginMethod')}>
              <Select
                value={config.login_type}
                onValueChange={(value) => updateConfig({ login_type: value })}
                disabled={isDisabled}
              >
                <SelectTrigger>
                  <SelectValue placeholder={t('field.loginMethodPlaceholder')} />
                </SelectTrigger>
                <SelectContent>
                  {options?.login_types.map((type) => (
                    <SelectItem key={type.value} value={type.value}>
                      {type.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </Field>

            {config.login_type === 'cookie' ? (
              <Field label={t('field.cookies')} hint={t('field.cookiesHint')}>
                <textarea
                  value={config.cookies}
                  onChange={(e) => updateConfig({ cookies: e.target.value })}
                  disabled={isDisabled}
                  placeholder={t('field.cookiesPlaceholder')}
                  className={`${areaClass} font-mono text-xs`}
                />
              </Field>
            ) : null}

            {config.login_type === 'cookie' && (config.platform === 'xhs' || config.platform === 'dy') ? (
              <div className="rounded-lg bg-cyber-neon-orange/10 px-3 py-2.5 text-xs leading-relaxed text-cyber-text-secondary">
                {t('warning.cookieSlider')}
              </div>
            ) : null}
          </Section>

          <Section
            index="03"
            title={t('section.outputConfig.title')}
            description={t('section.outputConfig.description')}
          >
            <Field label={t('field.saveFormat')}>
              <Select
                value={config.save_option}
                onValueChange={(value) => updateConfig({ save_option: value })}
                disabled={isDisabled}
              >
                <SelectTrigger>
                  <SelectValue placeholder={t('field.saveFormatPlaceholder')} />
                </SelectTrigger>
                <SelectContent>
                  {options?.save_options.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </Field>

            <div className="-mx-1">
              <OptionRow
                checked={config.enable_comments}
                onCheckedChange={(isChecked) => {
                  updateConfig({
                    enable_comments: isChecked,
                    enable_sub_comments: isChecked ? config.enable_sub_comments : false,
                  })
                }}
                disabled={isDisabled}
                title={t('field.commentExtraction')}
              />
              <OptionRow
                checked={config.enable_sub_comments}
                onCheckedChange={(checked) => updateConfig({ enable_sub_comments: checked })}
                disabled={isDisabled || !config.enable_comments}
                title={t('field.subComments')}
              />
              <OptionRow
                checked={config.enable_media}
                onCheckedChange={(checked) => updateConfig({ enable_media: checked })}
                disabled={isDisabled}
                title={t('field.downloadMedia')}
                hint={t('field.downloadMediaHint')}
              />
              <OptionRow
                checked={config.headless}
                onCheckedChange={(checked) => updateConfig({ headless: checked })}
                disabled={isDisabled}
                title={t('field.headlessMode')}
                hint={t('field.headlessModeHint')}
              />
            </div>
          </Section>
        </div>
      </div>

      <div className="shrink-0 border-t border-cyber-border-subtle bg-cyber-bg-panel px-6 py-4">
        {isRunning ? (
          <Button
            onClick={() => stopCrawler()}
            disabled={isBusy}
            variant="destructive"
            className="h-11 w-full text-sm tracking-wide"
          >
            <Square className="h-4 w-4" />
            {isStopping ? t('button.stopping') : t('button.terminate')}
          </Button>
        ) : (
          <Button
            onClick={() => startCrawler(config)}
            disabled={isBusy}
            className="h-11 w-full text-sm tracking-wide"
          >
            <Play className="h-4 w-4" />
            {isStarting ? t('button.initiating') : t('button.initiateScan')}
          </Button>
        )}
      </div>
    </div>
  )
}
