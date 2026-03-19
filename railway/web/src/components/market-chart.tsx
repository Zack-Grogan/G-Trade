type Tone = "neutral" | "success" | "warning" | "accent";

export type ChartPoint = {
  timestamp: string;
  value: number | null;
};

export type ChartReferenceLine = {
  label: string;
  value: number | null;
  tone?: Tone;
};

export type ChartMarker = {
  label: string;
  timestamp: string;
  value?: number | null;
  tone?: Tone;
};

function toneClasses(tone: Tone = "neutral") {
  return {
    neutral: "stroke-zinc-500 fill-zinc-500 text-zinc-200",
    success: "stroke-emerald-400 fill-emerald-400 text-emerald-200",
    warning: "stroke-amber-400 fill-amber-400 text-amber-200",
    accent: "stroke-cyan-400 fill-cyan-400 text-cyan-200",
  }[tone];
}

function formatShortTime(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("en-US", {
    hour: "numeric",
    minute: "2-digit",
  }).format(date);
}

function nearestIndex(timestamps: string[], target: string) {
  if (!timestamps.length) {
    return 0;
  }

  const targetTime = new Date(target).getTime();
  if (Number.isNaN(targetTime)) {
    return 0;
  }

  let bestIndex = 0;
  let bestDistance = Number.POSITIVE_INFINITY;
  timestamps.forEach((timestamp, index) => {
    const currentTime = new Date(timestamp).getTime();
    if (Number.isNaN(currentTime)) {
      return;
    }

    const distance = Math.abs(currentTime - targetTime);
    if (distance < bestDistance) {
      bestDistance = distance;
      bestIndex = index;
    }
  });
  return bestIndex;
}

