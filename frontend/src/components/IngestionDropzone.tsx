/**
 * IngestionDropzone — drag-and-drop area for uploading a ChatGPT .zip export.
 *
 * Displays a real-time topic cluster view once the parse is complete.
 */

import React, { useCallback, useRef, useState } from "react";
import { Upload, FileArchive, CheckCircle2, AlertCircle } from "lucide-react";

const API_BASE = "/api";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface ConvertResult {
  output_dir: string;
  files_created: number;
  attachment_count: number;
  conversation_count: number;
  file_paths: string[];
}

interface IngestionDropzoneProps {
  onConverted?: (result: ConvertResult) => void;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function IngestionDropzone({ onConverted }: IngestionDropzoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [status, setStatus] = useState<"idle" | "uploading" | "done" | "error">("idle");
  const [result, setResult] = useState<ConvertResult | null>(null);
  const [errorMsg, setErrorMsg] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const uploadFile = useCallback(
    async (file: File) => {
      setStatus("uploading");
      setErrorMsg("");

      const form = new FormData();
      form.append("file", file);

      try {
        const res = await fetch(`${API_BASE}/convert`, {
          method: "POST",
          body: form,
        });

        if (!res.ok) {
          const detail = await res.text();
          throw new Error(detail || `HTTP ${res.status}`);
        }

        const data: ConvertResult = await res.json();
        setResult(data);
        setStatus("done");
        onConverted?.(data);
      } catch (err) {
        setErrorMsg(String(err));
        setStatus("error");
      }
    },
    [onConverted]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) uploadFile(file);
    },
    [uploadFile]
  );

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) uploadFile(file);
    },
    [uploadFile]
  );

  return (
    <div className="w-full">
      <div
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={`
          relative flex flex-col items-center justify-center gap-4 rounded-2xl border-2 border-dashed
          p-12 cursor-pointer transition-colors
          ${isDragging
            ? "border-brand-500 bg-brand-500/10"
            : "border-gray-700 bg-gray-900 hover:border-gray-500 hover:bg-gray-800"}
          ${status === "uploading" ? "pointer-events-none opacity-60" : ""}
        `}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".zip,.json"
          className="hidden"
          onChange={handleFileChange}
        />

        {status === "idle" || status === "uploading" ? (
          <>
            <div className="rounded-full bg-gray-800 p-4">
              <FileArchive className="h-10 w-10 text-brand-500" />
            </div>
            <div className="text-center">
              <p className="text-lg font-semibold text-gray-100">
                {status === "uploading" ? "Converting…" : "Drop your ChatGPT export here"}
              </p>
              <p className="mt-1 text-sm text-gray-400">
                Accepts <code>.zip</code> or <code>conversations.json</code>
              </p>
            </div>
            {status === "uploading" && (
              <div className="h-1.5 w-40 overflow-hidden rounded-full bg-gray-700">
                <div className="h-full animate-pulse bg-brand-500 rounded-full w-3/4" />
              </div>
            )}
          </>
        ) : status === "done" && result ? (
          <div className="flex flex-col items-center gap-3 text-center">
            <CheckCircle2 className="h-12 w-12 text-green-400" />
            <p className="text-lg font-semibold text-green-400">Conversion complete!</p>
            <div className="grid grid-cols-3 gap-4 mt-2 text-sm text-gray-300">
              <Stat label="Conversations" value={result.conversation_count} />
              <Stat label="Files created" value={result.files_created} />
              <Stat label="Attachments" value={result.attachment_count} />
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Output: <code>{result.output_dir}</code>
            </p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-2 text-center">
            <AlertCircle className="h-10 w-10 text-red-400" />
            <p className="text-red-400 font-medium">Conversion failed</p>
            <p className="text-xs text-gray-400">{errorMsg}</p>
          </div>
        )}
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg bg-gray-800 px-4 py-3">
      <p className="text-2xl font-bold text-brand-400">{value.toLocaleString()}</p>
      <p className="text-xs text-gray-400">{label}</p>
    </div>
  );
}
