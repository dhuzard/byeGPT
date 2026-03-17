import React, { useCallback, useRef, useState } from "react";
import { AlertCircle, CheckCircle2, FileArchive } from "lucide-react";
import * as tus from "tus-js-client";
import { TaxonomyData } from "../hooks/useNotebook";

const API_BASE = "/api";
const viteEnv = (import.meta as ImportMeta & {
  env?: Record<string, string | undefined>;
}).env;
const TUSD_ENDPOINT =
  viteEnv?.VITE_TUSD_ENDPOINT?.trim() || "http://127.0.0.1:1080/files";

interface ConvertResult {
  output_dir: string;
  files_created: number;
  attachment_count: number;
  conversation_count: number;
  file_paths: string[];
  taxonomy?: TaxonomyData;
}

interface IngestionDropzoneProps {
  onConverted?: (result: ConvertResult) => void;
  onFileSelected?: (file: File | null) => void;
}

export function IngestionDropzone({
  onConverted,
  onFileSelected,
}: IngestionDropzoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [status, setStatus] = useState<
    "idle" | "uploading" | "processing" | "done" | "error"
  >("idle");
  const [result, setResult] = useState<ConvertResult | null>(null);
  const [errorMsg, setErrorMsg] = useState("");
  const [uploadProgress, setUploadProgress] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const uploadFile = useCallback(
    async (file: File) => {
      const normalizedName = file.name.toLowerCase();
      if (!(normalizedName.endsWith(".zip") || normalizedName.endsWith(".json"))) {
        setStatus("error");
        setResult(null);
        setUploadProgress(0);
        setErrorMsg("Unsupported file type. Upload a .zip export or conversations.json.");
        onFileSelected?.(null);
        return;
      }

      setStatus("uploading");
      setResult(null);
      setErrorMsg("");
      setUploadProgress(0);
      onFileSelected?.(file);

      const upload = new tus.Upload(file, {
        endpoint: TUSD_ENDPOINT,
        chunkSize: 5 * 1024 * 1024,
        retryDelays: [0, 1000, 3000, 5000],
        removeFingerprintOnSuccess: true,
        metadata: {
          filename: file.name,
          filetype: file.type,
        },
        onError(error) {
          setErrorMsg(error.message);
          setStatus("error");
        },
        onProgress(bytesUploaded, bytesTotal) {
          setUploadProgress(Math.round((bytesUploaded / bytesTotal) * 100));
        },
        async onSuccess() {
          try {
            setStatus("processing");

            const uploadUrl = upload.url;
            if (!uploadUrl) {
              throw new Error("Tus upload completed without a resumable URL.");
            }

            const uploadId = new URL(uploadUrl).pathname.split("/").pop();
            if (!uploadId) {
              throw new Error("Could not determine the uploaded file ID.");
            }

            const response = await fetch(`${API_BASE}/convert/tus/${uploadId}`, {
              method: "POST",
            });
            if (!response.ok) {
              throw new Error(await response.text());
            }

            const data = (await response.json()) as ConvertResult;
            setResult(data);
            setStatus("done");
            onConverted?.(data);
          } catch (error) {
            const message = error instanceof Error ? error.message : String(error);
            setErrorMsg(message);
            setStatus("error");
          }
        },
      });

      upload.start();
    },
    [onConverted, onFileSelected]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) {
        void uploadFile(file);
      }
    },
    [uploadFile]
  );

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) {
        void uploadFile(file);
      }
    },
    [uploadFile]
  );

  const isBusy = status === "uploading" || status === "processing";
  const progressWidth = status === "processing" ? 100 : uploadProgress;

  return (
    <div className="w-full">
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => {
          if (!isBusy) {
            inputRef.current?.click();
          }
        }}
        className={`
          relative flex cursor-pointer flex-col items-center justify-center gap-4 rounded-2xl
          border-2 border-dashed p-12 transition-colors
          ${
            isDragging
              ? "border-brand-500 bg-brand-500/10"
              : "border-gray-700 bg-gray-900 hover:border-gray-500 hover:bg-gray-800"
          }
          ${isBusy ? "pointer-events-none opacity-60" : ""}
        `}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".zip,.json"
          className="hidden"
          onChange={handleFileChange}
          disabled={isBusy}
        />

        {status === "idle" || status === "uploading" || status === "processing" ? (
          <>
            <div className="rounded-full bg-gray-800 p-4">
              <FileArchive className="h-10 w-10 text-brand-500" />
            </div>
            <div className="text-center">
              <p className="text-lg font-semibold text-gray-100">
                {status === "uploading"
                  ? "Uploading export..."
                  : status === "processing"
                    ? "Processing export..."
                    : "Drop your ChatGPT export here"}
              </p>
              <p className="mt-1 text-sm text-gray-400">
                Accepts <code>.zip</code> or <code>conversations.json</code>
              </p>
            </div>
            {isBusy && (
              <>
                <div className="h-1.5 w-40 overflow-hidden rounded-full bg-gray-700">
                  <div
                    className="h-full rounded-full bg-brand-500 transition-all"
                    style={{ width: `${progressWidth}%` }}
                  />
                </div>
                <div className="mt-2 text-sm text-gray-300">
                  {status === "uploading"
                    ? `Upload progress: ${uploadProgress}%`
                    : "Upload complete. Running conversion..."}
                </div>
              </>
            )}
          </>
        ) : status === "done" && result ? (
          <div className="flex flex-col items-center gap-3 text-center">
            <CheckCircle2 className="h-12 w-12 text-green-400" />
            <p className="text-lg font-semibold text-green-400">Conversion complete!</p>
            <div className="mt-2 grid grid-cols-3 gap-4 text-sm text-gray-300">
              <Stat label="Conversations" value={result.conversation_count} />
              <Stat label="Files created" value={result.files_created} />
              <Stat label="Attachments" value={result.attachment_count} />
            </div>
            <p className="mt-1 text-xs text-gray-500">
              Output: <code>{result.output_dir}</code>
            </p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-2 text-center">
            <AlertCircle className="h-10 w-10 text-red-400" />
            <p className="font-medium text-red-400">Conversion failed</p>
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
