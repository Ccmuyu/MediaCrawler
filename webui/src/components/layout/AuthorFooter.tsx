import { useTranslation } from 'react-i18next'

const links = [
  { href: 'https://github.com/NanmiCoder', title: 'GitHub', src: '/logos/github.png' },
  { href: 'https://space.bilibili.com/434377496', title: '哔哩哔哩', src: '/logos/bilibili_logo.png' },
  { href: 'https://www.xiaohongshu.com/user/profile/5f58bd990000000001003753', title: '小红书', src: '/logos/xiaohongshu_logo.png' },
  { href: 'https://www.douyin.com/user/MS4wLjABAAAATJPY7LAlaa5X-c8uNdWkvz0jUGgpw4eeXIwu_8BhvqE', title: '抖音', src: '/logos/douyin.png' },
]

export function AuthorFooter() {
  const { t } = useTranslation('license')

  return (
    <footer className="flex h-14 shrink-0 items-center justify-between gap-4 border-t border-cyber-border-subtle bg-cyber-bg-panel px-5 sm:px-6">
      <div className="flex min-w-0 items-center gap-3">
        <img
          src="/logos/my_logo.png"
          alt={t('author.name')}
          className="h-8 w-8 shrink-0 rounded-full object-cover"
        />
        <div className="min-w-0">
          <div className="truncate text-sm text-cyber-text-primary">{t('author.name')}</div>
          <div className="hidden truncate text-xs text-cyber-text-muted sm:block">{t('author.slogan')}</div>
        </div>
      </div>

      <div className="flex items-center gap-1">
        {links.map((link) => (
          <a
            key={link.title}
            href={link.href}
            target="_blank"
            rel="noopener noreferrer"
            title={link.title}
            className="flex h-8 w-8 items-center justify-center rounded-full transition-colors hover:bg-cyber-bg-tertiary"
          >
            <img src={link.src} alt={link.title} className="h-4 w-4 object-contain" />
          </a>
        ))}
      </div>
    </footer>
  )
}
