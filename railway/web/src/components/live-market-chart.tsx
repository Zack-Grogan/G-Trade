"use client";

import { useEffect, useMemo, useRef } from "react";
import {
  ColorType,
  CrosshairMode,
  LineSeries,
  LineStyle,
  createChart,
  createSeriesMarkers,
  type IChartApi,
  type ISeriesApi,
  type IPriceLine,
  type SeriesMarker,
  type Time,
  type UTCTimestamp,
} from "lightweight-charts";

import type { ChartMarker, ChartPoint, ChartReferenceLine } from "@/components/market-chart";

type Tone = "neutral" | "success" | "warning" | "accent";

function toUtcTimestamp(value: string): UTCTimestamp | null {
  const parsed = new Date(value).getTime();
  if (Number.isNaN(parsed)) {
    return null;
  }

  return Math.floor(parsed / 1000) as UTCTimestamp;
}

function toneStyles(tone: Tone = "neutral") {
  return {
    neutral: { line: "rgba(113, 113, 122, 0.9)", marker: "#a1a1aa" },
    success: { line: "rgba(52, 211, 153, 0.9)", marker: "#86efac" },
    warning: { line: "rgba(251, 191, 36, 0.9)", marker: "#fcd34d" },
    accent: { line: "rgba(34, 211, 238, 0.95)", marker: "#67e8f9" },
  }[tone];
}

