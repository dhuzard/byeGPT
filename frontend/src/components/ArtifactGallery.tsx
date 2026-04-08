import React, { useState } from "react";
import { ChevronDown, ChevronUp, Pause, Play, Send } from "lucide-react";
import { DataTableData, FlashcardsData, QuizData } from "../hooks/useNotebook";
import { MindMap, MindMapData } from "./MindMap";

interface Slide {
  title: string;
  content: string;
}

interface ArtifactGalleryProps {
  mindMap: MindMapData | null;
  audioUrl: string | null;
  videoUrl: string | null;
  cinematicVideoUrl: string | null;
  infographicUrl: string | null;
  slides: Slide[];
  quiz: QuizData | null;
  flashcards: FlashcardsData | null;
  dataTable: DataTableData | null;
  onReviseSlide?: (slideIndex: number, prompt: string) => void;
}

export function ArtifactGallery({
  mindMap,
  audioUrl,
  videoUrl,
  cinematicVideoUrl,
  infographicUrl,
  slides,
  quiz,
  flashcards,
  dataTable,
  onReviseSlide,
}: ArtifactGalleryProps) {
  if (
    !mindMap &&
    !audioUrl &&
    !videoUrl &&
    !cinematicVideoUrl &&
    !infographicUrl &&
    slides.length === 0 &&
    !quiz &&
    !flashcards &&
    !dataTable
  ) {
    return null;
  }

  return (
    <div className="flex flex-col gap-6">
      {mindMap && <MindMap data={mindMap} />}
      {audioUrl && <PodcastPlayer title="Audio Overview" audioUrl={audioUrl} />}
      {videoUrl && <VideoPanel title="Video Overview" url={videoUrl} />}
      {cinematicVideoUrl && <VideoPanel title="Cinematic Video" url={cinematicVideoUrl} />}
      {infographicUrl && <InfographicPanel url={infographicUrl} />}
      {slides.length > 0 && <SlideEditor slides={slides} onRevise={onReviseSlide} />}
      {quiz && <QuizPanel quiz={quiz} />}
      {flashcards && <FlashcardsPanel flashcards={flashcards} />}
      {dataTable && <DataTablePanel table={dataTable} />}
    </div>
  );
}

function PodcastPlayer({ title, audioUrl }: { title: string; audioUrl: string }) {
  const [playing, setPlaying] = useState(false);
  const audioRef = React.useRef<HTMLAudioElement>(null);

  const toggle = () => {
    if (!audioRef.current) return;
    if (playing) {
      audioRef.current.pause();
    } else {
      void audioRef.current.play();
    }
    setPlaying(!playing);
  };

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900 p-5">
      <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-gray-300">{title}</h3>
      <div className="flex items-center gap-4">
        <button
          onClick={toggle}
          className="flex-shrink-0 rounded-full bg-brand-600 p-3 text-white transition-colors hover:bg-brand-700"
        >
          {playing ? <Pause className="h-5 w-5" /> : <Play className="h-5 w-5" />}
        </button>
        <audio ref={audioRef} src={audioUrl} onEnded={() => setPlaying(false)} />
        <div className="flex-1">
          <div className="h-1.5 rounded-full bg-gray-700">
            <div className="h-full w-0 rounded-full bg-brand-500 transition-all" />
          </div>
          <p className="mt-1 text-xs text-gray-500">NotebookLM media export</p>
        </div>
      </div>
    </div>
  );
}

function VideoPanel({ title, url }: { title: string; url: string }) {
  return (
    <div className="overflow-hidden rounded-xl border border-gray-800 bg-gray-900">
      <div className="border-b border-gray-800 px-5 py-4">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-gray-300">{title}</h3>
      </div>
      <video controls className="w-full bg-black" src={url} />
    </div>
  );
}

