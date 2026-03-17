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

export interface ArtifactRecord {
  artifact_id: string;
  notebook_id: string;
  type: "mind_map" | "audio" | "slides" | "quiz";
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

export interface NotebookState {
  notebookIds: string[];
  selectedNotebookId: string | null;
  artifacts: ArtifactRecord[];
  currentJob: JobRecord | null;
  isLoading: boolean;
  error: string | null;
}

async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) {
    throw new Error(await readApiError(res));
  }
  return res.json() as Promise<T>;
}

async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(await readApiError(res));
  }
  return res.json() as Promise<T>;
}

async function apiPatch<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(await readApiError(res));
  }
  return res.json() as Promise<T>;
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
    // Fall back to plain text.
  }

  return text;
}

function withApiBase(path?: string | null): string | null {
  if (!path) return null;
  return path.startsWith("http") ? path : `${API_BASE}${path}`;
}

export function useNotebook() {
  const [state, setState] = useState<NotebookState>({
    notebookIds: [],
    selectedNotebookId: null,
    artifacts: [],
    currentJob: null,
    isLoading: false,
    error: null,
  });

  const setError = (error: string) =>
    setState((current) => ({ ...current, isLoading: false, error }));

  const setSelectedNotebookId = useCallback((notebookId: string) => {
    setState((current) => ({ ...current, selectedNotebookId: notebookId }));
  }, []);

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
          }
        );
        setState((current) => ({
          ...current,
          notebookIds: data.notebook_ids,
          selectedNotebookId: data.notebook_ids[0] ?? null,
          isLoading: false,
        }));
        return data.notebook_ids;
      } catch (err) {
        setError(String(err));
        return [];
      }
    },
    []
  );

  const refreshArtifact = useCallback(async (artifactId: string) => {
    return apiGet<ArtifactRecord>(`/artifacts/${artifactId}`);
  }, []);

  const startArtifactJob = useCallback(
    async (types: Array<"mind_map" | "audio" | "slides" | "quiz">) => {
      if (!state.selectedNotebookId) {
        return null;
      }

      setState((current) => ({ ...current, isLoading: true, error: null }));
      try {
        const job = await apiPost<JobRecord>(
          `/notebooks/${state.selectedNotebookId}/artifacts`,
          { types }
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

        const artifacts =
          latest.result?.artifacts ||
          (await Promise.all(latest.artifact_ids.map((artifactId) => refreshArtifact(artifactId))));

        setState((current) => ({
          ...current,
          artifacts: [
            ...current.artifacts.filter(
              (existing) => !artifacts.some((incoming) => incoming.type === existing.type)
            ),
            ...artifacts,
          ],
          currentJob: latest,
          isLoading: false,
        }));
        return latest;
      } catch (err) {
        setError(String(err));
        return null;
      }
    },
    [refreshArtifact, state.selectedNotebookId]
  );

  const reviseSlide = useCallback(
    async (slideIndex: number, prompt: string) => {
      const slidesArtifact = state.artifacts.find((artifact) => artifact.type === "slides");
      if (!slidesArtifact || !state.selectedNotebookId) {
        return;
      }

      try {
        const data = await apiPatch<{ slide: Slide }>(
          `/notebooks/${state.selectedNotebookId}/slides/${slideIndex}`,
          {
            artifact_id: slidesArtifact.artifact_id,
            revision_prompt: prompt,
          }
        );

        setState((current) => ({
          ...current,
          artifacts: current.artifacts.map((artifact) => {
            if (artifact.artifact_id !== slidesArtifact.artifact_id) {
              return artifact;
            }

            const currentSlides = Array.isArray(artifact.preview?.slides)
              ? [...artifact.preview.slides]
              : [];
            currentSlides[slideIndex] = data.slide;
            return {
              ...artifact,
              preview: {
                ...(artifact.preview || {}),
                slides: currentSlides,
              },
            };
          }),
        }));
      } catch (err) {
        setError(String(err));
      }
    },
    [state.artifacts, state.selectedNotebookId]
  );

  const mindMap = useMemo(
    () => (state.artifacts.find((artifact) => artifact.type === "mind_map")?.preview ?? null) as MindMapData | null,
    [state.artifacts]
  );
  const audioUrl = useMemo(
    () => {
      const downloadUrls = state.artifacts.find((artifact) => artifact.type === "audio")?.download_urls;
      return withApiBase(downloadUrls?.mp3 ?? downloadUrls?.wav ?? null);
    },
    [state.artifacts]
  );
  const slides = useMemo(
    () =>
      ((state.artifacts.find((artifact) => artifact.type === "slides")?.preview?.slides ??
        []) as Slide[]),
    [state.artifacts]
  );
  const quiz = useMemo(
    () => (state.artifacts.find((artifact) => artifact.type === "quiz")?.preview ?? null) as QuizData | null,
    [state.artifacts]
  );

  return {
    ...state,
    mindMap,
    audioUrl,
    slides,
    quiz,
    setSelectedNotebookId,
    uploadToNotebookLM,
    startArtifactJob,
    reviseSlide,
  };
}