function formatDateLabel(value: string | null | undefined) {
  if (!value) {
    return "—";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("en-US", {
    hour: "numeric",
    minute: "2-digit",
    month: "short",
    day: "numeric",
  }).format(date);
}

function buildMarkers(markers: ChartMarker[], lastValue: number | null): SeriesMarker<Time>[] {
  return markers.flatMap((marker) => {
    if (marker.value === null || marker.value === undefined || !Number.isFinite(marker.value)) {
      return [];
    }
    const time = toUtcTimestamp(marker.timestamp);
    if (time === null) {
      return [];
    }
    const tone = toneStyles(marker.tone ?? "neutral");
    const isAbove = lastValue === null ? (marker.tone ?? "neutral") === "warning" : marker.value >= lastValue;
    return [
      {
        time,
        price: marker.value,
        position: "atPriceMiddle" as const,
        shape: isAbove ? ("arrowDown" as const) : ("arrowUp" as const),
        color: tone.marker,
        text: marker.label,
        size: 1,
      },
    ];
  });
}

export function LiveMarketChart({
  points,
  markers = [],
  referenceLines = [],
  height = 520,
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
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Line"> | null>(null);
  const priceLinesRef = useRef<IPriceLine[]>([]);

  const chartPoints = useMemo(
    () =>
      points
        .map((point) => {
          const time = toUtcTimestamp(point.timestamp);
          if (time === null || point.value === null || point.value === undefined || !Number.isFinite(point.value)) {
            return null;
          }
          return { time, value: point.value };
        })
        .filter((point): point is { time: UTCTimestamp; value: number } => Boolean(point)),
    [points],
  );

  const allValues = useMemo(
    () =>
      [
        ...chartPoints.map((point) => point.value),
        ...referenceLines.map((line) => line.value).filter((value): value is number => typeof value === "number" && Number.isFinite(value)),
        ...markers.map((marker) => marker.value).filter((value): value is number => typeof value === "number" && Number.isFinite(value)),
      ].filter((value): value is number => typeof value === "number" && Number.isFinite(value)),
    [chartPoints, markers, referenceLines],
  );

  useEffect(() => {
    const container = containerRef.current;
    if (!container) {
      return;
    }

    if (chartRef.current) {
      chartRef.current.remove();
      chartRef.current = null;
      seriesRef.current = null;
      priceLinesRef.current = [];
    }

    const chart = createChart(container, {
      autoSize: true,
      layout: {
        background: { type: ColorType.Solid, color: "#09090b" },
        textColor: "#d4d4d8",
        fontSize: 12,
      },
      grid: {
        vertLines: { color: "rgba(39, 39, 42, 0.55)" },
        horzLines: { color: "rgba(39, 39, 42, 0.55)" },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: {
          color: "rgba(113, 113, 122, 0.75)",
          width: 1,
          style: LineStyle.Dashed,
          labelBackgroundColor: "#18181b",
        },
        horzLine: {
          color: "rgba(113, 113, 122, 0.75)",
          width: 1,
          style: LineStyle.Dashed,
          labelBackgroundColor: "#18181b",
        },
      },
      rightPriceScale: {
        borderColor: "rgba(39, 39, 42, 0.9)",
      },
      timeScale: {
        borderColor: "rgba(39, 39, 42, 0.9)",
        timeVisible: true,
        secondsVisible: false,
      },
      handleScroll: {
        mouseWheel: true,
        pressedMouseMove: true,
      },
      handleScale: {
        axisPressedMouseMove: true,
        pinch: true,
        mouseWheel: true,
      },
    });

    const series = chart.addSeries(LineSeries, {
      color: "#67e8f9",
      lineWidth: 2,
      priceLineVisible: false,
      lastValueVisible: true,
      crosshairMarkerVisible: true,
      priceFormat: {
        type: "price",
        precision: 2,
        minMove: 0.01,
      },
      title: title ?? "Series",
    });
    seriesRef.current = series;
    series.setData(chartPoints);

    priceLinesRef.current = referenceLines.flatMap((line) => {
      if (line.value === null || line.value === undefined || !Number.isFinite(line.value)) {
        return [];
      }
      const tone = toneStyles(line.tone ?? "neutral");
      return [
        series.createPriceLine({
          price: line.value,
          color: tone.line,
          lineWidth: 1,
          lineStyle: line.tone === "neutral" ? LineStyle.Dashed : LineStyle.Solid,
          axisLabelVisible: true,
          title: line.label,
        }),
      ];
    });

    const markerData = buildMarkers(markers, chartPoints.at(-1)?.value ?? null);
    if (markerData.length) {
      createSeriesMarkers(series, markerData);
    }

    chart.timeScale().fitContent();
    chartRef.current = chart;

    const resizeObserver = new ResizeObserver(() => {
      chart.timeScale().fitContent();
    });
    resizeObserver.observe(container);

    return () => {
      resizeObserver.disconnect();
      priceLinesRef.current = [];
      seriesRef.current = null;
      chart.remove();
      chartRef.current = null;
    };
  }, [chartPoints, markers, referenceLines, title]);

  if (!chartPoints.length && !allValues.length) {
    return (
      <div className="rounded-xl border border-dashed border-zinc-800/80 bg-zinc-950 p-5 text-sm text-zinc-400">
        <p className="text-sm font-medium text-zinc-100">{title ?? "Chart"}</p>
        <p className="mt-2 break-words">{subtitle ?? "No chart data is available for this view yet."}</p>
      </div>
    );
  }

  const minValue = allValues.length ? Math.min(...allValues) : null;
  const maxValue = allValues.length ? Math.max(...allValues) : null;
  const lastValue = chartPoints.at(-1)?.value ?? null;

  return (
    <section className="overflow-hidden rounded-xl border border-zinc-800/80 bg-zinc-950">
      {(title || subtitle) && (
        <div className="flex flex-wrap items-start justify-between gap-3 border-b border-zinc-800/80 px-4 py-3">
          <div className="min-w-0">
            {title ? <p className="text-[11px] uppercase tracking-[0.22em] text-cyan-300">{title}</p> : null}
            {subtitle ? <p className="mt-1 break-words text-sm text-zinc-400">{subtitle}</p> : null}
          </div>
          <div className="flex flex-wrap gap-2 text-[11px] uppercase tracking-[0.18em] text-zinc-500">
            {lastValue !== null ? <span className="rounded-md border border-zinc-800 bg-zinc-950 px-2 py-1 tabular-nums">last {lastValue.toFixed(2)}</span> : null}
            {minValue !== null ? <span className="rounded-md border border-zinc-800 bg-zinc-950 px-2 py-1 tabular-nums">min {minValue.toFixed(2)}</span> : null}
            {maxValue !== null ? <span className="rounded-md border border-zinc-800 bg-zinc-950 px-2 py-1 tabular-nums">max {maxValue.toFixed(2)}</span> : null}
          </div>
        </div>
      )}

      <div className="border-b border-zinc-800/80 bg-zinc-950" style={{ height }}>
        <div ref={containerRef} className="h-full w-full" />
      </div>

      <div className="flex flex-wrap items-center justify-between gap-2 px-4 py-3 text-xs text-zinc-500">
        <span>Range {formatDateLabel(points[0]?.timestamp)} → {formatDateLabel(points.at(-1)?.timestamp)}</span>
        <span>{markers.length ? `${markers.length} markers` : "No markers"}</span>
      </div>
    </section>
  );
}