function InfographicPanel({ url }: { url: string }) {
  return (
    <div className="overflow-hidden rounded-xl border border-gray-800 bg-gray-900">
      <div className="border-b border-gray-800 px-5 py-4">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-gray-300">Infographic</h3>
      </div>
      <img src={url} alt="NotebookLM infographic" className="w-full" />
    </div>
  );
}

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
    <div className="overflow-hidden rounded-xl border border-gray-800 bg-gray-900">
      <div className="border-b border-gray-800 px-5 py-4">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-gray-300">
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
              {expanded === idx ? (
                <ChevronUp className="h-4 w-4 text-gray-500" />
              ) : (
                <ChevronDown className="h-4 w-4 text-gray-500" />
              )}
            </button>
            {expanded === idx && (
              <div className="mt-3 space-y-3">
                <p className="whitespace-pre-wrap text-sm text-gray-400">{slide.content}</p>
                {onRevise && (
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={prompts[idx] ?? ""}
                      onChange={(e) => setPrompts((p) => ({ ...p, [idx]: e.target.value }))}
                      placeholder="Revision prompt… e.g. 'Make this more visual'"
                      className="flex-1 rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-xs text-gray-100 focus:outline-none focus:ring-2 focus:ring-brand-500"
                      onKeyDown={(e) => e.key === "Enter" && handleRevise(idx)}
                    />
                    <button
                      onClick={() => handleRevise(idx)}
                      className="rounded-lg bg-brand-600 px-3 py-2 text-white transition-colors hover:bg-brand-700"
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

function QuizPanel({ quiz }: { quiz: QuizData }) {
  return (
    <div className="overflow-hidden rounded-xl border border-gray-800 bg-gray-900">
      <div className="border-b border-gray-800 px-5 py-4">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-gray-300">
          {quiz.title || "Quiz"}
        </h3>
      </div>
      <div className="divide-y divide-gray-800">
        {quiz.questions.map((question, index) => (
          <div key={`${question.question}-${index}`} className="px-5 py-4">
            <p className="text-sm font-medium text-gray-100">
              {index + 1}. {question.question}
            </p>
            {question.answer && <p className="mt-2 text-sm text-gray-400">Answer: {question.answer}</p>}
          </div>
        ))}
      </div>
    </div>
  );
}

function FlashcardsPanel({ flashcards }: { flashcards: FlashcardsData }) {
  const cards = flashcards.cards || [];
  return (
    <div className="overflow-hidden rounded-xl border border-gray-800 bg-gray-900">
      <div className="border-b border-gray-800 px-5 py-4">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-gray-300">
          {flashcards.title || "Flashcards"}
        </h3>
      </div>
      <div className="grid gap-3 p-5 md:grid-cols-2">
        {cards.map((card, index) => (
          <div key={index} className="rounded-2xl border border-gray-800 bg-gray-950/70 p-4">
            <p className="text-xs uppercase tracking-[0.18em] text-gray-500">Card {index + 1}</p>
            <p className="mt-3 text-sm font-medium text-white">{card.front || card.f}</p>
            <p className="mt-3 text-sm text-gray-400">{card.back || card.b}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function DataTablePanel({ table }: { table: DataTableData }) {
  const rows = table.rows || [];
  if (rows.length === 0) {
    return null;
  }
  const headers = Object.keys(rows[0]);
  return (
    <div className="overflow-hidden rounded-xl border border-gray-800 bg-gray-900">
      <div className="border-b border-gray-800 px-5 py-4">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-gray-300">Data Table</h3>
      </div>
      <div className="overflow-auto p-5">
        <table className="min-w-full text-left text-sm text-gray-300">
          <thead>
            <tr className="border-b border-gray-800 text-xs uppercase tracking-[0.18em] text-gray-500">
              {headers.map((header) => (
                <th key={header} className="px-3 py-2 font-medium">
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, index) => (
              <tr key={index} className="border-b border-gray-900 align-top">
                {headers.map((header) => (
                  <td key={`${index}-${header}`} className="px-3 py-3">
                    {row[header]}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
