import { useEffect, useState } from "react";
import { Loader2, Search } from "lucide-react";

const API_BASE = "/api";

interface SearchPanelProps {
  outputDir: string;
}

interface SearchResult {
  document: string;
  metadata: {
    filename?: string;
    source?: string;
  };
  distance?: number;
}

export function SearchPanel({ outputDir }: SearchPanelProps) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState("Not indexed yet.");
  const [isIndexed, setIsIndexed] = useState(false);

  const refreshStatus = async () => {
    try {
      const response = await fetch(`${API_BASE}/search/index/status`);
      const data = (await response.json()) as { ready: boolean; document_count: number };
      setIsIndexed(Boolean(data.ready));
      setStatus(
        data.ready
          ? `${data.document_count.toLocaleString()} searchable chunks ready`
          : "Index is empty"
      );
    } catch {
      setStatus("Search service unavailable");
      setIsIndexed(false);
    }
  };

  useEffect(() => {
    void refreshStatus();
  }, []);

  const buildIndex = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`${API_BASE}/search/index`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ input_dir: outputDir }),
      });
      const data = (await response.json()) as { document_count?: number };
      setIsIndexed(true);
      setStatus(`${(data.document_count || 0).toLocaleString()} searchable chunks ready`);
    } finally {
      setIsLoading(false);
    }
  };

  const runQuery = async () => {
    if (!query.trim()) return;
    setIsLoading(true);
    try {
      const response = await fetch(`${API_BASE}/search/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: query, n_results: 6 }),
      });
      const data = (await response.json()) as { results: SearchResult[] };
      setResults(data.results);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="rounded-3xl border border-gray-800 bg-gray-900/90 p-5 shadow-[0_20px_60px_rgba(0,0,0,0.25)]">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.22em] text-gray-500">Chroma Search</p>
          <h3 className="mt-2 text-lg font-semibold text-white">Query your archive locally</h3>
        </div>
        <button
          onClick={buildIndex}
          disabled={isLoading}
          className="rounded-2xl bg-cyan-500 px-4 py-2 text-sm font-medium text-slate-950 transition-colors hover:bg-cyan-400 disabled:bg-gray-700 disabled:text-gray-400"
        >
          {isLoading && !isIndexed ? "Building..." : isIndexed ? "Rebuild Index" : "Build Index"}
        </button>
      </div>

      <p className="mt-3 text-sm text-gray-400">{status}</p>

      <div className="mt-5 flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search for an old topic, decision, or snippet"
          className="flex-1 rounded-2xl border border-gray-700 bg-gray-950 px-4 py-3 text-sm text-gray-100 focus:outline-none focus:ring-2 focus:ring-cyan-500"
          onKeyDown={(e) => e.key === "Enter" && void runQuery()}
        />
        <button
          onClick={runQuery}
          disabled={!isIndexed || isLoading}
          className="inline-flex items-center gap-2 rounded-2xl border border-gray-700 bg-gray-800 px-4 py-3 text-sm text-gray-100 transition-colors hover:bg-gray-700 disabled:opacity-60"
        >
          {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
          Search
        </button>
      </div>

      <div className="mt-5 space-y-3">
        {results.map((result, index) => (
          <div
            key={`${result.metadata.source}-${index}`}
            className="rounded-2xl border border-gray-800 bg-gray-950/80 px-4 py-4"
          >
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm font-medium text-white">
                {result.metadata.filename || result.metadata.source || "Result"}
              </p>
              {typeof result.distance === "number" && (
                <span className="text-xs text-gray-500">distance {result.distance.toFixed(3)}</span>
              )}
            </div>
            <p className="mt-2 text-sm leading-6 text-gray-300">
              {result.document.slice(0, 220)}
              {result.document.length > 220 ? "..." : ""}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
