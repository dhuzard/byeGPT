/**
 * PassportCard — "Digital Passport" preview card.
 *
 * Shows the synthesised persona Markdown and a "Sync Persona as Global Context"
 * button that copies it to the clipboard.
 */

import React, { useState } from "react";
import { Clipboard, ClipboardCheck, User } from "lucide-react";

const API_BASE = "/api";

interface PassportCardProps {
  exportFile: File | null;
}

export function PassportCard({ exportFile }: PassportCardProps) {
  const [markdown, setMarkdown] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState("");

  const generate = async () => {
    if (!exportFile) return;
    setLoading(true);
    setError("");

    const form = new FormData();
    form.append("file", exportFile);

    try {
      const res = await fetch(`${API_BASE}/persona`, { method: "POST", body: form });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setMarkdown(data.passport_markdown);
    } catch (err) {
      setError(String(err));
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
    <div className="rounded-xl bg-gray-900 border border-gray-800 p-5">
      <div className="flex items-center gap-3 mb-4">
        <div className="rounded-full bg-gray-800 p-2">
          <User className="h-5 w-5 text-brand-400" />
        </div>
        <h3 className="font-semibold text-gray-100">Digital Passport</h3>
      </div>

      {!markdown ? (
        <button
          onClick={generate}
          disabled={!exportFile || loading}
          className="w-full rounded-lg bg-brand-600 hover:bg-brand-700 disabled:bg-gray-700
                     disabled:cursor-not-allowed px-4 py-2.5 text-sm font-medium text-white transition-colors"
        >
          {loading ? "Generating…" : "Generate Digital Passport"}
        </button>
      ) : (
        <>
          <pre className="rounded-lg bg-gray-950 p-3 text-xs text-gray-300 overflow-auto max-h-40 whitespace-pre-wrap mb-3">
            {markdown.slice(0, 600)}
            {markdown.length > 600 ? "\n…" : ""}
          </pre>
          <button
            onClick={copyToClipboard}
            className="flex items-center gap-2 w-full justify-center rounded-lg
                       bg-gray-800 hover:bg-gray-700 px-4 py-2 text-sm text-gray-200 transition-colors"
          >
            {copied
              ? <><ClipboardCheck className="h-4 w-4 text-green-400" /> Copied!</>
              : <><Clipboard className="h-4 w-4" /> Sync Persona as Global Context</>}
          </button>
        </>
      )}

      {error && (
        <p className="mt-2 text-xs text-red-400">{error}</p>
      )}
    </div>
  );
}
