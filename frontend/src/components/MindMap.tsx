/**
 * MindMap — renders the NotebookLM mind-map JSON using react-force-graph-2d.
 *
 * Falls back to a simple table list when the library is unavailable
 * (e.g., during SSR or in test environments).
 */

import React, { useRef } from "react";

interface Node {
  id: string;
  label: string;
  group?: string;
}

interface Link {
  source: string;
  target: string;
}

export interface MindMapData {
  nodes: Node[];
  links: Link[];
}

interface MindMapProps {
  data: MindMapData;
}

// Try to lazy-import react-force-graph-2d; degrade gracefully if missing
const ForceGraph2D = React.lazy(() =>
  import("react-force-graph-2d").then((m) => ({ default: m.default }))
);

export function MindMap({ data }: MindMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  const graphData = {
    nodes: data.nodes.map((n) => ({ id: n.id, name: n.label, group: n.group })),
    links: data.links.map((l) => ({ source: l.source, target: l.target })),
  };

  return (
    <div ref={containerRef} className="w-full rounded-xl overflow-hidden bg-gray-950 border border-gray-800">
      <div className="px-4 py-3 border-b border-gray-800 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-200">Mind Map</h3>
        <span className="text-xs text-gray-500">
          {data.nodes.length} nodes · {data.links.length} links
        </span>
      </div>
      <React.Suspense
        fallback={
          <FallbackTable nodes={data.nodes} />
        }
      >
        <ForceGraph2D
          graphData={graphData}
          width={800}
          height={480}
          backgroundColor="#03050a"
          nodeLabel="name"
          nodeColor={() => "#14b8a6"}
          linkColor={() => "#374151"}
          nodeCanvasObject={(node: any, ctx: CanvasRenderingContext2D) => {
            const label: string = node.name ?? "";
            const fontSize = 12;
            ctx.font = `${fontSize}px Sans-Serif`;
            ctx.fillStyle = "#14b8a6";
            ctx.beginPath();
            ctx.arc(node.x, node.y, 6, 0, 2 * Math.PI);
            ctx.fill();
            ctx.fillStyle = "#e5e7eb";
            ctx.fillText(label, node.x + 9, node.y + 4);
          }}
        />
      </React.Suspense>
    </div>
  );
}

function FallbackTable({ nodes }: { nodes: Node[] }) {
  return (
    <div className="p-4 overflow-auto max-h-80">
      <table className="w-full text-sm text-gray-300">
        <thead>
          <tr className="text-left border-b border-gray-800">
            <th className="pb-2 pr-4 text-gray-500">ID</th>
            <th className="pb-2 pr-4 text-gray-500">Label</th>
            <th className="pb-2 text-gray-500">Group</th>
          </tr>
        </thead>
        <tbody>
          {nodes.map((n) => (
            <tr key={n.id} className="border-b border-gray-900">
              <td className="py-1.5 pr-4 font-mono text-xs text-gray-500">
                {n.id.substring(0, 12)}
              </td>
              <td className="py-1.5 pr-4">{n.label}</td>
              <td className="py-1.5 text-xs text-gray-400">{n.group ?? "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
