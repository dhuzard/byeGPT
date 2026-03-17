/**
 * ChatGallery — displays a grid of converted chat files.
 */

import React from "react";
import { FileText } from "lucide-react";

interface ChatGalleryProps {
  filePaths: string[];
}

export function ChatGallery({ filePaths }: ChatGalleryProps) {
  if (!filePaths.length) return null;

  return (
    <div className="w-full">
      <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-3">
        Converted Files
      </h3>
      <div className="grid grid-cols-2 gap-2 max-h-72 overflow-y-auto pr-1">
        {filePaths.map((p) => {
          const name = p.split("/").pop() ?? p;
          return (
            <div
              key={p}
              className="flex items-center gap-2 rounded-lg bg-gray-800 border border-gray-700 px-3 py-2
                         text-xs text-gray-300 hover:bg-gray-700 transition-colors"
            >
              <FileText className="h-3.5 w-3.5 flex-shrink-0 text-brand-400" />
              <span className="truncate">{name}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
