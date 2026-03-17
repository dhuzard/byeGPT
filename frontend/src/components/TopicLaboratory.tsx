import { useMemo, useState } from "react";
import { TaxonomyData } from "../hooks/useNotebook";

interface TopicLaboratoryProps {
  taxonomy: TaxonomyData;
  notebookCount: number;
  selectable?: boolean;
  disabled?: boolean;
  onCreateThematicNotebook?: (selections: Array<{ category: string; subcategory: string }>) => void;
}

export function TopicLaboratory({
  taxonomy,
  notebookCount,
  selectable = false,
  disabled = false,
  onCreateThematicNotebook,
}: TopicLaboratoryProps) {
  const [selectedKeys, setSelectedKeys] = useState<string[]>([]);

  const selectedSelections = useMemo(
    () =>
      selectedKeys.map((key) => {
        const [category, subcategory] = key.split("::");
        return { category, subcategory };
      }),
    [selectedKeys],
  );

  const toggleSelection = (category: string, subcategory: string) => {
    const key = `${category}::${subcategory}`;
    setSelectedKeys((current) =>
      current.includes(key)
        ? current.filter((entry) => entry !== key)
        : [...current, key],
    );
  };

  return (
    <div className="space-y-5">
      {taxonomy.suggested_notebooks && taxonomy.suggested_notebooks.length > 0 && (
        <div className="rounded-3xl border border-gray-800 bg-gray-900/90 p-5">
          <p className="text-xs uppercase tracking-[0.22em] text-gray-500">Suggested notebooks</p>
          <div className="mt-4 grid gap-3 md:grid-cols-3">
            {taxonomy.suggested_notebooks.map((item) => (
              <div key={item.title} className="rounded-2xl border border-gray-800 bg-gray-950/70 p-4">
                <p className="text-sm font-semibold text-white">{item.title}</p>
                <p className="mt-2 text-xs text-gray-400">{item.subcategories.join(", ")}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-2">
        {taxonomy.categories.map((category) => (
          <article
            key={category.slug}
            className="rounded-3xl border border-gray-800 bg-gray-900/90 p-5 shadow-[0_20px_60px_rgba(0,0,0,0.25)]"
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-xs uppercase tracking-[0.22em] text-gray-500">Category</p>
                <h3 className="mt-2 text-lg font-semibold text-white">{category.name}</h3>
                <p className="mt-2 text-sm text-gray-400">{category.representative_titles?.[0]}</p>
              </div>
              <div className="rounded-2xl border border-cyan-500/20 bg-cyan-500/10 px-3 py-2 text-right">
                <p className="text-xs text-cyan-200">Chats</p>
                <p className="text-xl font-semibold text-cyan-100">{category.count}</p>
              </div>
            </div>

            <div className="mt-4 flex flex-wrap gap-2 text-xs">
              <span className="rounded-full bg-gray-800 px-3 py-1 text-gray-300">
                Source ready: {taxonomy.total_conversations > 0 ? "yes" : "no"}
              </span>
              <span className="rounded-full bg-gray-800 px-3 py-1 text-gray-300">
                Notebook sync: {notebookCount > 0 ? "connected" : "pending"}
              </span>
            </div>

            <div className="mt-5 space-y-3">
              {category.subcategories.map((subcategory) => {
                const key = `${category.slug}::${subcategory.slug}`;
                const checked = selectedKeys.includes(key);
                return (
                  <label
                    key={key}
                    className={`block rounded-2xl border px-4 py-3 text-sm ${
                      checked
                        ? "border-cyan-400/40 bg-cyan-500/10 text-cyan-100"
                        : "border-gray-800 bg-gray-950/70 text-gray-300"
                    } ${selectable && !disabled ? "cursor-pointer" : ""}`}
                  >
                    <div className="flex items-start gap-3">
                      {selectable && (
                        <input
                          type="checkbox"
                          checked={checked}
                          disabled={disabled}
                          onChange={() => toggleSelection(category.slug, subcategory.slug)}
                          className="mt-1"
                        />
                      )}
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{subcategory.name}</span>
                          <span className="text-xs text-gray-500">{subcategory.count} chats</span>
                        </div>
                        {subcategory.representative_titles && subcategory.representative_titles.length > 0 && (
                          <p className="mt-2 text-xs text-gray-400">
                            {subcategory.representative_titles.slice(0, 2).join(" · ")}
                          </p>
                        )}
                      </div>
                    </div>
                  </label>
                );
              })}
            </div>
          </article>
        ))}
      </div>

      {selectable && onCreateThematicNotebook && (
        <div className="flex items-center justify-between rounded-3xl border border-gray-800 bg-gray-900/90 px-5 py-4">
          <div>
            <p className="text-sm font-semibold text-white">Thematic notebook builder</p>
            <p className="text-xs text-gray-400">
              {selectedSelections.length} subcategor{selectedSelections.length === 1 ? "y" : "ies"} selected
            </p>
          </div>
          <button
            onClick={() => onCreateThematicNotebook(selectedSelections)}
            disabled={disabled || selectedSelections.length === 0}
            className="rounded-2xl bg-cyan-500 px-4 py-3 text-sm font-medium text-slate-950 transition-colors hover:bg-cyan-400 disabled:bg-gray-700 disabled:text-gray-400"
          >
            Create Thematic Notebook
          </button>
        </div>
      )}
    </div>
  );
}
