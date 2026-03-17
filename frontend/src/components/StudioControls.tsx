/**
 * StudioControls — sidebar panel for triggering NotebookLM actions.
 *
 * Lets the user:
 * - Upload converted Markdown to NotebookLM
 * - Generate a mind map, audio overview, or slides
 */

import React, { useState } from "react";
import {
  CloudUpload,
  BrainCircuit,
  Headphones,
  Presentation,
  Loader2,
} from "lucide-react";
import { useNotebook } from "../hooks/useNotebook";

interface StudioControlsProps {
  outputDir: string | null;
  notebookIds: string[];
  onNotebookIds: (ids: string[]) => void;
}

export function StudioControls({
  outputDir,
  notebookIds,
  onNotebookIds,
}: StudioControlsProps) {
  const {
    isLoading,
    error,
    uploadToNotebookLM,
    fetchMindMap,
    fetchAudio,
    fetchSlides,
  } = useNotebook();

  const [notebookTitle, setNotebookTitle] = useState("byeGPT Archive");
  const [activeNotebook, setActiveNotebook] = useState("");

  const handleUpload = async () => {
    if (!outputDir) return;
    const ids = await uploadToNotebookLM(outputDir, notebookTitle);
    if (ids.length) {
      onNotebookIds(ids);
      setActiveNotebook(ids[0]);
    }
  };

  const notebookId = activeNotebook || notebookIds[0] || "";

  return (
    <div className="flex flex-col gap-6">
      {/* Upload section */}
      <section className="rounded-xl bg-gray-900 p-5 border border-gray-800">
        <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-4">
          1 · Upload to NotebookLM
        </h3>
        <label className="block text-xs text-gray-400 mb-1">Notebook title</label>
        <input
          type="text"
          value={notebookTitle}
          onChange={(e) => setNotebookTitle(e.target.value)}
          className="w-full rounded-lg bg-gray-800 border border-gray-700 px-3 py-2 text-sm
                     text-gray-100 focus:outline-none focus:ring-2 focus:ring-brand-500 mb-3"
          placeholder="My Knowledge Base"
        />
        <ActionButton
          onClick={handleUpload}
          disabled={!outputDir || isLoading}
          icon={<CloudUpload className="h-4 w-4" />}
          label="Upload to NotebookLM"
          isLoading={isLoading}
        />
        {notebookIds.length > 0 && (
          <div className="mt-3 rounded bg-gray-800 p-2 text-xs text-gray-400">
            {notebookIds.length} notebook{notebookIds.length > 1 ? "s" : ""} created
          </div>
        )}
      </section>

      {/* Notebook selector */}
      {notebookIds.length > 0 && (
        <section className="rounded-xl bg-gray-900 p-5 border border-gray-800">
          <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-4">
            2 · Generate Artifacts
          </h3>
          {notebookIds.length > 1 && (
            <>
              <label className="block text-xs text-gray-400 mb-1">
                Select notebook
              </label>
              <select
                value={activeNotebook}
                onChange={(e) => setActiveNotebook(e.target.value)}
                className="w-full rounded-lg bg-gray-800 border border-gray-700 px-3 py-2
                           text-sm text-gray-100 focus:outline-none focus:ring-2
                           focus:ring-brand-500 mb-3"
              >
                {notebookIds.map((id) => (
                  <option key={id} value={id}>
                    {id.substring(0, 16)}…
                  </option>
                ))}
              </select>
            </>
          )}

          <div className="grid grid-cols-1 gap-2">
            <ActionButton
              onClick={() => fetchMindMap(notebookId)}
              disabled={!notebookId || isLoading}
              icon={<BrainCircuit className="h-4 w-4" />}
              label="Generate Mind Map"
              isLoading={isLoading}
            />
            <ActionButton
              onClick={() => fetchAudio(notebookId)}
              disabled={!notebookId || isLoading}
              icon={<Headphones className="h-4 w-4" />}
              label="Generate Audio Overview"
              isLoading={isLoading}
            />
            <ActionButton
              onClick={() => fetchSlides(notebookId)}
              disabled={!notebookId || isLoading}
              icon={<Presentation className="h-4 w-4" />}
              label="Generate Slides"
              isLoading={isLoading}
            />
          </div>
        </section>
      )}

      {error && (
        <p className="rounded-lg bg-red-900/30 border border-red-800 px-4 py-3 text-sm text-red-300">
          {error}
        </p>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// ActionButton helper
// ---------------------------------------------------------------------------

interface ActionButtonProps {
  onClick: () => void;
  disabled: boolean;
  icon: React.ReactNode;
  label: string;
  isLoading?: boolean;
}

function ActionButton({
  onClick,
  disabled,
  icon,
  label,
  isLoading,
}: ActionButtonProps) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className="flex items-center gap-2 w-full rounded-lg bg-brand-600 hover:bg-brand-700
                 disabled:bg-gray-700 disabled:cursor-not-allowed
                 px-4 py-2.5 text-sm font-medium text-white transition-colors"
    >
      {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : icon}
      {label}
    </button>
  );
}
