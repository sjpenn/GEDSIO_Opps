import React, { useEffect } from 'react';
import { X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';

interface SlideoutProps {
  isOpen: boolean;
  onClose: () => void;
  children: React.ReactNode;
  width?: string;
  title?: string;
  side?: 'left' | 'right';
}

export function Slideout({ 
  isOpen, 
  onClose, 
  children, 
  width = "max-w-2xl", 
  title,
  side = 'right'
}: SlideoutProps) {
  // Lock body scroll when open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  // keydown escape to close
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
        if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, [onClose]);

  const isRight = side === 'right';

  return (
    <div 
      className={cn(
        "fixed inset-0 z-50 flex transition-all duration-700 pointer-events-none",
        isRight ? "justify-end" : "justify-start",
        isOpen ? "pointer-events-auto" : ""
      )}
    >
      {/* Backdrop */}
      <div 
        className={cn(
          "absolute inset-0 bg-black/40 backdrop-blur-sm transition-opacity duration-700 ease-in-out",
          isOpen ? "opacity-100" : "opacity-0"
        )}
        onClick={onClose}
      />

      {/* Slideout Panel - "Slow but confident" animation curve */}
      <div 
        className={cn(
          "relative h-full bg-background shadow-2xl flex flex-col transition-transform duration-700 cubic-bezier(0.32, 0.72, 0, 1)",
          isRight ? "border-l" : "border-r",
          width,
          "w-full", // Mobile full width by default unless width constrained
          isOpen 
            ? "translate-x-0" 
            : (isRight ? "translate-x-full" : "-translate-x-full")
        )}
        style={{ transitionTimingFunction: 'cubic-bezier(0.25, 1, 0.5, 1)' }} // Custom "confident" ease
      >
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h2 className="text-lg font-semibold">{title}</h2>
          <Button 
            variant="ghost" 
            size="icon" 
            onClick={onClose}
            className="rounded-full hover:bg-muted"
          >
            <X className="h-5 w-5" />
          </Button>
        </div>
        <div className="flex-1 overflow-y-auto p-6">
          {children}
        </div>
      </div>
    </div>
  );
}
