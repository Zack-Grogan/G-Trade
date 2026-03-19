import type { ReactNode } from "react";

type Tone = "neutral" | "success" | "warning" | "accent" | "danger";

function formatValue(value: number) {
  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 2,
    minimumFractionDigits: 0,
  }).format(value);
}

export function formatDate(value: string | null | undefined) {
  if (!value) {
    return "—";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

export function formatCurrency(value: number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  }).format(value);
}

export function StatCard({
  label,
  value,
  note,
}: {
  label: string;
  value: string;
  note?: string;
}) {
  return (
    <article className="overflow-hidden rounded-xl border border-zinc-800/80 bg-zinc-950 p-4">
      <p className="text-[11px] uppercase tracking-[0.22em] text-zinc-500">{label}</p>
      <p className="mt-3 truncate text-2xl font-semibold tracking-tight text-zinc-50 tabular-nums">{value}</p>
      {note ? <p className="mt-2 break-words text-sm leading-6 text-zinc-400">{note}</p> : null}
    </article>
  );
}

export function KpiCard({
  label,
  value,
  detail,
  tone = "neutral",
}: {
  label: string;
  value: string;
  detail?: string;
  tone?: Tone;
}) {
  const toneClasses = {
    neutral: "border-zinc-800 bg-zinc-950",
    success: "border-emerald-500/20 bg-emerald-500/10",
    warning: "border-amber-500/20 bg-amber-500/10",
    accent: "border-cyan-500/20 bg-cyan-500/10",
    danger: "border-rose-500/20 bg-rose-500/10",
  }[tone];

  return (
    <article className={`overflow-hidden rounded-xl border p-4 ${toneClasses}`}>
      <p className="text-[11px] uppercase tracking-[0.22em] text-zinc-500">{label}</p>
      <p className="mt-3 truncate text-2xl font-semibold tracking-tight text-zinc-50 tabular-nums">{value}</p>
      {detail ? <p className="mt-2 break-words text-sm leading-6 text-zinc-400">{detail}</p> : null}
    </article>
  );
}

export function StatusPill({
  label,
  value,
  tone = "neutral",
}: {
  label: string;
  value: string;
  tone?: Tone;
}) {
  const toneClasses = {
    neutral: "border-zinc-800 bg-zinc-950 text-zinc-300",
    success: "border-emerald-500/20 bg-emerald-500/10 text-emerald-200",
    warning: "border-amber-500/20 bg-amber-500/10 text-amber-200",
    accent: "border-cyan-500/20 bg-cyan-500/10 text-cyan-200",
    danger: "border-rose-500/20 bg-rose-500/10 text-rose-200",
  }[tone];

  return (
    <span className={`inline-flex items-center gap-2 rounded-md border px-3 py-1.5 text-[11px] font-medium ${toneClasses}`}>
      <span className="uppercase tracking-[0.22em] text-zinc-500">{label}</span>
      <span className="truncate tabular-nums">{value}</span>
    </span>
  );
}

export function Panel({
  eyebrow,
  title,
  description,
  children,
  action,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  children: ReactNode;
  action?: ReactNode;
}) {
  return (
    <section className="rounded-xl border border-zinc-800/80 bg-zinc-950 p-5">
      <div className="flex min-w-0 items-start justify-between gap-4">
        <div>
          {eyebrow ? <p className="text-[11px] uppercase tracking-[0.22em] text-cyan-300">{eyebrow}</p> : null}
          <h2 className="mt-2 text-xl font-semibold tracking-tight text-zinc-50">{title}</h2>
          {description ? <p className="mt-2 max-w-3xl break-words text-sm leading-6 text-zinc-400">{description}</p> : null}
        </div>
        {action ? <div className="shrink-0">{action}</div> : null}
      </div>
      <div className="mt-5">{children}</div>
    </section>
  );
}

export function Badge({
  children,
  tone = "neutral",
}: {
  children: ReactNode;
  tone?: Tone;
}) {
  const toneClasses = {
    neutral: "border-zinc-800 bg-zinc-950 text-zinc-300",
    success: "border-emerald-500/20 bg-emerald-500/10 text-emerald-200",
    warning: "border-amber-500/20 bg-amber-500/10 text-amber-200",
    accent: "border-cyan-500/20 bg-cyan-500/10 text-cyan-200",
    danger: "border-rose-500/20 bg-rose-500/10 text-rose-200",
  }[tone];

  return <span className={`inline-flex items-center rounded-md border px-2.5 py-1 text-[11px] font-medium ${toneClasses}`}>{children}</span>;
}

export function MiniBarChart({
  values,
  labels,
}: {
  values: number[];
  labels: string[];
}) {
  const max = Math.max(...values.map((value) => Math.abs(value)), 1);

  return (
    <div className="space-y-3">
      <div className="flex h-28 items-end gap-2">
        {values.map((value, index) => {
          const height = `${Math.max((Math.abs(value) / max) * 100, 8)}%`;
          const isPositive = value >= 0;
          return (
            <div key={`${labels[index]}-${index}`} className="flex-1">
              <div className="relative flex h-full items-end rounded-lg border border-zinc-800 bg-zinc-900/70 p-1">
                <div
                  className={`w-full rounded-md ${isPositive ? "bg-emerald-400/80" : "bg-rose-400/80"}`}
                  style={{ height }}
                />
              </div>
            </div>
          );
        })}
      </div>
      <div className="grid grid-cols-2 gap-2 text-[11px] text-zinc-500 sm:grid-cols-4 md:grid-cols-8">
        {labels.map((label) => (
          <span key={label} className="truncate">
            {label}
          </span>
        ))}
      </div>
    </div>
  );
}

export function DataTable({
  columns,
  children,
}: {
  columns: string[];
  children: ReactNode;
}) {
  return (
    <div className="overflow-hidden rounded-xl border border-zinc-800/80 bg-zinc-950">
      <div className="grid grid-cols-2 gap-3 border-b border-zinc-800/80 px-4 py-3 text-[11px] uppercase tracking-[0.22em] text-zinc-500 sm:grid-cols-4">
        {columns.map((column) => (
          <span key={column}>{column}</span>
        ))}
      </div>
      <div className="divide-y divide-zinc-800/80">{children}</div>
    </div>
  );
}

export function DataRow({
  cells,
}: {
  cells: ReactNode[];
}) {
  return (
    <div className="grid grid-cols-2 gap-3 px-4 py-3 text-sm text-zinc-300 sm:grid-cols-4">
      {cells.map((cell, index) => (
        <div key={index} className="min-w-0 overflow-hidden">
          {cell}
        </div>
      ))}
    </div>
  );
}

export function formatShort(value: number) {
  return formatValue(value);
}

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <div className="rounded-xl border border-dashed border-zinc-800/80 bg-zinc-950 p-5">
      <p className="text-sm font-medium text-zinc-100">{title}</p>
      <p className="mt-2 max-w-2xl break-words text-sm leading-6 text-zinc-400">{description}</p>
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  );
}
