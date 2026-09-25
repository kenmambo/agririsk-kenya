"""Formatting utilities, risk badging, and standardized disclaimers for AgriRisk Kenya."""

from typing import Optional, Dict, Any

# Standard Risk Band Definitions and Color Mappings
RISK_THRESHOLDS = {
    "Low": (0.0, 0.25),
    "Moderate": (0.25, 0.50),
    "Elevated": (0.50, 0.75),
    "High": (0.75, 1.0)
}

RISK_COLORS = {
    "Low": "#2ca02c",        # Forest Green
    "Moderate": "#e6a817",   # Amber
    "Elevated": "#e65100",   # Deep Orange
    "High": "#d32f2f"        # Crimson Red
}

RISK_BADGE_STYLES = {
    "Low": {"bg": "#d4edda", "text": "#155724", "border": "#c3e6cb"},
    "Moderate": {"bg": "#fff3cd", "text": "#856404", "border": "#ffeeba"},
    "Elevated": {"bg": "#ffe8cc", "text": "#b78103", "border": "#ffd8a8"},
    "High": {"bg": "#f8d7da", "text": "#721c24", "border": "#f5c6cb"}
}

RESEARCH_DISCLAIMER_TEXT = (
    "RESEARCH PROTOTYPE DISCLAIMER: AgriRisk Kenya is a data-driven decision-support "
    "and early-warning research prototype. Model-generated risk probabilities reflect "
    "statistical associations across historical climate, vegetation, and market indicators. "
    "They do NOT constitute official humanitarian warnings, emergency declarations, or "
    "official IPC acute food insecurity classifications. Official food security classifications "
    "are determined by the Kenya Food Security Steering Group (KFSSG) and the IPC Global Support Unit."
)


def assign_risk_band(probability: float) -> str:
    """Assign categorical risk band based on predicted probability.

    Args:
        probability: Float value in range [0.0, 1.0].

    Returns:
        Risk band string: 'Low', 'Moderate', 'Elevated', or 'High'.
    """
    if probability < 0.25:
        return "Low"
    elif probability < 0.50:
        return "Moderate"
    elif probability < 0.75:
        return "Elevated"
    else:
        return "High"


def get_risk_color(risk_band: str) -> str:
    """Return HEX color code for a given risk band."""
    return RISK_COLORS.get(risk_band, "#6c757d")


def render_risk_badge(risk_band: str) -> str:
    """Render an HTML badge pill for the specified risk band."""
    style = RISK_BADGE_STYLES.get(risk_band, {"bg": "#e2e3e5", "text": "#383d41", "border": "#d6d8db"})
    return (
        f'<span style="background-color: {style["bg"]}; color: {style["text"]}; '
        f'border: 1px solid {style["border"]}; padding: 3px 10px; border-radius: 12px; '
        f'font-weight: 600; font-size: 0.85rem; display: inline-block;">'
        f'{risk_band} Risk'
        f'</span>'
    )


def render_disclaimer_banner() -> str:
    """Render a prominent standardized disclaimer banner in HTML format."""
    return (
        '<div style="background-color: #fff8e1; border-left: 5px solid #ffa000; '
        'padding: 12px 18px; border-radius: 4px; margin-bottom: 20px; font-size: 0.9rem; '
        'color: #5d4037; line-height: 1.45;">'
        '<strong>RESEARCH PROTOTYPE - NOT AN OPERATIONAL WARNING:</strong><br>'
        'This dashboard is an experimental academic prototype for multi-indicator risk analysis. '
        'Model risk probabilities are statistical estimations and do not replace official IPC '
        'classifications issued by the Kenya Food Security Steering Group (KFSSG).'
        '</div>'
    )


def format_anomaly(val: Optional[float], unit: str = "%") -> str:
    """Format an anomaly number with leading sign and specified unit."""
    if val is None or pd_is_nan(val):
        return "N/A"
    sign = "+" if val > 0 else ""
    return f"{sign}{val:.1f}{unit}"


