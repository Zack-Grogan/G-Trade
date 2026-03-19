(function () {
  function parseJsonScript(id) {
    const el = document.getElementById(id);
    if (!el) return null;
    try {
      return JSON.parse(el.textContent || "null");
    } catch (error) {
      console.error("Failed to parse JSON script", error);
      return null;
    }
  }

  function textContent(selector, value) {
    if (value === undefined || value === null) return;
    document.querySelectorAll(selector).forEach((el) => {
      el.textContent = String(value);
    });
  }

  const pacificFormatter = new Intl.DateTimeFormat("en-US", {
    timeZone: "America/Los_Angeles",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
    timeZoneName: "short",
  });

  function money(value) {
    const number = Number(value);
    if (!Number.isFinite(number)) return "-";
    return `$${number.toFixed(2)}`;
  }

  function number(value, digits = 2) {
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) return "-";
    return numeric.toFixed(digits);
  }

  function formatTimestamp(value) {
    if (!value) return "-";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return String(value);
    return pacificFormatter.format(date);
  }

  function zoneLabel(zone) {
    if (!zone) return "inactive";
    if (typeof zone === "string") return zone;
    if (typeof zone === "object") {
      if (zone.name) return String(zone.name);
      if (zone.state === "active") return "Outside";
      return "inactive";
    }
    return String(zone);
  }

  function connectStream(url, onMessage) {
    const source = new EventSource(url);
    source.addEventListener("message", (event) => {
      try {
        onMessage(JSON.parse(event.data));
      } catch (error) {
        console.error("Failed to parse SSE payload", error);
      }
    });
    source.onerror = (error) => {
      if (document.visibilityState === "hidden") return;
      if (source.readyState === EventSource.CLOSED) {
        console.warn("SSE stream closed", url, error);
      }
    };
    window.addEventListener("beforeunload", () => source.close(), { once: true });
    return source;
  }

  function initStateStream(url, selectors) {
    const update = (payload) => {
      if (!payload) return;
      textContent(selectors.status, payload.status);
      textContent(selectors.zone, zoneLabel(payload.zone));
      textContent(selectors.position, payload.position?.contracts ?? payload.position ?? 0);
      textContent(selectors.longScore, number(payload.alpha?.long_score));
      textContent(selectors.shortScore, number(payload.alpha?.short_score));
      textContent(selectors.flatBias, number(payload.alpha?.flat_bias));
      textContent(selectors.runId, payload.run_id || "-");
      textContent(selectors.lastEntry, payload.alpha?.last_entry_reason || "-");
      textContent(selectors.lastExit, payload.alpha?.last_exit_reason || "-");
    };

    const bootstrap = parseJsonScript("page-data");
    if (bootstrap && bootstrap.state) {
      update(bootstrap.state);
    }
    return connectStream(url, update);
  }

  function buildMarkerSeries(markers) {
    return (markers || []).map((marker) => ({
      time: marker.time,
      position: marker.position,
      color: marker.color,
      shape: marker.shape,
      text: marker.text,
    }));
  }

  function initChart(containerId, payload) {
    const container = document.getElementById(containerId);
    if (!container || !window.LightweightCharts) return null;

    const chart = window.LightweightCharts.createChart(container, {
      layout: {
        background: { color: "#0a0f14" },
        textColor: "#dbe4ee",
        fontFamily: "Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
      },
      grid: {
        vertLines: { color: "rgba(36, 49, 64, 0.65)" },
        horzLines: { color: "rgba(36, 49, 64, 0.65)" },
      },
      rightPriceScale: {
        borderColor: "rgba(36, 49, 64, 0.9)",
      },
      timeScale: {
        borderColor: "rgba(36, 49, 64, 0.9)",
        timeVisible: true,
        secondsVisible: false,
      },
      crosshair: {
        mode: window.LightweightCharts.CrosshairMode.Normal,
      },
      localization: {
        priceFormatter: (price) => price.toFixed(2),
      },
    });

    function addSeriesCompat(type, options) {
      if (typeof chart.addSeries === "function" && window.LightweightCharts[type]) {
        return chart.addSeries(window.LightweightCharts[type], options);
      }
      if (type === "CandlestickSeries" && typeof chart.addCandlestickSeries === "function") {
        return chart.addCandlestickSeries(options);
      }
      if (type === "LineSeries" && typeof chart.addLineSeries === "function") {
        return chart.addLineSeries(options);
      }
      throw new Error(`Unsupported Lightweight Charts series API for ${type}`);
    }

    const candleSeries = addSeriesCompat("CandlestickSeries", {
      upColor: "#4ade80",
      downColor: "#ef4444",
      borderUpColor: "#4ade80",
      borderDownColor: "#ef4444",
      wickUpColor: "#4ade80",
      wickDownColor: "#ef4444",
    });

    const priceSeries = addSeriesCompat("LineSeries", {
      color: "#5dd4ff",
      lineWidth: 2,
    });

    const vwapSeries = addSeriesCompat("LineSeries", {
      color: "#f59e0b",
      lineWidth: 1,
    });

    const upperSeries = addSeriesCompat("LineSeries", {
      color: "rgba(136, 227, 164, 0.85)",
      lineWidth: 1,
    });

    const lowerSeries = addSeriesCompat("LineSeries", {
      color: "rgba(251, 113, 133, 0.85)",
      lineWidth: 1,
    });

    const render = (data) => {
      if (!data) return;
      if (Array.isArray(data.candles) && data.candles.length) {
        candleSeries.setData(data.candles);
        chart.timeScale().fitContent();
      }
      if (Array.isArray(data.series?.price) && data.series.price.length) {
        priceSeries.setData(data.series.price);
      }
      if (Array.isArray(data.series?.vwap) && data.series.vwap.length) {
        vwapSeries.setData(data.series.vwap);
      }
      if (Array.isArray(data.series?.upper_band) && data.series.upper_band.length) {
        upperSeries.setData(data.series.upper_band);
      }
      if (Array.isArray(data.series?.lower_band) && data.series.lower_band.length) {
        lowerSeries.setData(data.series.lower_band);
      }
      if (typeof candleSeries.setMarkers === "function") {
        candleSeries.setMarkers(buildMarkerSeries(data.markers));
      } else if (typeof window.LightweightCharts.createSeriesMarkers === "function") {
        window.LightweightCharts.createSeriesMarkers(candleSeries, buildMarkerSeries(data.markers));
      }
    };

    render(payload);

    const streamUrl = "/stream/chart";
    connectStream(streamUrl, (next) => {
      render(next);
    });

    const resize = () => {
      chart.applyOptions({ width: container.clientWidth, height: Math.max(container.clientHeight, 520) });
    };
    window.addEventListener("resize", resize);
    if (typeof ResizeObserver !== "undefined") {
      new ResizeObserver(resize).observe(container);
    }
    resize();
    return chart;
  }

  function initLogsStream(url, listSelector) {
    const update = (payload) => {
      const list = document.querySelector(listSelector);
      if (!list || !payload) return;
      const items = [
        ...(payload.logs || []).map((row) => ({
          timestamp: row.logged_at,
          title: `${row.level || "INFO"} · ${row.display_source || row.logger_name || row.source || ""}`,
          detail: row.display_message || row.message || "",
        })),
      ];
      list.innerHTML = items
        .slice(0, 50)
        .map(
          (item) => `
            <div class="stack-item">
              <div class="stack-title">${formatTimestamp(item.timestamp)}</div>
              <div class="stack-subtle">${item.title}</div>
              <div>${item.detail}</div>
            </div>
          `,
        )
        .join("");
    };
    const bootstrap = parseJsonScript("page-data");
    if (bootstrap) {
      update(bootstrap);
    }
    return connectStream(url, update);
  }

  window.GTradeConsole = {
    initStateStream,
    initChart,
    initLogsStream,
    parseJsonScript,
    connectStream,
    money,
    number,
    formatTimestamp,
  };
})();
