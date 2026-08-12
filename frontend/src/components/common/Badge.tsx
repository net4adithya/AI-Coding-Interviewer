import React from 'react';
import { cn } from '@/utils/cn';

interface BadgeProps {
  variant?: 'active' | 'draft' | 'completed' | 'warning' | 'info';
  children: React.ReactNode;
  className?: string;
}

export function Badge({ variant = 'active', children, className }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border',
        {
          'bg-surface-container-highest text-primary-container border-surface-variant': variant === 'active' || variant === 'info',
          'bg-gray-100 text-secondary border-gray-200': variant === 'draft',
          'bg-blue-50 text-blue-700 border-blue-100': variant === 'completed',
          'bg-red-50 text-red-700 border-red-100': variant === 'warning',
        },
        className
      )}
    >
      {children}
    </span>
  );
}
