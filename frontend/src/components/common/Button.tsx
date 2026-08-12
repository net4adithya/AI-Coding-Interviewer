import React from 'react';
import { cn } from '@/utils/cn';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  children: React.ReactNode;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', children, ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          'inline-flex items-center justify-center rounded font-navigation transition-opacity focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-container disabled:pointer-events-none disabled:opacity-50',
          {
            'bg-primary-container text-white hover:opacity-90 font-semibold tracking-wide': variant === 'primary',
            'bg-surface-container-highest text-on-surface hover:opacity-90': variant === 'secondary',
            'border custom-border bg-surface-container-lowest hover:bg-surface-container-highest text-secondary': variant === 'outline',
            'bg-transparent hover:bg-surface-container-highest text-secondary': variant === 'ghost',
            'py-1.5 px-3 text-xs': size === 'sm',
            'py-2 px-4 text-sm': size === 'md',
            'py-3 px-6 text-base': size === 'lg',
          },
          className
        )}
        {...props}
      >
        {children}
      </button>
    );
  }
);
Button.displayName = 'Button';
