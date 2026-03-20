(function () {
  // Inline SVG icon paths keyed by name — mirrors SVG_ICON_PATHS in flask_console.py
  const ICON_PATHS = {
    activity: '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>',
    "trending-up": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline><polyline points="17 6 23 6 23 12"></polyline></svg>',
    "arrow-up-right": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="7" y1="17" x2="17" y2="7"></line><polyline points="7 7 17 7 17 17"></polyline></svg>',
    "plus-circle": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="16"></line><line x1="8" y1="12" x2="16" y2="12"></line></svg>',
    lock: '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>',
    "minus-circle": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="8" y1="12" x2="16" y2="12"></line></svg>',
    "alert-triangle": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>',
    "x-circle": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>',
    "trending-down": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 18 13.5 8.5 8.5 13.5 1 6"></polyline><polyline points="17 18 23 18 23 12"></polyline></svg>',
    "shield-alert": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>',
    shield: '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>',
    briefcase: '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path></svg>',
  };

  // Registry mirror — notif_type → { icon, label }
  // NOTIF_REGISTRY must stay in sync with NOTIFICATION_TYPES keys in flask_console.py
  // NOTIF_REGISTRY must stay in sync with NOTIFICATION_TYPES keys in flask_console.py
  const NOTIF_REGISTRY = {
    runtime_heartbeat: { icon: "activity", label: "Heartbeat" },
    market_heartbeat: { icon: "trending-up", label: "Market" },
    broker_order: { icon: "arrow-up-right", label: "Order" },
    broker_position: { icon: "briefcase", label: "Position" },
    risk: { icon: "shield", label: "Risk" },
    failsafe: { icon: "alert-triangle", label: "Fail-Safe" },
    flatten: { icon: "x-circle", label: "Flatten" },
    blocked: { icon: "lock", label: "Blocked" },
    skipped: { icon: "minus-circle", label: "Skipped" },
    position_open: { icon: "plus-circle", label: "Position" },
    loss: { icon: "trending-down", label: "Loss" },
    daily_limit: { icon: "shield-alert", label: "Daily Limit" },
    consecutive_loss: { icon: "shield-alert", label: "Consecutive Loss" },
  };

  function getIconSvg(name) {
    return ICON_PATHS[name] || "";
  }

  function getNotifMeta(notifType) {
    return NOTIF_REGISTRY[notifType] || { icon: "", label: notifType || "" };
  }

  function fmtValue(value, fmt) {
    if (fmt === "bool") return value === true || value === "True" || value === "true" || value === "1" ? "Yes" : "No";
    if (fmt === "price") {
      const n = Number(value);
      return Number.isFinite(n) ? n.toFixed(2) : value;
    }
    if (fmt === "int") {
      const n = Number(value);
      return Number.isFinite(n) ? String(Math.floor(n)) : value;
    }
    return value;
  }

  function renderLogCard(row) {
    const notifType = row.notif_type || "";
    const meta = getNotifMeta(notifType);
    const iconSvg = getIconSvg(meta.icon);
    const label = meta.label || notifType || "";
    const summary = row.notif_summary || row.display_message || "";
    const fields = row.display_fields || [];

    let chipsHtml = "";
    if (fields.length > 0) {
      const chips = fields.map(function (f) {
        const colorCls = f.color ? "is-" + f.color : "";
        return (
          '<span class="chip ' + colorCls + '">' +
          '<span class="chip-label">' + (f.label || "") + '</span>' +
          '<span class="chip-sep">&nbsp;</span>' +
          '<span class="chip-val">' + (f.value || "") + '</span>' +
          "</span>"
        );
      });
      chipsHtml = '<div class="notif-fields">' + chips.join("") + "</div>";
    }

    var cardClass = notifType ? "notif notif-" + notifType : "notif";
    var iconHtml = iconSvg ? '<span class="notif-icon">' + iconSvg + "</span>" : "";

    return (
      '<div class="' + cardClass + '">' +
      iconHtml +
      '<div class="notif-body">' +
      '<div class="notif-label">' + label + '</div>' +
      '<div class="notif-summary">' + summary + '</div>' +
      chipsHtml +
      "</div>" +
      "</div>"
    );
  }

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
      textContent(selectors.decisions, payload.heartbeat?.decisions_last_min ?? "-");
      textContent(selectors.failSafe, payload.heartbeat?.fail_safe_lockout ?? "-");
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
    if (!container) {
      console.error("[Chart] Container not found:", containerId);
      return null;
    }
    if (!window.LightweightCharts) {
      console.error("[Chart] LightweightCharts not loaded");
      return null;
    }

    console.info("[Chart] Initializing with v" + (window.LightweightCharts.version || "unknown"));

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
      leftPriceScale: {
        visible: true,
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
      throw new Error(`[Chart] Unsupported series API for ${type}`);
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

    const alphaLongSeries = addSeriesCompat("LineSeries", {
      color: "rgba(74, 222, 128, 0.95)",
      lineWidth: 1,
      priceScaleId: "left",
      lastValueVisible: false,
      priceLineVisible: false,
    });

    const alphaShortSeries = addSeriesCompat("LineSeries", {
      color: "rgba(239, 68, 68, 0.95)",
      lineWidth: 1,
      priceScaleId: "left",
      lastValueVisible: false,
      priceLineVisible: false,
    });

    const alphaFlatSeries = addSeriesCompat("LineSeries", {
      color: "rgba(245, 158, 11, 0.95)",
      lineWidth: 1,
      priceScaleId: "left",
      lastValueVisible: false,
      priceLineVisible: false,
    });

    let isInitialized = false;
    let seriesMarkersApi = null;

    const collectMarkers = (data) => {
      const combined = [];
      if (Array.isArray(data?.markers)) {
        combined.push(...data.markers);
      }
      const markerSets = data?.marker_sets || {};
      ["trade", "decision", "execution"].forEach((key) => {
        if (Array.isArray(markerSets[key])) {
          combined.push(...markerSets[key]);
        }
      });
      const deduped = new Map();
      combined.forEach((marker) => {
        if (!marker || marker.time === undefined || marker.time === null) return;
        const dedupeKey = [
          marker.time,
          marker.shape || "",
          marker.position || "",
          marker.color || "",
          marker.text || "",
        ].join("|");
        if (!deduped.has(dedupeKey)) {
          deduped.set(dedupeKey, marker);
        }
      });
      return Array.from(deduped.values()).sort((a, b) => (a.time || 0) - (b.time || 0));
    };

    const applyMarkers = (data) => {
      const normalized = buildMarkerSeries(collectMarkers(data));
      if (typeof candleSeries.setMarkers === "function") {
        candleSeries.setMarkers(normalized);
        return;
      }
      if (typeof window.LightweightCharts.createSeriesMarkers === "function") {
        if (!seriesMarkersApi) {
          seriesMarkersApi = window.LightweightCharts.createSeriesMarkers(candleSeries, normalized);
          return;
        }
        if (typeof seriesMarkersApi.setMarkers === "function") {
          seriesMarkersApi.setMarkers(normalized);
          return;
        }
        seriesMarkersApi = window.LightweightCharts.createSeriesMarkers(candleSeries, normalized);
      }
    };

    const renderFull = (data) => {
      if (!data) return;
      const candles = Array.isArray(data.candles) ? data.candles : [];
      candleSeries.setData(candles);
      priceSeries.setData(Array.isArray(data.series?.price) ? data.series.price : []);
      vwapSeries.setData(Array.isArray(data.series?.vwap) ? data.series.vwap : []);
      upperSeries.setData(Array.isArray(data.series?.upper_band) ? data.series.upper_band : []);
      lowerSeries.setData(Array.isArray(data.series?.lower_band) ? data.series.lower_band : []);
      alphaLongSeries.setData(Array.isArray(data.series?.alpha_long) ? data.series.alpha_long : []);
      alphaShortSeries.setData(Array.isArray(data.series?.alpha_short) ? data.series.alpha_short : []);
      alphaFlatSeries.setData(Array.isArray(data.series?.alpha_flat) ? data.series.alpha_flat : []);
      applyMarkers(data);
      if (!isInitialized && candles.length) {
        chart.timeScale().fitContent();
      }
      isInitialized = true;
    };

    const renderIncremental = (data) => {
      if (!data || !isInitialized) return;
      if (Array.isArray(data.candles) && data.candles.length) {
        candleSeries.update(data.candles[data.candles.length - 1]);
      }
      if (Array.isArray(data.series?.price) && data.series.price.length) {
        priceSeries.update(data.series.price[data.series.price.length - 1]);
      }
      if (Array.isArray(data.series?.vwap) && data.series.vwap.length) {
        vwapSeries.update(data.series.vwap[data.series.vwap.length - 1]);
      }
      if (Array.isArray(data.series?.upper_band) && data.series.upper_band.length) {
        upperSeries.update(data.series.upper_band[data.series.upper_band.length - 1]);
      }
      if (Array.isArray(data.series?.lower_band) && data.series.lower_band.length) {
        lowerSeries.update(data.series.lower_band[data.series.lower_band.length - 1]);
      }
      if (Array.isArray(data.series?.alpha_long) && data.series.alpha_long.length) {
        alphaLongSeries.update(data.series.alpha_long[data.series.alpha_long.length - 1]);
      }
      if (Array.isArray(data.series?.alpha_short) && data.series.alpha_short.length) {
        alphaShortSeries.update(data.series.alpha_short[data.series.alpha_short.length - 1]);
      }
      if (Array.isArray(data.series?.alpha_flat) && data.series.alpha_flat.length) {
        alphaFlatSeries.update(data.series.alpha_flat[data.series.alpha_flat.length - 1]);
      }
      applyMarkers(data);
    };

    renderFull(payload);

    const lookbackHours = payload?.chart_window?.lookback_hours;
    const streamUrl = Number.isFinite(Number(lookbackHours))
      ? `/stream/chart?lookback_hours=${encodeURIComponent(String(lookbackHours))}`
      : "/stream/chart";
    connectStream(streamUrl, (next) => {
      renderFull(next);
    });

    let resizeTimeout;
    const resize = () => {
      clearTimeout(resizeTimeout);
      resizeTimeout = setTimeout(() => {
        chart.applyOptions({ width: container.clientWidth, height: Math.max(container.clientHeight, 520) });
      }, 100);
    };
    if (typeof ResizeObserver !== "undefined") {
      new ResizeObserver(resize).observe(container);
    } else {
      window.addEventListener("resize", resize);
    }
    resize();
    return chart;
  }

  function initLogsStream(url, listSelector) {
    const update = (payload) => {
      const list = document.querySelector(listSelector);
      if (!list || !payload) return;
      const items = (payload.logs || []).slice(0, 50).map((row) => {
        // Use the new card renderer if we have a notif_type
        if (row.notif_type) {
          return (
            '<div class="stack-item">' +
            '<div class="stack-title">' + formatTimestamp(row.logged_at) + "</div>" +
            '<div class="stack-subtle">' + (row.level || "INFO") + " · " + (row.display_source || row.logger_name || row.source || "") + "</div>" +
            renderLogCard(row) +
            "</div>"
          );
        }
        // Legacy fallback — handle both list (new) and dict (old) display_fields
        const fields = row.display_fields;
        let fieldsHtml = "";
        if (fields) {
          if (Array.isArray(fields)) {
            // New list format: [{label, value, color}, ...]
            fieldsHtml =
              '<dl class="display-fields">' +
              fields
                .map((f) => `<dt>${f.label || ""}</dt><dd>${f.value || ""}</dd>`)
                .join("") +
              "</dl>";
          } else {
            // Old dict format: {key: value, ...}
            fieldsHtml =
              '<dl class="display-fields">' +
              Object.entries(fields)
                .map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`)
                .join("") +
              "</dl>";
          }
        }
        return (
          '<div class="stack-item">' +
          '<div class="stack-title">' + formatTimestamp(row.logged_at) + "</div>" +
          '<div class="stack-subtle">' + (row.level || "INFO") + " · " + (row.display_source || row.logger_name || row.source || "") + "</div>" +
          "<div>" + (row.display_message || row.message || "") + "</div>" +
          fieldsHtml +
          "</div>"
        );
      });
      list.innerHTML = items.join("");
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
    renderLogCard,
    getNotifMeta,
    getIconSvg,
  };
})();
