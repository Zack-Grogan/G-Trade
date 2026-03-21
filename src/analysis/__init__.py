"""Local analysis helpers for regime packets and trade review."""

from .fill_quality import (
    FillAnalysis,
    FillQualityAnalyzer,
    FillQualityReport,
    FillScorecard,
    build_fill_quality_report,
)
from .matrix_correlation import (
    CorrelationReport,
    ScoreOutcomePair,
    ThresholdResult,
    build_matrix_correlation_report,
    build_regime_breakdown,
    build_score_distribution,
    build_zone_breakdown,
    compute_threshold_analysis,
    extract_score_outcome_pairs,
)
from .regime_packet import (
    build_launch_readiness,
    build_regime_packet,
    build_trade_review,
    render_regime_packet_markdown,
)
from .stress_periods import (
    StressPeriod,
    StressReport,
    build_stress_periods_dict,
    build_stress_report,
    detect_stress_periods,
    detect_stress_periods_from_observability,
    detect_stress_periods_from_topstep,
)
from .trade_analyzer import (
    TradeAnalysisReport,
    TradeStats,
    ZoneTradeStats,
    ThresholdSensitivity,
    build_trade_analysis_report,
    compute_trade_stats,
    compute_zone_stats,
    compute_threshold_sensitivity,
    compute_hold_time_distribution,
    compute_hourly_breakdown,
    query_completed_trades,
    render_trade_analysis_summary,
)
from .threshold_optimizer import (
    HoldTimeRecommendation,
    OptimizationReport,
    ThresholdRecommendation,
    TrailingStopRecommendation,
    build_optimization_report,
    optimize_entry_threshold,
    optimize_exit_decay_score,
    optimize_max_hold_minutes,
    optimize_trailing_stop,
    recommend_config_updates,
    render_optimization_yaml_patch,
)

__all__ = [
    # Fill quality
    "FillAnalysis",
    "FillQualityAnalyzer",
    "FillQualityReport",
    "FillScorecard",
    "build_fill_quality_report",
    # Matrix correlation
    "CorrelationReport",
    "ScoreOutcomePair",
    "ThresholdResult",
    "build_matrix_correlation_report",
    "build_regime_breakdown",
    "build_score_distribution",
    "build_zone_breakdown",
    "compute_threshold_analysis",
    "extract_score_outcome_pairs",
    # Regime packet
    "build_launch_readiness",
    "build_regime_packet",
    "build_trade_review",
    "render_regime_packet_markdown",
    # Stress periods
    "StressPeriod",
    "StressReport",
    "build_stress_periods_dict",
    "build_stress_report",
    "detect_stress_periods",
    "detect_stress_periods_from_observability",
    "detect_stress_periods_from_topstep",
    # Trade analyzer (analyzes ACTUAL TRADES from replay)
    "TradeAnalysisReport",
    "TradeStats",
    "ZoneTradeStats",
    "ThresholdSensitivity",
    "build_trade_analysis_report",
    "compute_trade_stats",
    "compute_zone_stats",
    "compute_threshold_sensitivity",
    "compute_hold_time_distribution",
    "compute_hourly_breakdown",
    "query_completed_trades",
    "render_trade_analysis_summary",
    # Threshold optimizer
    "HoldTimeRecommendation",
    "OptimizationReport",
    "ThresholdRecommendation",
    "TrailingStopRecommendation",
    "build_optimization_report",
    "optimize_entry_threshold",
    "optimize_exit_decay_score",
    "optimize_max_hold_minutes",
    "optimize_trailing_stop",
    "recommend_config_updates",
    "render_optimization_yaml_patch",
]
