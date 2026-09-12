import React, { useState, useEffect } from 'react';

export default function ResizableSplitter({ onDrag }) {
  const [isDragging, setIsDragging] = useState(false);

  useEffect(() => {
    const handleMouseMove = (e) => {
      if (isDragging) {
        onDrag(e.movementX);
      }
    };

    const handleMouseUp = () => {
      if (isDragging) {
        setIsDragging(false);
      }
    };

    if (isDragging) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging, onDrag]);

  return (
    <div 
      className={`splitter-handle ${isDragging ? 'dragging' : ''}`}
      onMouseDown={(e) => {
        e.preventDefault();
        setIsDragging(true);
      }}
      title="Drag to resize sections"
    >
      <div className="splitter-line" />
    </div>
  );
}
