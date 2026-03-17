import { useState } from "react";
import { ArtifactGallery } from "./components/ArtifactGallery";
import { ChatGallery } from "./components/ChatGallery";
import { IngestionDropzone } from "./components/IngestionDropzone";
import { PassportCard } from "./components/PassportCard";
import { SearchPanel } from "./components/SearchPanel";
import { StudioControls } from "./components/StudioControls";
import { TopicLaboratory } from "./components/TopicLaboratory";
import { useNotebook } from "./hooks/useNotebook";

interface TopicLaboratoryData {
  total_conversations: number;
  topics: Array<{
    topic: string;
    count: number;
    titles: string[];
  }>;
}

interface ConvertResult {
  output_dir: string;
  files_created: number;
  attachment_count: number;
  conversation_count: number;
  file_paths: string[];
  topic_laboratory?: TopicLaboratoryData;
}

export default function App() {
  const [convertResult, setConvertResult] = useState<ConvertResult | null>(null);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [passportId, setPassportId] = useState<string | null>(null);

  const {
    notebookIds,
    selectedNotebookId,
    currentJob,
    mindMap,
    audioUrl,
    slides,
    quiz,
    isLoading,
    error,
    startArtifactJob,
    reviseSlide,
    setSelectedNotebookId,
    uploadToNotebookLM,
  } = useNotebook();

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <header className="border-b border-gray-800 bg-gray-900 px-6 py-4">
        <div className="mx-auto flex max-w-7xl items-center gap-3">
          <span className="text-2xl">🚀</span>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-white">
              byeGPT <span className="text-brand-400">Studio</span>
            </h1>
            <p className="text-xs text-gray-500">v4 · Knowledge OS</p>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-6 py-8">
        <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
          <div className="flex flex-col gap-8 lg:col-span-2">
            <section>
              <SectionHeader step={1} title="Import your ChatGPT export" />
              <IngestionDropzone
                onConverted={setConvertResult}
                onFileSelected={setUploadedFile}
              />
            </section>

            {uploadedFile && (
              <section>
                <SectionHeader step={2} title="Digital Passport" />
                <PassportCard exportFile={uploadedFile} onGenerated={setPassportId} />
              </section>
            )}

            {convertResult && convertResult.file_paths.length > 0 && (
              <section>
                <SectionHeader step={3} title="Converted Files" />
                <ChatGallery filePaths={convertResult.file_paths} />
              </section>
            )}

            {convertResult?.topic_laboratory && (
              <section>
                <SectionHeader step={4} title="Topic Laboratory" />
                <TopicLaboratory
                  data={convertResult.topic_laboratory}
                  notebookCount={notebookIds.length}
                />
              </section>
            )}

            {convertResult?.output_dir && (
              <section>
                <SectionHeader step={5} title="Semantic Search" />
                <SearchPanel outputDir={convertResult.output_dir} />
              </section>
            )}

            {(mindMap || audioUrl || slides.length > 0 || quiz) && (
              <section>
                <SectionHeader step={6} title="Artifacts" />
                <ArtifactGallery
                  mindMap={mindMap}
                  audioUrl={audioUrl}
                  slides={slides}
                  quiz={quiz}
                  onReviseSlide={reviseSlide}
                />
              </section>
            )}
          </div>

          <div className="lg:col-span-1">
            <div className="sticky top-8">
              <SectionHeader step={null} title="Studio Controls" />
              <StudioControls
                outputDir={convertResult?.output_dir ?? null}
                passportId={passportId}
                notebookIds={notebookIds}
                selectedNotebookId={selectedNotebookId}
                currentJob={currentJob}
                isLoading={isLoading}
                error={error}
                onSelectedNotebookId={setSelectedNotebookId}
                onUpload={uploadToNotebookLM}
                onGenerateArtifacts={startArtifactJob}
              />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

function SectionHeader({
  step,
  title,
}: {
  step: number | null;
  title: string;
}) {
  return (
    <div className="mb-4 flex items-center gap-3">
      {step !== null && (
        <span className="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full bg-brand-600 text-xs font-bold text-white">
          {step}
        </span>
      )}
      <h2 className="text-base font-semibold text-gray-100">{title}</h2>
    </div>
  );
}
