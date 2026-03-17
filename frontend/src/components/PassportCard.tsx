import { useMemo, useState } from "react";
import { Clipboard, ClipboardCheck, FileText, Sparkles, User } from "lucide-react";

const API_BASE = "/api";

interface PassportCardProps {
  exportFile: File | null;
  onGenerated?: (passportId: string | null) => void;
}

interface PassportSection {
  title: string;
  bullets: string[];
  paragraphs: string[];
}

interface PassportMetric {
  label: string;
  value: string;
}

export function PassportCard({ exportFile, onGenerated }: PassportCardProps) {
  const [markdown, setMarkdown] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState("");
  const [showRaw, setShowRaw] = useState(false);

  const parsed = useMemo(() => parsePassport(markdown), [markdown]);

  const generate = async () => {
    if (!exportFile) return;
    setLoading(true);
    setError("");

    const form = new FormData();
    form.append("file", exportFile);

    try {
      const res = await fetch(`${API_BASE}/persona`, { method: "POST", body: form });
      const text = await res.text();
      if (!res.ok) {
        throw new Error(readErrorText(text));
      }
      const data = JSON.parse(text) as { passport_markdown: string; passport_id?: string };
      setMarkdown(data.passport_markdown);
      onGenerated?.(data.passport_id ?? null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = () => {
    if (!markdown) return;
    navigator.clipboard.writeText(markdown).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <div className="overflow-hidden rounded-[28px] border border-cyan-500/20 bg-[radial-gradient(circle_at_top_left,_rgba(34,211,238,0.16),_transparent_30%),linear-gradient(180deg,_rgba(10,15,25,0.98),_rgba(3,7,18,0.98))] shadow-[0_30px_80px_rgba(0,0,0,0.45)]">
      <div className="border-b border-white/10 px-6 py-5">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="rounded-2xl border border-cyan-400/20 bg-cyan-400/10 p-3">
              <User className="h-5 w-5 text-cyan-300" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white">Digital Passport</h3>
              <p className="mt-1 text-sm text-gray-400">
                A cleaner handoff profile for a new AI assistant.
              </p>
            </div>
          </div>

          {markdown && (
            <button
              onClick={copyToClipboard}
              className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-gray-200 transition-colors hover:bg-white/10"
            >
              {copied ? (
                <>
                  <ClipboardCheck className="h-4 w-4 text-emerald-400" />
                  Copied
                </>
              ) : (
                <>
                  <Clipboard className="h-4 w-4" />
                  Copy Markdown
                </>
              )}
            </button>
          )}
        </div>
      </div>

      {!markdown ? (
        <div className="px-6 py-8">
          <div className="rounded-3xl border border-dashed border-cyan-400/20 bg-white/[0.03] p-8 text-center">
            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-cyan-400/10">
              <Sparkles className="h-7 w-7 text-cyan-300" />
            </div>
            <p className="mx-auto max-w-xl text-sm leading-6 text-gray-300">
              Generate a structured profile that summarizes style, topics, and a reusable
              working prompt from this export.
            </p>
            <button
              onClick={generate}
              disabled={!exportFile || loading}
              className="mt-6 inline-flex items-center justify-center rounded-2xl bg-cyan-500 px-5 py-3 text-sm font-medium text-slate-950 transition-colors hover:bg-cyan-400 disabled:cursor-not-allowed disabled:bg-gray-700 disabled:text-gray-400"
            >
              {loading ? "Generating passport..." : "Generate Digital Passport"}
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-6 px-6 py-6">
          {parsed.metrics.length > 0 && (
            <div className="grid gap-3 md:grid-cols-3">
              {parsed.metrics.map((metric) => (
                <div
                  key={metric.label}
                  className="rounded-2xl border border-white/10 bg-white/[0.04] p-4"
                >
                  <p className="text-xs uppercase tracking-[0.22em] text-gray-500">
                    {metric.label}
                  </p>
                  <p className="mt-2 text-lg font-semibold text-white">{metric.value}</p>
                </div>
              ))}
            </div>
          )}

          <div className="grid gap-4 lg:grid-cols-2">
            {parsed.sections.map((section) => (
              <section
                key={section.title}
                className="rounded-3xl border border-white/10 bg-white/[0.04] p-5"
              >
                <div className="mb-4 flex items-center gap-2">
                  <FileText className="h-4 w-4 text-cyan-300" />
                  <h4 className="text-sm font-semibold uppercase tracking-[0.22em] text-gray-300">
                    {section.title}
                  </h4>
                </div>
                {section.paragraphs.map((paragraph, index) => (
                  <p key={`${section.title}-p-${index}`} className="mb-3 text-sm leading-6 text-gray-300">
                    {paragraph}
                  </p>
                ))}
                {section.bullets.length > 0 && (
                  <div className="space-y-2">
                    {section.bullets.map((bullet, index) => (
                      <div
                        key={`${section.title}-b-${index}`}
                        className="rounded-2xl border border-cyan-500/10 bg-slate-950/40 px-4 py-3 text-sm text-gray-200"
                      >
                        {bullet}
                      </div>
                    ))}
                  </div>
                )}
              </section>
            ))}
          </div>

          <button
            onClick={() => setShowRaw((value) => !value)}
            className="text-sm text-cyan-300 transition-colors hover:text-cyan-200"
          >
            {showRaw ? "Hide raw markdown" : "Show raw markdown"}
          </button>

          {showRaw && (
            <pre className="max-h-80 overflow-auto rounded-2xl border border-white/10 bg-slate-950/80 p-4 text-xs leading-6 text-gray-300 whitespace-pre-wrap">
              {markdown}
            </pre>
          )}
        </div>
      )}

      {error && <p className="px-6 pb-6 text-sm text-red-400">{error}</p>}
    </div>
  );
}

function parsePassport(markdown: string | null): {
  metrics: PassportMetric[];
  sections: PassportSection[];
} {
  if (!markdown) {
    return { metrics: [], sections: [] };
  }

  const lines = markdown
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line && line !== "---");

  const metrics: PassportMetric[] = [];
  const sections: PassportSection[] = [];
  let currentSection: PassportSection | null = null;

  for (const line of lines) {
    if (line.startsWith("|") && !line.includes("---")) {
      const cells = line
        .split("|")
        .map((cell) => cell.trim())
        .filter(Boolean);
      if (cells.length >= 2 && cells[0] !== "Metric") {
        metrics.push({ label: cells[0], value: cells[1] });
      }
      continue;
    }

    if (line.startsWith("## ")) {
      currentSection = {
        title: line.replace(/^##\s+/, ""),
        bullets: [],
        paragraphs: [],
      };
      sections.push(currentSection);
      continue;
    }

    if (!currentSection || line.startsWith("# ")) {
      continue;
    }

    if (line.startsWith("- ")) {
      currentSection.bullets.push(line.slice(2));
    } else {
      currentSection.paragraphs.push(line);
    }
  }

  return { metrics, sections };
}

function readErrorText(text: string): string {
  if (!text) {
    return "Request failed.";
  }

  try {
    const parsed = JSON.parse(text) as { detail?: string };
    if (parsed.detail) {
      return parsed.detail;
    }
  } catch {
    return text;
  }

  return text;
}
