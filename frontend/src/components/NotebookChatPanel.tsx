import { useState } from "react";
import { MessageSquare, Send } from "lucide-react";
import { ChatState } from "../hooks/useNotebook";

interface NotebookChatPanelProps {
  chat: ChatState;
  onAsk: (question: string) => Promise<unknown>;
  disabled?: boolean;
}

export function NotebookChatPanel({
  chat,
  onAsk,
  disabled = false,
}: NotebookChatPanelProps) {
  const [question, setQuestion] = useState("");
  const [isSending, setIsSending] = useState(false);

  const submit = async () => {
    if (!question.trim() || disabled || isSending) {
      return;
    }
    setIsSending(true);
    const currentQuestion = question.trim();
    setQuestion("");
    try {
      await onAsk(currentQuestion);
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div className="rounded-3xl border border-gray-800 bg-gray-900/90 p-5 shadow-[0_20px_60px_rgba(0,0,0,0.25)]">
      <div className="flex items-center gap-3">
        <div className="rounded-2xl border border-cyan-500/20 bg-cyan-500/10 p-3">
          <MessageSquare className="h-5 w-5 text-cyan-300" />
        </div>
        <div>
          <p className="text-xs uppercase tracking-[0.22em] text-gray-500">Notebook Chat</p>
          <h3 className="mt-1 text-lg font-semibold text-white">Ask this notebook</h3>
        </div>
      </div>

      <div className="mt-5 max-h-[26rem] space-y-4 overflow-auto">
        {chat.turns.length === 0 ? (
          <div className="rounded-2xl border border-gray-800 bg-gray-950/70 px-4 py-4 text-sm text-gray-400">
            Ask a question about the selected notebook. Follow-up questions will stay in the same NotebookLM conversation.
          </div>
        ) : (
          chat.turns.map((turn, index) => (
            <div key={`${turn.question}-${index}`} className="space-y-2">
              <div className="rounded-2xl bg-cyan-500/10 px-4 py-3 text-sm text-cyan-50">
                <p className="text-xs uppercase tracking-[0.18em] text-cyan-200/80">You</p>
                <p className="mt-2 whitespace-pre-wrap">{turn.question}</p>
              </div>
              <div className="rounded-2xl border border-gray-800 bg-gray-950/80 px-4 py-3 text-sm text-gray-200">
                <p className="text-xs uppercase tracking-[0.18em] text-gray-500">NotebookLM</p>
                <p className="mt-2 whitespace-pre-wrap">{turn.answer}</p>
              </div>
            </div>
          ))
        )}
      </div>

      <div className="mt-5 flex gap-2">
        <input
          type="text"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              void submit();
            }
          }}
          placeholder="What are the key themes in this notebook?"
          disabled={disabled || isSending}
          className="flex-1 rounded-2xl border border-gray-700 bg-gray-950 px-4 py-3 text-sm text-gray-100 focus:outline-none focus:ring-2 focus:ring-cyan-500"
        />
        <button
          onClick={() => void submit()}
          disabled={disabled || isSending || !question.trim()}
          className="inline-flex items-center gap-2 rounded-2xl bg-cyan-500 px-4 py-3 text-sm font-medium text-slate-950 transition-colors hover:bg-cyan-400 disabled:bg-gray-700 disabled:text-gray-400"
        >
          <Send className="h-4 w-4" />
          Ask
        </button>
      </div>
    </div>
  );
}
