import * as React from 'react'
import { cn } from '@/lib/utils'
import { Check } from 'lucide-react'

export interface CheckboxProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  onCheckedChange?: (checked: boolean) => void
}

const Checkbox = React.forwardRef<HTMLInputElement, CheckboxProps>(
  ({ className, checked, onCheckedChange, ...props }, ref) => {
    return (
      <label className="inline-flex items-center cursor-pointer">
        <input
          type="checkbox"
          className="sr-only peer"
          ref={ref}
          checked={checked}
          onChange={(e) => onCheckedChange?.(e.target.checked)}
          {...props}
        />
        <div
          className={cn(
            'h-[18px] w-[18px] shrink-0 rounded-[5px] border border-cyber-border-DEFAULT bg-cyber-bg-primary focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-50 peer-checked:bg-cyber-neon-cyan peer-checked:border-cyber-neon-cyan flex items-center justify-center transition-colors',
            className
          )}
        >
          <Check className={cn('h-3 w-3 text-cyber-bg-primary transition-opacity', checked ? 'opacity-100' : 'opacity-0')} />
        </div>
      </label>
    )
  }
)
Checkbox.displayName = 'Checkbox'

export { Checkbox }
