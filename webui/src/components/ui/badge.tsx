import * as React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const badgeVariants = cva(
  'inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium transition-colors focus:outline-none',
  {
    variants: {
      variant: {
        default:
          'border-transparent bg-cyber-bg-tertiary text-cyber-text-primary',
        secondary:
          'border-cyber-border-DEFAULT bg-cyber-bg-tertiary text-cyber-text-secondary',
        destructive:
          'border-transparent bg-cyber-neon-pink/10 text-cyber-neon-pink',
        outline:
          'border-cyber-border-DEFAULT text-cyber-text-secondary',
        success:
          'border-transparent bg-cyber-neon-green/10 text-cyber-neon-green',
        warning:
          'border-transparent bg-cyber-neon-orange/10 text-cyber-neon-orange',
        idle:
          'border-cyber-border-DEFAULT bg-transparent text-cyber-text-muted',
        running:
          'border-transparent bg-cyber-neon-green/10 text-cyber-neon-green',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  )
}

export { Badge, badgeVariants }
