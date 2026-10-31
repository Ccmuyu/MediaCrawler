import { Sun, Moon, Monitor } from 'lucide-react'
import { useThemeStore } from '@/store/themeStore'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

type Theme = 'light' | 'dark' | 'system'

const themes: { value: Theme; label: string; icon: typeof Sun }[] = [
  { value: 'light', label: 'Light', icon: Sun },
  { value: 'dark', label: 'Dark', icon: Moon },
  { value: 'system', label: 'Auto', icon: Monitor },
]

export function ThemeToggle() {
  const { theme, setTheme } = useThemeStore()

  const currentTheme = themes.find(t => t.value === theme) || themes[0]
  const Icon = currentTheme.icon

  return (
    <Select value={theme} onValueChange={(value: Theme) => setTheme(value)}>
      <SelectTrigger className="h-8 w-[108px] justify-start gap-1.5 rounded-full border-transparent bg-transparent px-2.5 text-xs text-cyber-text-secondary hover:bg-cyber-bg-tertiary">
        <Icon className="mr-1 h-3.5 w-3.5" />
        <SelectValue>{currentTheme.label}</SelectValue>
      </SelectTrigger>
      <SelectContent>
        {themes.map(({ value, label, icon: ItemIcon }) => (
          <SelectItem key={value} value={value} className="text-sm">
            <div className="flex items-center gap-2">
              <ItemIcon className="h-3.5 w-3.5" />
              {label}
            </div>
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}
