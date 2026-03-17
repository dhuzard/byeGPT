import { ReactNode, useMemo, useState } from "react";
import { ArtifactGallery } from "./components/ArtifactGallery";
import { IngestionDropzone } from "./components/IngestionDropzone";
import { NotebookChatPanel } from "./components/NotebookChatPanel";
import { PassportCard } from "./components/PassportCard";
import { SearchPanel } from "./components/SearchPanel";
import { StudioControls } from "./components/StudioControls";
import { TopicLaboratory } from "./components/TopicLaboratory";
import { NotebookRecord, TaxonomyData, useNotebook } from "./hooks/useNotebook";

interface ConvertResult {
  output_dir: string;
  files_created: number;
  attachment_count: number;
  conversation_count: number;
  file_paths: string[];
  taxonomy?: TaxonomyData;
}

export default function App() {
  const [convertResult, setConvertResult] = useState<ConvertResult | null>(null);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [passportId, setPassportId] = useState<string | null>(null);
  const [passportTaxonomy, setPassportTaxonomy] = useState<TaxonomyData | null>(null);

  const {
    notebooks,
    selectedNotebook,
    selectedNotebookId,
    sources,
    currentJob,
    chat,
    mindMap,
    audioUrl,
    videoUrl,
    cinematicVideoUrl,
    flashcards,
    infographicUrl,
    slides,
    quiz,
    dataTable,
    isLoading,
    error,
    uploadToNotebookLM,
    createDerivedNotebook,
    startArtifactJob,
    reviseSlide,
    askNotebook,
    setSelectedNotebookId,
  } = useNotebook();

  const activeTaxonomy = useMemo(
    () => selectedNotebook?.taxonomy || passportTaxonomy || convertResult?.taxonomy || null,
    [convertResult?.taxonomy, passportTaxonomy, selectedNotebook?.taxonomy],
  );

  const handleCreateThematicNotebook = async (
    selections: Array<{ category: string; subcategory: string }>,
  ) => {
    if (!passportId || !convertResult?.output_dir) {
      return;
    }
    const title = buildThematicNotebookTitle(activeTaxonomy, selections);
    await createDerivedNotebook({
      title,
      passportId,
      parentOutputDir: convertResult.output_dir,
      parentNotebookId: selectedNotebook?.kind === "master" ? selectedNotebook.notebook_id : null,
      selections,
    });
  };

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <header className="border-b border-gray-800 bg-gray-900 px-6 py-4">
        <div className="mx-auto flex max-w-7xl items-center gap-3">
          <span className="text-2xl">🚀</span>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-white">
              byeGPT <span className="text-brand-400">Studio</span>
            </h1>
            <p className="text-xs text-gray-500">v5 · Thematic Knowledge OS</p>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-6 py-8">
        <div className="grid grid-cols-1 gap-8 lg:grid-cols-[1.7fr,0.9fr]">
          <div className="flex flex-col gap-8">
            {!selectedNotebook && (
              <>
                <section>
                  <SectionHeader step={1} title="Import your ChatGPT export" />
                  <IngestionDropzone
                    onConverted={setConvertResult}
                    onFileSelected={setUploadedFile}
                  />
                </section>

                {uploadedFile && (
                  <section>
                    <SectionHeader step={2} title="Digital Passport 2.0" />
                    <PassportCard
                      exportFile={uploadedFile}
                      onGenerated={({ passportId: nextPassportId, taxonomy }) => {
                        setPassportId(nextPassportId);
                        setPassportTaxonomy(taxonomy);
                      }}
                    />
                  </section>
                )}

                {activeTaxonomy && (
                  <section>
                    <SectionHeader step={3} title="Topic Laboratory" />
                    <TopicLaboratory
                      taxonomy={activeTaxonomy}
                      notebookCount={notebooks.length}
                      selectable={Boolean(passportId)}
                      disabled={isLoading}
                      onCreateThematicNotebook={handleCreateThematicNotebook}
                    />
                  </section>
                )}

                {convertResult?.output_dir && (
                  <section>
                    <SectionHeader step={4} title="Semantic Search" />
                    <SearchPanel outputDir={convertResult.output_dir} />
                  </section>
                )}
              </>
            )}

            {selectedNotebook && (
              <>
                <section>
                  <SectionHeader step={null} title="Studio Workspace" />
                  <div className="grid gap-6 xl:grid-cols-2">
                    <WorkspacePanel title="Sources">
                      <NotebookSummary notebook={selectedNotebook} />
                      <div className="mt-4 space-y-2">
                        {sources.map((source) => (
                          <div
                            key={source.path}
                            className="rounded-2xl border border-gray-800 bg-gray-950/80 px-4 py-3"
                          >
                            <p className="text-sm font-medium text-white">{source.title}</p>
                            <p className="mt-1 text-xs text-gray-500">{source.path}</p>
                          </div>
                        ))}
                      </div>
                    </WorkspacePanel>

                    <WorkspacePanel title="Knowledge Map">
                      {selectedNotebook.taxonomy ? (
                        <TopicLaboratory
                          taxonomy={selectedNotebook.taxonomy}
                          notebookCount={notebooks.length}
                        />
                      ) : (
                        <p className="text-sm text-gray-400">No taxonomy linked to this notebook yet.</p>
                      )}
                    </WorkspacePanel>
                  </div>
                </section>

                <section>
                  <SectionHeader step={null} title="Semantic Search" />
                  <SearchPanel outputDir={selectedNotebook.output_dir} />
                </section>

                <section>
                  <SectionHeader step={null} title="Notebook Interaction" />
                  <NotebookChatPanel
                    chat={chat}
                    onAsk={askNotebook}
                    disabled={isLoading}
                  />
                </section>

                <section>
                  <SectionHeader step={null} title="Artifacts" />
                  <ArtifactGallery
                    mindMap={mindMap}
                    audioUrl={audioUrl}
                    videoUrl={videoUrl}
                    cinematicVideoUrl={cinematicVideoUrl}
                    infographicUrl={infographicUrl}
                    slides={slides}
                    quiz={quiz}
                    flashcards={flashcards}
                    dataTable={dataTable}
                    onReviseSlide={reviseSlide}
                  />
                </section>
              </>
            )}
          </div>

          <div className="lg:col-span-1">
            <div className="sticky top-8">
              <SectionHeader step={null} title="Studio Controls" />
              <StudioControls
                outputDir={convertResult?.output_dir ?? null}
                passportId={passportId}
                notebooks={notebooks}
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

function WorkspacePanel({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <div className="rounded-3xl border border-gray-800 bg-gray-900/90 p-5 shadow-[0_20px_60px_rgba(0,0,0,0.25)]">
      <p className="text-xs uppercase tracking-[0.22em] text-gray-500">{title}</p>
      <div className="mt-4">{children}</div>
    </div>
  );
}

function NotebookSummary({ notebook }: { notebook: NotebookRecord }) {
  return (
    <div className="grid gap-3 md:grid-cols-2">
      <MetricCard label="Notebook" value={notebook.title} />
      <MetricCard label="Kind" value={notebook.kind} />
      <MetricCard label="Sources" value={String(notebook.source_count)} />
      <MetricCard
        label="Filters"
        value={
          notebook.selection_filters.length > 0
            ? `${notebook.selection_filters.length} selected`
            : "Full archive"
        }
      />
    </div>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-4">
      <p className="text-xs uppercase tracking-[0.22em] text-gray-500">{label}</p>
      <p className="mt-2 text-sm font-semibold text-white">{value}</p>
    </div>
  );
}

function buildThematicNotebookTitle(
  taxonomy: TaxonomyData | null,
  selections: Array<{ category: string; subcategory: string }>,
) {
  if (!taxonomy || selections.length === 0) {
    return "Thematic Notebook";
  }
  const labels = selections
    .slice(0, 2)
    .map((selection) => {
      const category = taxonomy.categories.find((item) => item.slug === selection.category);
      const subcategory = category?.subcategories.find((item) => item.slug === selection.subcategory);
      return subcategory?.name || category?.name || selection.subcategory;
    });
  return `${labels.join(" + ")} Notebook`;
}
