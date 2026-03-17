/**
 * ArtifactGallery — renders mind map, podcast player, and slide editor.
 */

import React, { useState } from "react";
import { Play, Pause, ChevronDown, ChevronUp, Send } from "lucide-react";
import { MindMap, MindMapData } from "./MindMap";

interface Slide {
  title: string;
  content: string;
}

interface ArtifactGalleryProps {
  mindMap: MindMapData | null;
  audioUrl: string | null;
  slides: Slide[];
  onReviseSlide?: (slideIndex: number, prompt: string) => void;
}

export function ArtifactGallery({
  mindMap,
  audioUrl,
  slides,
  onReviseSlide,
}: ArtifactGalleryProps) {
  if (!mindMap && !audioUrl && slides.length === 0) return null;

  return (
    <div className="flex flex-col gap-6">
      {mindMap && <MindMap data={mindMap} />}
      {audioUrl && <PodcastPlayer audioUrl={audioUrl} />}
      {slides.length > 0 && (
        <SlideEditor
          slides={slides}
          onRevise={onReviseSlide}
        />
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Podcast Player
// ---------------------------------------------------------------------------

function PodcastPlayer({ audioUrl }: { audioUrl: string }) {
  const [playing, setPlaying] = useState(false);
  const audioRef = React.useRef<HTMLAudioElement>(null);

  const toggle = () => {
    if (!audioRef.current) return;
    if (playing) {
      audioRef.current.pause();
    } else {
      audioRef.current.play();
    }
    setPlaying(!playing);
  };

  return (
    <div className="rounded-xl bg-gray-900 border border-gray-800 p-5">
      <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-4">
        Audio Overview
      </h3>
      <div className="flex items-center gap-4">
        <button
          onClick={toggle}
          className="flex-shrink-0 rounded-full bg-brand-600 hover:bg-brand-700 p-3 text-white transition-colors"
        >
          {playing
            ? <Pause className="h-5 w-5" />
            : <Play className="h-5 w-5" />}
        </button>
        <audio ref={audioRef} src={audioUrl} onEnded={() => setPlaying(false)} />
        <div className="flex-1">
          <div className="h-1.5 rounded-full bg-gray-700">
            <div className="h-full rounded-full bg-brand-500 w-0 transition-all" />
          </div>
          <p className="mt-1 text-xs text-gray-500">Audio Overview · MP3</p>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Slide Editor
// ---------------------------------------------------------------------------

interface SlideEditorProps {
  slides: Slide[];
  onRevise?: (slideIndex: number, prompt: string) => void;
}

function SlideEditor({ slides, onRevise }: SlideEditorProps) {
  const [expanded, setExpanded] = useState<number | null>(0);
  const [prompts, setPrompts] = useState<Record<number, string>>({});

  const handleRevise = (index: number) => {
    const prompt = prompts[index];
    if (prompt?.trim() && onRevise) {
      onRevise(index, prompt.trim());
    }
  };

  return (
    <div className="rounded-xl bg-gray-900 border border-gray-800 overflow-hidden">
      <div className="px-5 py-4 border-b border-gray-800">
        <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">
          Slides ({slides.length})
        </h3>
      </div>
      <div className="divide-y divide-gray-800">
        {slides.map((slide, idx) => (
          <div key={idx} className="px-5 py-3">
            <button
              onClick={() => setExpanded(expanded === idx ? null : idx)}
              className="flex w-full items-center justify-between text-left"
            >
              <span className="text-sm font-medium text-gray-100">
                {idx + 1}. {slide.title}
              </span>
              {expanded === idx
                ? <ChevronUp className="h-4 w-4 text-gray-500" />
                : <ChevronDown className="h-4 w-4 text-gray-500" />}
            </button>
            {expanded === idx && (
              <div className="mt-3 space-y-3">
                <p className="text-sm text-gray-400 whitespace-pre-wrap">
                  {slide.content}
                </p>
                {onRevise && (
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={prompts[idx] ?? ""}
                      onChange={(e) =>
                        setPrompts((p) => ({ ...p, [idx]: e.target.value }))
                      }
                      placeholder="Revision prompt… e.g. 'Make this more visual'"
                      className="flex-1 rounded-lg bg-gray-800 border border-gray-700 px-3 py-2
                                 text-xs text-gray-100 focus:outline-none focus:ring-2 focus:ring-brand-500"
                      onKeyDown={(e) => e.key === "Enter" && handleRevise(idx)}
                    />
                    <button
                      onClick={() => handleRevise(idx)}
                      className="rounded-lg bg-brand-600 hover:bg-brand-700 px-3 py-2 text-white transition-colors"
                    >
                      <Send className="h-3.5 w-3.5" />
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