def format_currency(val: Optional[float], prefix: str = "KES ") -> str:
    """Format currency values cleanly."""
    if val is None or pd_is_nan(val):
        return "N/A"
    return f"{prefix}{val:,.2f}"


def format_zscore(val: Optional[float]) -> str:
    """Format statistical z-score."""
    if val is None or pd_is_nan(val):
        return "N/A"
    sign = "+" if val > 0 else ""
    return f"{sign}{val:.2f} \u03c3"


def pd_is_nan(val: Any) -> bool:
    """Check if value is NaN or None without importing heavy pandas overhead."""
    import math
    try:
        return math.isnan(float(val))
    except (ValueError, TypeError):
        return False


def generate_non_causal_interpretation(
    county_name: str,
    period: str,
    risk_band: str,
    risk_prob: float,
    indicators: Dict[str, Any]
) -> str:
    """Generate a structured, non-causal contextual interpretation for a county.

    Explicitly emphasizes that identified patterns are statistical risk correlates,
    not causal attributions.

    Args:
        county_name: Canonical county name.
        period: Month period string (e.g. '2024-12').
        risk_band: Categorical risk band ('Low', 'Moderate', 'Elevated', 'High').
        risk_prob: Model risk probability (0.0 to 1.0).
        indicators: Dictionary of key features for this county-month.

    Returns:
        Markdown-formatted non-causal interpretation.
    """
    rain_3m = indicators.get("rainfall_anomaly_3m")
    ndvi_3m = indicators.get("ndvi_anomaly_3m")
    price_z = indicators.get("maize_price_zscore")
    dry_streak = indicators.get("consecutive_dry_months", 0)
    prev_ipc = indicators.get("previous_ipc_phase", "Unknown")

    contributing_factors = []

    if rain_3m is not None and not pd_is_nan(rain_3m):
        if rain_3m < -20:
            contributing_factors.append(f"Substantial 3-month rainfall deficit ({format_anomaly(rain_3m)})")
        elif rain_3m > 20:
            contributing_factors.append(f"Above-average 3-month rainfall ({format_anomaly(rain_3m)})")

    if dry_streak is not None and not pd_is_nan(dry_streak) and dry_streak >= 2:
        contributing_factors.append(f"Extended dry spell streak of {int(dry_streak)} consecutive months")

    if ndvi_3m is not None and not pd_is_nan(ndvi_3m):
        if ndvi_3m < -10:
            contributing_factors.append(f"Severe vegetation vegetative stress ({format_anomaly(ndvi_3m)} NDVI anomaly)")
        elif ndvi_3m < 0:
            contributing_factors.append(f"Mild vegetation vegetative deficit ({format_anomaly(ndvi_3m)} NDVI anomaly)")

    if price_z is not None and not pd_is_nan(price_z):
        if price_z > 1.0:
            contributing_factors.append(f"Marked staple food price pressure ({format_zscore(price_z)} above historical baseline)")

    if prev_ipc in ["Crisis", "Emergency", "Catastrophe"]:
        contributing_factors.append(f"Pre-existing acute vulnerability (prior IPC phase: {prev_ipc})")

    lines = [
        f"**Automated Risk Summary for {county_name} ({period})**",
        f"- **Model Estimated Risk Probability:** `{risk_prob * 100:.1f}%` ({risk_band} Risk)",
    ]

    if contributing_factors:
        lines.append("- **Statistical Risk Correlates:**")
        for factor in contributing_factors:
            lines.append(f"  * {factor}")
    else:
        lines.append("- **Statistical Risk Correlates:** Climate, vegetation, and market indicators remain within normal seasonal ranges.")

    lines.append("")
    lines.append(
        "> **Important Non-Causal Note:** These indicators are statistical features correlated with "
        "historical acute food insecurity classifications. Feature presence does not imply direct "
        "causality; humanitarian food insecurity arises from complex, interacting socio-ecological, "
        "market, conflict, and livelihood dynamics."
    )

    return "\n".join(lines)
