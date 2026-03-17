import { useEffect, useState } from "react";
import {
  BrainCircuit,
  CloudUpload,
  Headphones,
  Loader2,
  LogIn,
  Presentation,
  RefreshCw,
  ShieldCheck,
  ShieldX,
} from "lucide-react";
import { useNotebook } from "../hooks/useNotebook";

const API_BASE = "/api";

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
      if (data.authenticated) {
        setAuthMessage("NotebookLM session is connected.");
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setAuthMessage(message);
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
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
      });
      const text = await res.text();

      if (!res.ok) {
        throw new Error(text || `HTTP ${res.status}`);
      }

      const data = JSON.parse(text) as { message?: string; status?: string };
      setAuthMessage(
        data.message ||
          "Login flow started. If no browser appears in Docker, provide a valid .byegpt/storage.json session file."
      );
      window.setTimeout(() => {
        void refreshAuthStatus();
      }, 2500);
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setAuthMessage(message);
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

    const ids = await uploadToNotebookLM(outputDir, notebookTitle);
    if (ids.length) {
      onNotebookIds(ids);
      setActiveNotebook(ids[0]);
    }
  };

  const notebookId = activeNotebook || notebookIds[0] || "";

  return (
    <div className="flex flex-col gap-6">
      <section className="rounded-2xl border border-gray-800 bg-gray-900/90 p-5 shadow-[0_20px_60px_rgba(0,0,0,0.35)]">
        <div className="mb-4 flex items-center justify-between gap-3">
          <div>
            <h3 className="text-sm font-semibold uppercase tracking-[0.22em] text-gray-400">
              NotebookLM Access
            </h3>
            <p className="mt-1 text-xs text-gray-500">
              Connect a saved Google session before uploading converted files.
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
            label={isAuthenticated ? "Reconnect Session" : "Start Login"}
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

        <div className="mt-4 rounded-xl border border-amber-500/20 bg-amber-500/10 p-3 text-xs text-amber-100">
          In Docker, browser login may not open on your host. If refresh never turns green,
          place a valid Playwright session file at <code>.byegpt/storage.json</code> and
          refresh status.
        </div>

        {authMessage && (
          <p className="mt-3 text-sm text-gray-300">{authMessage}</p>
        )}
      </section>

      <section className="rounded-2xl border border-gray-800 bg-gray-900/90 p-5 shadow-[0_20px_60px_rgba(0,0,0,0.35)]">
        <h3 className="mb-4 text-sm font-semibold uppercase tracking-[0.22em] text-gray-400">
          1 · Upload To NotebookLM
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
          label="Upload to NotebookLM"
          isLoading={isLoading}
        />
        {!isAuthenticated && (
          <p className="mt-3 text-xs text-amber-300">
            Connect NotebookLM first. The backend needs a saved Google session.
          </p>
        )}
        {notebookIds.length > 0 && (
          <div className="mt-3 rounded-xl bg-gray-800 p-3 text-xs text-gray-300">
            {notebookIds.length} notebook{notebookIds.length > 1 ? "s" : ""} created
          </div>
        )}
      </section>

      {notebookIds.length > 0 && (
        <section className="rounded-2xl border border-gray-800 bg-gray-900/90 p-5 shadow-[0_20px_60px_rgba(0,0,0,0.35)]">
          <h3 className="mb-4 text-sm font-semibold uppercase tracking-[0.22em] text-gray-400">
            2 · Generate Artifacts
          </h3>
          {notebookIds.length > 1 && (
            <>
              <label className="mb-1 block text-xs text-gray-400">Select notebook</label>
              <select
                value={activeNotebook}
                onChange={(e) => setActiveNotebook(e.target.value)}
                className="mb-3 w-full rounded-xl border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100 focus:outline-none focus:ring-2 focus:ring-brand-500"
              >
                {notebookIds.map((id) => (
                  <option key={id} value={id}>
                    {id.substring(0, 16)}...
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
        Connected
      </div>
    );
  }

  return (
    <div className="inline-flex items-center gap-2 rounded-full border border-red-500/30 bg-red-500/10 px-3 py-1 text-xs text-red-300">
      <ShieldX className="h-3.5 w-3.5" />
      Not connected
    </div>
  );
}

interface ActionButtonProps {
  onClick: () => void;
  disabled: boolean;
  icon: React.ReactNode;
  label: string;
  isLoading?: boolean;
  tone?: "primary" | "secondary";
}

function ActionButton({
  onClick,
  disabled,
  icon,
  label,
  isLoading,
  tone = "primary",
}: ActionButtonProps) {
  const toneClass =
    tone === "secondary"
      ? "bg-gray-800 text-gray-200 hover:bg-gray-700"
      : "bg-brand-600 text-white hover:bg-brand-700";

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`flex w-full items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:bg-gray-700 disabled:text-gray-400 ${toneClass}`}
    >
      {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : icon}
      {label}
    </button>
  );
}
