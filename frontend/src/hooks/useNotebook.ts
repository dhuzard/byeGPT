import { useCallback, useMemo, useState } from "react";

const API_BASE = "/api";

export interface MindMapData {
  nodes: { id: string; label: string; group?: string }[];
  links: { source: string; target: string }[];
}

export interface Slide {
  title: string;
  content: string;
}

export interface QuizQuestion {
  question: string;
  answer?: string;
}

export interface QuizData {
  title?: string;
  questions: QuizQuestion[];
}

export interface Flashcard {
  front?: string;
  back?: string;
  f?: string;
  b?: string;
}

export interface FlashcardsData {
  title?: string;
  cards: Flashcard[];
}

export interface DataTableData {
  rows: Array<Record<string, string>>;
}

export interface TaxonomySubcategory {
  name: string;
  slug: string;
  count: number;
  representative_titles?: string[];
  conversation_ids: string[];
}

export interface TaxonomyCategory {
  name: string;
  slug: string;
  count: number;
  representative_titles?: string[];
  subcategories: TaxonomySubcategory[];
}

export interface TaxonomyData {
  version?: string;
  total_conversations: number;
  categories: TaxonomyCategory[];
  suggested_notebooks?: Array<{
    title: string;
    category: string;
    subcategories: string[];
  }>;
}

export interface ArtifactRecord {
  artifact_id: string;
  notebook_id: string;
  type:
    | "mind_map"
    | "audio"
    | "slides"
    | "quiz"
    | "video"
    | "cinematic_video"
    | "flashcards"
    | "infographic"
    | "data_table";
  preview: any;
  download_urls: Record<string, string>;
  upstream_artifact_id?: string | null;
}

export interface JobRecord {
  job_id: string;
  status: "queued" | "running" | "completed" | "failed";
  artifact_ids: string[];
  error?: string | null;
  result?: {
    artifacts?: ArtifactRecord[];
  } | null;
}

export interface NotebookSelection {
  category: string;
  subcategory: string;
}

export interface NotebookRecord {
  notebook_id: string;
  title: string;
  kind: "master" | "thematic";
  output_dir: string;
  source_paths: string[];
  source_count: number;
  passport_id?: string | null;
  taxonomy_version?: string | null;
  parent_notebook_id?: string | null;
  selection_filters: NotebookSelection[];
  conversation_ids: string[];
  artifacts?: ArtifactRecord[];
  taxonomy?: TaxonomyData | null;
}

export interface SourceRecord {
  path: string;
  title: string;
  conversation_id?: string | null;
}

export interface ChatTurn {
  question: string;
  answer: string;
}

export interface ChatState {
  conversationId: string | null;
  turns: ChatTurn[];
}

interface NotebookState {
  notebooks: NotebookRecord[];
  selectedNotebookId: string | null;
  sources: SourceRecord[];
  artifacts: ArtifactRecord[];
  chat: ChatState;
  currentJob: JobRecord | null;
  isLoading: boolean;
  error: string | null;
}

