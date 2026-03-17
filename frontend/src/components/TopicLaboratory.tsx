interface TopicLaboratoryProps {
  data: {
    total_conversations: number;
    topics: Array<{
      topic: string;
      count: number;
      titles: string[];
    }>;
  };
  notebookCount: number;
}

export function TopicLaboratory({ data, notebookCount }: TopicLaboratoryProps) {
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      {data.topics.map((topic) => (
        <article
          key={topic.topic}
          className="rounded-3xl border border-gray-800 bg-gray-900/90 p-5 shadow-[0_20px_60px_rgba(0,0,0,0.25)]"
        >
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-[0.22em] text-gray-500">Cluster</p>
              <h3 className="mt-2 text-lg font-semibold text-white">{topic.topic}</h3>
            </div>
            <div className="rounded-2xl border border-cyan-500/20 bg-cyan-500/10 px-3 py-2 text-right">
              <p className="text-xs text-cyan-200">Conversations</p>
              <p className="text-xl font-semibold text-cyan-100">{topic.count}</p>
            </div>
          </div>

          <div className="mt-4 flex flex-wrap gap-2 text-xs">
            <span className="rounded-full bg-gray-800 px-3 py-1 text-gray-300">
              Source ready: {data.total_conversations > 0 ? "yes" : "no"}
            </span>
            <span className="rounded-full bg-gray-800 px-3 py-1 text-gray-300">
              Notebook sync: {notebookCount > 0 ? "connected" : "pending"}
            </span>
          </div>

          <div className="mt-5 space-y-2">
            {topic.titles.map((title) => (
              <div
                key={title}
                className="rounded-2xl border border-gray-800 bg-gray-950/70 px-4 py-3 text-sm text-gray-300"
              >
                {title}
              </div>
            ))}
          </div>
        </article>
      ))}
    </div>
  );
}
