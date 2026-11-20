import type { DataFile } from '@/types/crawler'

const WORK_PLATFORMS = new Set([
  'xhs',
  'dy',
  'douyin',
  'ks',
  'kuaishou',
  'bili',
  'bilibili',
  'wb',
  'weibo',
])

/** 内容文件才进作品墙。评论、贴吧、知乎仍走表格。 */
export function isWorksFile(file: DataFile): boolean {
  const platform = file.path.split(/[/\\]/)[0]?.toLowerCase()
  const kind = file.name.split('_')[1]
  const type = file.type.toLowerCase()
  return (type === 'json' || type === 'jsonl') && kind === 'contents' && WORK_PLATFORMS.has(platform)
}
