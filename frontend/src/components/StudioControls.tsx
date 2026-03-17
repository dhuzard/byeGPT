import { ReactNode, useEffect, useState } from "react";
import {
  BrainCircuit,
  CloudUpload,
  Download,
  Headphones,
  Loader2,
  LogIn,
  Presentation,
  RefreshCw,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { JobRecord, NotebookRecord } from "../hooks/useNotebook";

const API_BASE = "/api";

interface StudioControlsProps {
  outputDir: string | null;
  passportId: string | null;
  notebooks: NotebookRecord[];
  selectedNotebookId: string | null;
  currentJob: JobRecord | null;
  isLoading: boolean;
  error: string | null;
  onUpload: (
    outputDir: string,
    title?: string,
    passportId?: string | null
  ) => Promise<NotebookRecord[]>;
  onGenerateArtifacts: (
    types: Array<"mind_map" | "audio" | "slides" | "quiz">
  ) => Promise<JobRecord | null>;
  onSelectedNotebookId: (notebookId: string) => void;
}

export function StudioControls({
  outputDir,
  passportId,
  notebooks,
  selectedNotebookId,
  currentJob,
  isLoading,
  error,
  onUpload,
  onGenerateArtifacts,
  onSelectedNotebookId,
}: StudioControlsProps) {
  const [notebookTitle, setNotebookTitle] = useState("byeGPT Archive");
  const [authChecked, setAuthChecked] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [authLoading, setAuthLoading] = useState(false);
  const [authMessage, setAuthMessage] = useState("");

  const refreshAuthStatus = async () => {
    setAuthLoading(true);
    setAuthMessage("");
    try {
      const res = await fetch(`${API_BASE}/auth/status`);
      if (!res.ok) {
        throw new Error(await res.text());
      }
      const data = (await res.json()) as { authenticated: boolean };
      setIsAuthenticated(Boolean(data.authenticated));
      setAuthMessage(
        data.authenticated
          ? "Studio is ready. Demo mode works without Google login."
          : "NotebookLM login is still required."
      );
    } catch (err) {
      setAuthMessage(err instanceof Error ? err.message : String(err));
      setIsAuthenticated(false);
    } finally {
      setAuthChecked(true);
      setAuthLoading(false);
    }
  };

  useEffect(() => {
    void refreshAuthStatus();
  }, []);

  const startLogin = async () => {
    setAuthLoading(true);
    setAuthMessage("");
    try {
      const res = await fetch(`${API_BASE}/auth/login`, { method: "POST" });
      const text = await res.text();
      if (!res.ok) {
        throw new Error(text || `HTTP ${res.status}`);
      }
      const data = JSON.parse(text) as { message?: string };
      setAuthMessage(data.message ?? "Login flow started.");
      window.setTimeout(() => {
        void refreshAuthStatus();
      }, 1000);
    } catch (err) {
      setAuthMessage(err instanceof Error ? err.message : String(err));
      setIsAuthenticated(false);
    } finally {
      setAuthChecked(true);
      setAuthLoading(false);
    }
  };

  const handleUpload = async () => {
    if (!outputDir || !isAuthenticated) {
      return;
    }
    const created = await onUpload(outputDir, notebookTitle, passportId);
    if (created[0]) {
      onSelectedNotebookId(created[0].notebook_id);
    }
  };

  const notebookId = selectedNotebookId || notebooks[0]?.notebook_id || "";

  const handleBundleExport = () => {
    if (!notebookId) {
      return;
    }
    window.open(`${API_BASE}/notebooks/${notebookId}/export`, "_blank", "noopener,noreferrer");
  };

  return (
    <div className="flex flex-col gap-6">
      <section className="rounded-2xl border border-gray-800 bg-gray-900/90 p-5 shadow-[0_20px_60px_rgba(0,0,0,0.35)]">
        <div className="mb-4 flex items-center justify-between gap-3">
          <div>
            <h3 className="text-sm font-semibold uppercase tracking-[0.22em] text-gray-400">
              Studio Access
            </h3>
            <p className="mt-1 text-xs text-gray-500">
              Demo mode is the easiest path for non-technical testers.
            </p>
          </div>
          <AuthBadge
            loading={authLoading}
            checked={authChecked}
            authenticated={isAuthenticated}
          />
        </div>

        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
          <ActionButton
            onClick={startLogin}
            disabled={authLoading}
            icon={<LogIn className="h-4 w-4" />}
            label="Check Login"
            isLoading={authLoading}
          />
          <ActionButton
            onClick={refreshAuthStatus}
            disabled={authLoading}
            icon={<RefreshCw className="h-4 w-4" />}
            label="Refresh Status"
            isLoading={false}
            tone="secondary"
          />
        </div>

        {authMessage && <p className="mt-3 text-sm text-gray-300">{authMessage}</p>}
      </section>

      <section className="rounded-2xl border border-gray-800 bg-gray-900/90 p-5 shadow-[0_20px_60px_rgba(0,0,0,0.35)]">
        <h3 className="mb-4 text-sm font-semibold uppercase tracking-[0.22em] text-gray-400">
          1 · Create Notebook
        </h3>
        <label className="mb-1 block text-xs text-gray-400">Notebook title</label>
        <input
          type="text"
          value={notebookTitle}
          onChange={(e) => setNotebookTitle(e.target.value)}
          className="mb-3 w-full rounded-xl border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100 focus:outline-none focus:ring-2 focus:ring-brand-500"
          placeholder="My Knowledge Base"
        />
        <ActionButton
          onClick={handleUpload}
          disabled={!outputDir || isLoading || !isAuthenticated}
          icon={<CloudUpload className="h-4 w-4" />}
          label="Create Notebook"
          isLoading={isLoading}
        />
        {notebooks.length > 0 && (
          <div className="mt-3 rounded-xl bg-gray-800 p-3 text-xs text-gray-300">
            {notebooks.length} notebook{notebooks.length > 1 ? "s" : ""} created
          </div>
        )}
      </section>

      {notebooks.length > 0 && (
        <section className="rounded-2xl border border-gray-800 bg-gray-900/90 p-5 shadow-[0_20px_60px_rgba(0,0,0,0.35)]">
          <h3 className="mb-4 text-sm font-semibold uppercase tracking-[0.22em] text-gray-400">
            2 · Generate Studio Suite
          </h3>
          {notebooks.length > 1 && (
            <>
              <label className="mb-1 block text-xs text-gray-400">Select notebook</label>
              <select
                value={notebookId}
                onChange={(event) => onSelectedNotebookId(event.target.value)}
                className="mb-3 w-full rounded-xl border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100 focus:outline-none focus:ring-2 focus:ring-brand-500"
              >
                {notebooks.map((notebook) => (
                  <option key={notebook.notebook_id} value={notebook.notebook_id}>
                    {notebook.title}
                  </option>
                ))}
              </select>
            </>
          )}

          <div className="grid grid-cols-1 gap-2">
            <ActionButton
              onClick={() => void onGenerateArtifacts(["mind_map", "audio", "slides", "quiz"])}
              disabled={!notebookId || isLoading}
              icon={<Sparkles className="h-4 w-4" />}
              label="Generate Studio Suite"
              isLoading={isLoading}
            />
            <ActionButton
              onClick={() => void onGenerateArtifacts(["mind_map"])}
              disabled={!notebookId || isLoading}
              icon={<BrainCircuit className="h-4 w-4" />}
              label="Generate Mind Map"
              isLoading={false}
              tone="secondary"
            />
            <ActionButton
              onClick={() => void onGenerateArtifacts(["audio"])}
              disabled={!notebookId || isLoading}
              icon={<Headphones className="h-4 w-4" />}
              label="Generate Audio"
              isLoading={false}
              tone="secondary"
            />
            <ActionButton
              onClick={() => void onGenerateArtifacts(["slides", "quiz"])}
              disabled={!notebookId || isLoading}
              icon={<Presentation className="h-4 w-4" />}
              label="Generate Slides + Quiz"
              isLoading={false}
              tone="secondary"
            />
          </div>

          {currentJob && (
            <div className="mt-4 rounded-xl border border-white/10 bg-white/[0.04] p-3 text-sm text-gray-300">
              Job {currentJob.job_id}: {currentJob.status}
            </div>
          )}
        </section>
      )}

      {notebooks.length > 0 && (
        <section className="rounded-2xl border border-gray-800 bg-gray-900/90 p-5 shadow-[0_20px_60px_rgba(0,0,0,0.35)]">
          <h3 className="mb-4 text-sm font-semibold uppercase tracking-[0.22em] text-gray-400">
            3 · Export Bundle
          </h3>
          <ActionButton
            onClick={handleBundleExport}
            disabled={!notebookId}
            icon={<Download className="h-4 w-4" />}
            label="Download Notebook Bundle"
            isLoading={false}
            tone="secondary"
          />
        </section>
      )}

      {error && (
        <p className="rounded-xl border border-red-800 bg-red-900/30 px-4 py-3 text-sm text-red-300">
          {error}
        </p>
      )}
    </div>
  );
}

function AuthBadge({
  authenticated,
  checked,
  loading,
}: {
  authenticated: boolean;
  checked: boolean;
  loading: boolean;
}) {
  if (loading && !checked) {
    return (
      <div className="inline-flex items-center gap-2 rounded-full border border-gray-700 bg-gray-800 px-3 py-1 text-xs text-gray-300">
        <Loader2 className="h-3.5 w-3.5 animate-spin" />
        Checking
      </div>
    );
  }

  if (authenticated) {
    return (
      <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs text-emerald-300">
        <ShieldCheck className="h-3.5 w-3.5" />
        Ready
      </div>
    );
  }

  return (
    <div className="inline-flex items-center gap-2 rounded-full border border-amber-500/30 bg-amber-500/10 px-3 py-1 text-xs text-amber-300">
      Login Needed
    </div>
  );
}

function ActionButton({
  onClick,
  disabled,
  icon,
  label,
  isLoading,
  tone = "primary",
}: {
  onClick: () => void;
  disabled?: boolean;
  icon: ReactNode;
  label: string;
  isLoading: boolean;
  tone?: "primary" | "secondary";
}) {
  const toneClasses =
    tone === "primary"
      ? "bg-brand-500 text-slate-950 hover:bg-brand-400"
      : "border border-white/10 bg-white/[0.04] text-gray-100 hover:bg-white/[0.08]";

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`inline-flex items-center justify-center gap-2 rounded-xl px-4 py-3 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:bg-gray-800 disabled:text-gray-500 ${toneClasses}`}
    >
      {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : icon}
      {label}
    </button>
  );
}