async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`);
  if (!response.ok) {
    throw new Error(await readApiError(response));
  }
  return response.json() as Promise<T>;
}

async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(await readApiError(response));
  }
  return response.json() as Promise<T>;
}

async function apiPatch<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(await readApiError(response));
  }
  return response.json() as Promise<T>;
}

async function readApiError(res: Response): Promise<string> {
  const text = await res.text();
  if (!text) {
    return `HTTP ${res.status}`;
  }
  try {
    const parsed = JSON.parse(text) as { detail?: string };
    if (parsed.detail) {
      return parsed.detail;
    }
  } catch {
    // Fall back to raw text.
  }
  return text;
}

function withApiBase(path?: string | null): string | null {
  if (!path) {
    return null;
  }
  return path.startsWith("http") ? path : `${API_BASE}${path}`;
}

function mergeNotebooks(
  current: NotebookRecord[],
  incoming: NotebookRecord[],
): NotebookRecord[] {
  const byId = new Map(current.map((notebook) => [notebook.notebook_id, notebook]));
  for (const notebook of incoming) {
    byId.set(notebook.notebook_id, {
      ...(byId.get(notebook.notebook_id) || {}),
      ...notebook,
    });
  }
  return Array.from(byId.values());
}

export function useNotebook() {
  const [state, setState] = useState<NotebookState>({
    notebooks: [],
    selectedNotebookId: null,
    sources: [],
    artifacts: [],
    chat: {
      conversationId: null,
      turns: [],
    },
    currentJob: null,
    isLoading: false,
    error: null,
  });

  const setError = (error: string) =>
    setState((current) => ({ ...current, isLoading: false, error }));

  const loadNotebook = useCallback(async (notebookId: string) => {
    const [detail, sourcePayload] = await Promise.all([
      apiGet<NotebookRecord>(`/notebooks/${notebookId}`),
      apiGet<{ sources: SourceRecord[] }>(`/notebooks/${notebookId}/sources`),
    ]);

    setState((current) => ({
      ...current,
      notebooks: mergeNotebooks(current.notebooks, [detail]),
      selectedNotebookId: notebookId,
      artifacts: detail.artifacts || [],
      sources: sourcePayload.sources || [],
      isLoading: false,
      error: null,
    }));
    try {
      const chatPayload = await apiGet<{ conversation_id: string | null; turns: ChatTurn[] }>(
        `/notebooks/${notebookId}/chat`,
      );
      setState((current) => ({
        ...current,
        chat: {
          conversationId: chatPayload.conversation_id,
          turns: chatPayload.turns || [],
        },
      }));
    } catch {
      setState((current) => ({
        ...current,
        chat: {
          conversationId: null,
          turns: [],
        },
      }));
    }
    return detail;
  }, []);

  const setSelectedNotebookId = useCallback(
    (notebookId: string) => {
      setState((current) => ({ ...current, selectedNotebookId: notebookId, isLoading: true }));
      void loadNotebook(notebookId).catch((err) => setError(String(err)));
    },
    [loadNotebook],
  );

  const uploadToNotebookLM = useCallback(
    async (outputDir: string, title = "byeGPT Archive", passportId?: string | null) => {
      setState((current) => ({ ...current, isLoading: true, error: null }));
      try {
        const data = await apiPost<{ notebook_ids: string[] }>(
          "/notebooks/upload",
          {
            notebook_title: title,
            output_dir: outputDir,
            passport_id: passportId ?? null,
          },
        );
        const notebooks = await Promise.all(
          data.notebook_ids.map((notebookId) => apiGet<NotebookRecord>(`/notebooks/${notebookId}`)),
        );
        const selectedNotebookId = notebooks[0]?.notebook_id ?? null;
        setState((current) => ({
          ...current,
          notebooks: mergeNotebooks(current.notebooks, notebooks),
          selectedNotebookId,
          isLoading: false,
        }));
        if (selectedNotebookId) {
          await loadNotebook(selectedNotebookId);
        }
        return notebooks;
      } catch (err) {
        setError(String(err));
        return [];
      }
    },
    [loadNotebook],
  );

  const createDerivedNotebook = useCallback(
    async (payload: {
      title: string;
      passportId: string;
      parentOutputDir?: string | null;
      parentNotebookId?: string | null;
      selections: NotebookSelection[];
    }) => {
      setState((current) => ({ ...current, isLoading: true, error: null }));
      try {
        const notebook = await apiPost<NotebookRecord>("/notebooks/derived", {
          title: payload.title,
          passport_id: payload.passportId,
          parent_output_dir: payload.parentOutputDir ?? null,
          parent_notebook_id: payload.parentNotebookId ?? null,
          selections: payload.selections,
        });
        setState((current) => ({
          ...current,
          notebooks: mergeNotebooks(current.notebooks, [notebook]),
          selectedNotebookId: notebook.notebook_id,
          isLoading: false,
        }));
        await loadNotebook(notebook.notebook_id);
        return notebook;
      } catch (err) {
        setError(String(err));
        return null;
      }
    },
    [loadNotebook],
  );

  const startArtifactJob = useCallback(
    async (
      types: Array<
        | "mind_map"
        | "audio"
        | "slides"
        | "quiz"
        | "video"
        | "cinematic_video"
        | "flashcards"
        | "infographic"
        | "data_table"
      >,
    ) => {
      if (!state.selectedNotebookId) {
        return null;
      }

      setState((current) => ({ ...current, isLoading: true, error: null }));
      try {
        const job = await apiPost<JobRecord>(
          `/notebooks/${state.selectedNotebookId}/artifacts`,
          { types },
        );
        setState((current) => ({ ...current, currentJob: job }));

        let latest = job;
        while (latest.status === "queued" || latest.status === "running") {
          await new Promise((resolve) => window.setTimeout(resolve, 800));
          latest = await apiGet<JobRecord>(`/jobs/${job.job_id}`);
          setState((current) => ({ ...current, currentJob: latest }));
        }

        if (latest.status === "failed") {
          throw new Error(latest.error || "Artifact job failed.");
        }

        await loadNotebook(state.selectedNotebookId);
        setState((current) => ({ ...current, currentJob: latest, isLoading: false }));
        return latest;
      } catch (err) {
        setError(String(err));
        return null;
      }
    },
    [loadNotebook, state.selectedNotebookId],
  );

  const reviseSlide = useCallback(
    async (slideIndex: number, prompt: string) => {
      const slidesArtifact = state.artifacts.find((artifact) => artifact.type === "slides");
      if (!slidesArtifact || !state.selectedNotebookId) {
        return;
      }

      try {
        await apiPatch<{ slide: Slide }>(
          `/notebooks/${state.selectedNotebookId}/slides/${slideIndex}`,
          {
            artifact_id: slidesArtifact.artifact_id,
            revision_prompt: prompt,
          },
        );
        await loadNotebook(state.selectedNotebookId);
      } catch (err) {
        setError(String(err));
      }
    },
    [loadNotebook, state.artifacts, state.selectedNotebookId],
  );

  const askNotebook = useCallback(
    async (question: string) => {
      if (!state.selectedNotebookId || !question.trim()) {
        return null;
      }
      try {
        const response = await apiPost<{
          answer: string;
          conversation_id: string;
        }>(`/notebooks/${state.selectedNotebookId}/chat`, {
          question,
          conversation_id: state.chat.conversationId,
        });
        setState((current) => ({
          ...current,
          chat: {
            conversationId: response.conversation_id,
            turns: [
              ...current.chat.turns,
              {
                question,
                answer: response.answer,
              },
            ],
          },
        }));
        return response;
      } catch (err) {
        setError(String(err));
        return null;
      }
    },
    [state.chat.conversationId, state.selectedNotebookId],
  );

  const selectedNotebook = useMemo(
    () =>
      state.notebooks.find((notebook) => notebook.notebook_id === state.selectedNotebookId) || null,
    [state.notebooks, state.selectedNotebookId],
  );

  const mindMap = useMemo(
    () => (state.artifacts.find((artifact) => artifact.type === "mind_map")?.preview ?? null) as MindMapData | null,
    [state.artifacts],
  );
  const audioUrl = useMemo(() => {
    const downloadUrls = state.artifacts.find((artifact) => artifact.type === "audio")?.download_urls;
    return withApiBase(downloadUrls?.mp3 ?? downloadUrls?.mp4 ?? downloadUrls?.wav ?? null);
  }, [state.artifacts]);
  const slides = useMemo(
    () => ((state.artifacts.find((artifact) => artifact.type === "slides")?.preview?.slides ?? []) as Slide[]),
    [state.artifacts],
  );
  const quiz = useMemo(
    () => (state.artifacts.find((artifact) => artifact.type === "quiz")?.preview ?? null) as QuizData | null,
    [state.artifacts],
  );
  const videoUrl = useMemo(() => {
    const downloadUrls = state.artifacts.find((artifact) => artifact.type === "video")?.download_urls;
    return withApiBase(downloadUrls?.mp4 ?? null);
  }, [state.artifacts]);
  const cinematicVideoUrl = useMemo(() => {
    const downloadUrls = state.artifacts.find((artifact) => artifact.type === "cinematic_video")?.download_urls;
    return withApiBase(downloadUrls?.mp4 ?? null);
  }, [state.artifacts]);
  const flashcards = useMemo(
    () => (state.artifacts.find((artifact) => artifact.type === "flashcards")?.preview ?? null) as FlashcardsData | null,
    [state.artifacts],
  );
  const infographicUrl = useMemo(() => {
    const downloadUrls = state.artifacts.find((artifact) => artifact.type === "infographic")?.download_urls;
    return withApiBase(downloadUrls?.png ?? null);
  }, [state.artifacts]);
  const dataTable = useMemo(
    () => (state.artifacts.find((artifact) => artifact.type === "data_table")?.preview ?? null) as DataTableData | null,
    [state.artifacts],
  );

  return {
    ...state,
    selectedNotebook,
    mindMap,
    audioUrl,
    slides,
    quiz,
    videoUrl,
    cinematicVideoUrl,
    flashcards,
    infographicUrl,
    dataTable,
    chat: state.chat,
    setSelectedNotebookId,
    loadNotebook,
    uploadToNotebookLM,
    createDerivedNotebook,
    startArtifactJob,
    reviseSlide,
    askNotebook,
  };
}
