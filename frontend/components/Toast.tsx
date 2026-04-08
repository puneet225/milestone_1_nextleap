"use client";

import { useEffect, useState } from "react";
import { X } from "lucide-react";

interface ToastProps {
  message: string;
  onDismiss: () => void;
}

export function Toast({ message, onDismiss }: ToastProps) {
  useEffect(() => {
    const t = setTimeout(onDismiss, 6000);
    return () => clearTimeout(t);
  }, [onDismiss]);

  return (
    <div className="toast error flex items-start gap-3">
      <span className="flex-1 text-sm">{message}</span>
      <button onClick={onDismiss} className="text-gray-400 hover:text-white mt-0.5 shrink-0">
        <X size={14} />
      </button>
    </div>
  );
}