export function MarketChart({
  points,
  markers = [],
  referenceLines = [],
  height = 280,
  title,
  subtitle,
}: {
  points: ChartPoint[];
  markers?: ChartMarker[];
  referenceLines?: ChartReferenceLine[];
  height?: number;
  title?: string;
  subtitle?: string;
}) {
  const values = points.map((point) => point.value).filter((value): value is number => typeof value === "number" && Number.isFinite(value));
  const referenceValues = referenceLines.map((line) => line.value).filter((value): value is number => typeof value === "number" && Number.isFinite(value));
  const markerValues = markers.map((marker) => marker.value).filter((value): value is number => typeof value === "number" && Number.isFinite(value));
  const allValues = [...values, ...referenceValues, ...markerValues];

  if (!points.length || !allValues.length) {
    return (
      <div className="rounded-2xl border border-dashed border-zinc-800 bg-zinc-950/70 p-5 text-sm text-zinc-400">
        {title ? <p className="text-sm font-medium text-zinc-100">{title}</p> : null}
        <p className={title ? "mt-2" : ""}>{subtitle ?? "No chart data is available for this view yet."}</p>
      </div>
    );
  }

  const minValue = Math.min(...allValues);
  const maxValue = Math.max(...allValues);
  const padding = Math.max((maxValue - minValue) * 0.12, Math.abs(maxValue) * 0.03, 1);
  const lower = minValue - padding;
  const upper = maxValue + padding;
  const width = 960;
  const plotWidth = width - 96;
  const plotHeight = height - 72;
  const pointTimestamps = points.map((point) => point.timestamp);
  const plotLeft = 56;
  const plotTop = 20;

  const xForIndex = (index: number) => {
    if (points.length <= 1) {
      return plotLeft + plotWidth / 2;
    }
    return plotLeft + (index / (points.length - 1)) * plotWidth;
  };

  const yForValue = (value: number) => {
    const normalized = (value - lower) / (upper - lower);
    return plotTop + plotHeight - normalized * plotHeight;
  };

  const pointsPath = points
    .map((point, index) => {
      if (point.value === null || point.value === undefined || !Number.isFinite(point.value)) {
        return null;
      }
      const x = xForIndex(index);
      const y = yForValue(point.value);
      return `${index === 0 ? "M" : "L"} ${x} ${y}`;
    })
    .filter(Boolean)
    .join(" ");

  return (
    <div className="rounded-3xl border border-zinc-800 bg-zinc-950/80 p-5">
      {(title || subtitle) && (
        <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
          <div>
            {title ? <p className="text-[11px] uppercase tracking-[0.22em] text-cyan-300">{title}</p> : null}
            {subtitle ? <p className="mt-1 text-sm text-zinc-400">{subtitle}</p> : null}
          </div>
          <div className="flex flex-wrap gap-2 text-[11px] text-zinc-500">
            <span className="rounded-full border border-zinc-800 bg-zinc-900 px-2.5 py-1">min {lower.toFixed(2)}</span>
            <span className="rounded-full border border-zinc-800 bg-zinc-900 px-2.5 py-1">max {upper.toFixed(2)}</span>
          </div>
        </div>
      )}

      <div className="overflow-hidden rounded-2xl border border-zinc-800 bg-black/30">
        <svg viewBox={`0 0 ${width} ${height}`} className="h-auto w-full" role="img" aria-label={title ?? "Price chart"}>
          <defs>
            <linearGradient id="price-gradient" x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" stopColor="rgb(103 232 249)" stopOpacity="0.85" />
              <stop offset="100%" stopColor="rgb(103 232 249)" stopOpacity="0.1" />
            </linearGradient>
          </defs>

          <line x1={plotLeft} x2={width - 24} y1={plotTop + plotHeight} y2={plotTop + plotHeight} className="stroke-zinc-800" />

          {referenceLines.map((line) => {
            if (line.value === null || line.value === undefined || !Number.isFinite(line.value)) {
              return null;
            }
            const y = yForValue(line.value);
            const toneClass = toneClasses(line.tone ?? "neutral");
            return (
              <g key={`${line.label}-${line.value}`}>
                <line x1={plotLeft} x2={width - 24} y1={y} y2={y} className={`${toneClass} opacity-70`} strokeDasharray="6 6" strokeWidth="1.5" />
                <text x={width - 28} y={Math.max(y - 4, 12)} textAnchor="end" className={`fill-current text-[10px] uppercase tracking-[0.18em] ${toneClass}`}>
                  {line.label} {line.value.toFixed(2)}
                </text>
              </g>
            );
          })}

          {pointsPath ? <path d={pointsPath} fill="none" stroke="url(#price-gradient)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" /> : null}

          {points.map((point, index) => {
            if (point.value === null || point.value === undefined || !Number.isFinite(point.value)) {
              return null;
            }
            const x = xForIndex(index);
            const y = yForValue(point.value);
            return <circle key={`${point.timestamp}-${index}`} cx={x} cy={y} r="2.5" className="fill-cyan-300" />;
          })}

          {markers.map((marker) => {
            if (marker.value === null || marker.value === undefined || !Number.isFinite(marker.value)) {
              return null;
            }
            const x = xForIndex(nearestIndex(pointTimestamps, marker.timestamp));
            const y = yForValue(marker.value);
            const toneClass = toneClasses(marker.tone ?? "accent");
            return (
              <g key={`${marker.label}-${marker.timestamp}`}>
                <line x1={x} x2={x} y1={plotTop} y2={plotTop + plotHeight} className={`${toneClass} opacity-60`} strokeDasharray="4 4" strokeWidth="1.25" />
                <circle cx={x} cy={y} r="4" className={`stroke-zinc-950 ${toneClass} stroke-2`} />
                <rect x={Math.max(x - 42, 16)} y={Math.max(y - 34, 8)} width="84" height="20" rx="10" className="fill-zinc-950/90 stroke-zinc-800" />
                <text x={x} y={Math.max(y - 20, 22)} textAnchor="middle" className={`fill-current text-[10px] font-medium uppercase tracking-[0.18em] ${toneClass}`}>
                  {marker.label}
                </text>
              </g>
            );
          })}

          <text x={plotLeft} y={height - 16} className="fill-zinc-500 text-[10px] uppercase tracking-[0.18em]">
            {formatShortTime(points[0].timestamp)}
          </text>
          <text x={width - 24} y={height - 16} textAnchor="end" className="fill-zinc-500 text-[10px] uppercase tracking-[0.18em]">
            {formatShortTime(points[points.length - 1].timestamp)}
          </text>
        </svg>
      </div>
    </div>
  );
}
