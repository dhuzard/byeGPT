/**
 * useNotebook — API polling hook for NotebookLM artifacts.
 *
 * Polls the backend for the status of an asynchronous artifact generation
 * task (mind map, audio overview, slides) until it is ready or fails.
 */

import { useCallback, useState } from "react";

const API_BASE = "/api";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface ConvertResult {
  output_dir: string;
  files_created: number;
  attachment_count: number;
  conversation_count: number;
  file_paths: string[];
}

export interface PersonaResult {
  passport_markdown: string;
}

export interface MindMapData {
  nodes: { id: string; label: string; group?: string }[];
  links: { source: string; target: string }[];
}

export interface Slide {
  title: string;
  content: string;
}

export interface NotebookState {
  notebookIds: string[];
  mindMap: MindMapData | null;
  audioUrl: string | null;
  slides: Slide[];
  isLoading: boolean;
  error: string | null;
}

// ---------------------------------------------------------------------------
// Low-level fetch helpers
// ---------------------------------------------------------------------------

async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || `HTTP ${res.status}`);
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
    const detail = await res.text();
    throw new Error(detail || `HTTP ${res.status}`);
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
    const detail = await res.text();
    throw new Error(detail || `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useNotebook() {
  const [state, setState] = useState<NotebookState>({
    notebookIds: [],
    mindMap: null,
    audioUrl: null,
    slides: [],
    isLoading: false,
    error: null,
  });

  const setLoading = (isLoading: boolean) =>
    setState((s) => ({ ...s, isLoading, error: null }));

  const setError = (error: string) =>
    setState((s) => ({ ...s, isLoading: false, error }));

  // ── Upload notebooks ──────────────────────────────────────────────────────

  const uploadToNotebookLM = useCallback(
    async (outputDir: string, title = "byeGPT Archive") => {
      setLoading(true);
      try {
        const data = await apiPost<{ notebook_ids: string[] }>(
          "/notebooks/upload",
          { notebook_title: title, output_dir: outputDir }
        );
        setState((s) => ({
          ...s,
          notebookIds: data.notebook_ids,
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

  // ── Mind map ──────────────────────────────────────────────────────────────

  const fetchMindMap = useCallback(async (notebookId: string) => {
    setLoading(true);
    try {
      const data = await apiGet<{ mind_map: MindMapData }>(
        `/notebooks/${notebookId}/mindmap`
      );
      setState((s) => ({ ...s, mindMap: data.mind_map, isLoading: false }));
    } catch (err) {
      setError(String(err));
    }
  }, []);

  // ── Audio overview ────────────────────────────────────────────────────────

  const fetchAudio = useCallback(async (notebookId: string) => {
    setLoading(true);
    try {
      const url = `${API_BASE}/notebooks/${notebookId}/audio`;
      setState((s) => ({ ...s, audioUrl: url, isLoading: false }));
    } catch (err) {
      setError(String(err));
    }
  }, []);

  // ── Slides ────────────────────────────────────────────────────────────────

  const fetchSlides = useCallback(async (notebookId: string) => {
    setLoading(true);
    try {
      const data = await apiGet<{ slides: Slide[] }>(
        `/notebooks/${notebookId}/slides`
      );
      setState((s) => ({ ...s, slides: data.slides, isLoading: false }));
    } catch (err) {
      setError(String(err));
    }
  }, []);

  const reviseSlide = useCallback(
    async (
      notebookId: string,
      artifactId: string,
      slideIndex: number,
      prompt: string
    ) => {
      try {
        const data = await apiPatch<{ slide: Slide }>(
          `/notebooks/${notebookId}/slides/${slideIndex}`,
          { artifact_id: artifactId, revision_prompt: prompt }
        );
        setState((s) => {
          const slides = [...s.slides];
          slides[slideIndex] = data.slide;
          return { ...s, slides };
        });
      } catch (err) {
        setError(String(err));
      }
    },
    []
  );

  // Cleanup on unmount — placeholder for future AbortController integration
  return {
    ...state,
    uploadToNotebookLM,
    fetchMindMap,
    fetchAudio,
    fetchSlides,
    reviseSlide,
  };
}
