'use client';

import { useEffect, useCallback } from 'react';
import Image from 'next/image';
import { TransformWrapper, TransformComponent } from 'react-zoom-pan-pinch';
import { X, ZoomIn, ZoomOut, RotateCcw } from 'lucide-react';

interface ImageLightboxProps {
  src: string;
  alt: string;
  onClose: () => void;
}

export function ImageLightbox({ src, alt, onClose }: ImageLightboxProps) {
  // Handle ESC key
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    },
    [onClose]
  );

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    // Prevent body scroll when lightbox is open
    document.body.style.overflow = 'hidden';

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = '';
    };
  }, [handleKeyDown]);

  // Handle backdrop click
  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 bg-black/90 backdrop-blur-sm flex items-center justify-center"
      onClick={handleBackdropClick}
    >
      {/* Close button */}
      <button
        onClick={onClose}
        className="absolute top-4 right-4 z-50 p-2 bg-white/10 hover:bg-white/20 rounded-full transition-colors"
        aria-label="Close"
      >
        <X className="h-6 w-6 text-white" />
      </button>

      {/* Zoom controls */}
      <TransformWrapper
        initialScale={1}
        minScale={0.5}
        maxScale={4}
        centerOnInit
        wheel={{ step: 0.1 }}
        pinch={{ step: 5 }}
      >
        {({ zoomIn, zoomOut, resetTransform }) => (
          <>
            {/* Control buttons */}
            <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-50 flex gap-2">
              <button
                onClick={() => zoomOut()}
                className="p-2 bg-white/10 hover:bg-white/20 rounded-full transition-colors"
                aria-label="Zoom out"
              >
                <ZoomOut className="h-5 w-5 text-white" />
              </button>
              <button
                onClick={() => resetTransform()}
                className="p-2 bg-white/10 hover:bg-white/20 rounded-full transition-colors"
                aria-label="Reset zoom"
              >
                <RotateCcw className="h-5 w-5 text-white" />
              </button>
              <button
                onClick={() => zoomIn()}
                className="p-2 bg-white/10 hover:bg-white/20 rounded-full transition-colors"
                aria-label="Zoom in"
              >
                <ZoomIn className="h-5 w-5 text-white" />
              </button>
            </div>

            {/* Zoomable image */}
            <TransformComponent
              wrapperClass="!w-full !h-full"
              contentClass="!w-full !h-full flex items-center justify-center"
            >
              <div className="relative w-full h-full max-w-[90vw] max-h-[90vh]">
                <Image
                  src={src}
                  alt={alt}
                  fill
                  sizes="90vw"
                  className="object-contain"
                  priority
                />
              </div>
            </TransformComponent>
          </>
        )}
      </TransformWrapper>

      {/* Help text */}
      <div className="absolute bottom-16 left-1/2 -translate-x-1/2 text-white/60 text-sm">
        Pinch or scroll to zoom • Drag to pan • Tap outside to close
      </div>
    </div>
  );
}
