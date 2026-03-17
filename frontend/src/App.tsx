/**
 * App.tsx — byeGPT Studio root component.
 *
 * Layout
 * ──────
 *  ┌─ Header ────────────────────────────────┐
 *  │ byeGPT Studio                           │
 *  ├─ Main ──────────────────────────────────┤
 *  │  ┌─ Left (2/3) ────┐  ┌─ Right (1/3) ─┐│
 *  │  │ IngestionDropzone│  │ StudioControls ││
 *  │  │ PassportCard     │  │                ││
 *  │  │ ChatGallery      │  │                ││
 *  │  │ ArtifactGallery  │  │                ││
 *  │  └─────────────────┘  └────────────────┘│
 *  └─────────────────────────────────────────┘
 */

import { useState } from "react";
import { IngestionDropzone } from "./components/IngestionDropzone";
import { StudioControls } from "./components/StudioControls";
import { ChatGallery } from "./components/ChatGallery";
import { PassportCard } from "./components/PassportCard";
import { ArtifactGallery } from "./components/ArtifactGallery";
import { useNotebook } from "./hooks/useNotebook";

interface ConvertResult {
  output_dir: string;
  files_created: number;
  attachment_count: number;
  conversation_count: number;
  file_paths: string[];
}

export default function App() {
  const [convertResult, setConvertResult] = useState<ConvertResult | null>(null);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [notebookIds, setNotebookIds] = useState<string[]>([]);

  const { mindMap, audioUrl, slides, fetchMindMap, fetchAudio, fetchSlides, reviseSlide } =
    useNotebook();

  const handleConverted = (result: ConvertResult) => {
    setConvertResult(result);
  };

  const activeNotebookId = notebookIds[0] ?? "";

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      {/* ── Header ── */}
      <header className="border-b border-gray-800 bg-gray-900 px-6 py-4">
        <div className="mx-auto max-w-7xl flex items-center gap-3">
          <span className="text-2xl">🚀</span>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-white">
              byeGPT{" "}
              <span className="text-brand-400">Studio</span>
            </h1>
            <p className="text-xs text-gray-500">v3 · Full-stack PowerApp</p>
          </div>
        </div>
      </header>

      {/* ── Main ── */}
      <main className="mx-auto max-w-7xl px-6 py-8">
        <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
          {/* Left column */}
          <div className="lg:col-span-2 flex flex-col gap-8">
            {/* Step 1: Ingest */}
            <section>
              <SectionHeader step={1} title="Import your ChatGPT export" />
              <IngestionDropzone
                onConverted={handleConverted}
              />
            </section>

            {/* Step 2: Passport */}
            {uploadedFile && (
              <section>
                <SectionHeader step={2} title="Digital Passport" />
                <PassportCard exportFile={uploadedFile} />
              </section>
            )}

            {/* Step 3: Files */}
            {convertResult && convertResult.file_paths.length > 0 && (
              <section>
                <SectionHeader step={3} title="Converted Files" />
                <ChatGallery filePaths={convertResult.file_paths} />
              </section>
            )}

            {/* Step 4: Artifacts */}
            {(mindMap || audioUrl || slides.length > 0) && (
              <section>
                <SectionHeader step={4} title="Artifacts" />
                <ArtifactGallery
                  mindMap={mindMap}
                  audioUrl={audioUrl}
                  slides={slides}
                  notebookId={activeNotebookId}
                  onReviseSlide={(idx, prompt) =>
                    reviseSlide(activeNotebookId, "", idx, prompt)
                  }
                />
              </section>
            )}
          </div>

          {/* Right column — Studio Controls */}
          <div className="lg:col-span-1">
            <div className="sticky top-8">
              <SectionHeader step={null} title="Studio Controls" />
              <StudioControls
                outputDir={convertResult?.output_dir ?? null}
                notebookIds={notebookIds}
                onNotebookIds={setNotebookIds}
              />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

// ---------------------------------------------------------------------------
// SectionHeader helper
// ---------------------------------------------------------------------------

function SectionHeader({
  step,
  title,
}: {
  step: number | null;
  title: string;
}) {
  return (
    <div className="flex items-center gap-3 mb-4">
      {step !== null && (
        <span className="flex h-6 w-6 items-center justify-center rounded-full bg-brand-600 text-xs font-bold text-white flex-shrink-0">
          {step}
        </span>
      )}
      <h2 className="text-base font-semibold text-gray-100">{title}</h2>
    </div>
  );
}
