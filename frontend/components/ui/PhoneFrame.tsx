'use client';

import { ReactNode } from 'react';

interface PhoneFrameProps {
  children: ReactNode;
  onClick?: () => void;
  className?: string;
}

export function PhoneFrame({ children, onClick, className = '' }: PhoneFrameProps) {
  return (
    <div
      onClick={onClick}
      className={`
        relative
        w-full
        max-w-[280px]
        mx-auto
        border-[3px]
        border-gray-800
        rounded-[40px]
        overflow-hidden
        shadow-xl
        bg-black
        ${onClick ? 'cursor-pointer hover:shadow-2xl transition-shadow' : ''}
        ${className}
      `}
    >
      {/* Inner screen area */}
      <div className="relative aspect-[9/19.5] bg-gray-100 rounded-[37px] overflow-hidden">
        {children}
      </div>
    </div>
  );
}
