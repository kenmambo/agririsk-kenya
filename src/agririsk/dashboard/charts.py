"""Plotly chart generation modules for AgriRisk Kenya dashboard pages."""

from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from agririsk.dashboard.formatting import RISK_COLORS

FEATURE_LABEL_MAP = {
    "rainfall_anomaly_1m": "1-Month Rainfall Anomaly (%)",
    "rainfall_anomaly_3m": "3-Month Rainfall Anomaly (%)",
    "rainfall_rolling_3m": "3-Month Cumulative Rainfall (mm)",
    "consecutive_dry_months": "Consecutive Dry Months Count",
    "ndvi_anomaly_1m": "1-Month NDVI Anomaly (%)",
    "ndvi_anomaly_3m": "3-Month NDVI Anomaly (%)",
    "ndvi_trend_3m": "3-Month NDVI Trend Slope",
    "maize_price_change_1m": "1-Month Maize Price Change (%)",
    "maize_price_change_3m": "3-Month Maize Price Change (%)",
    "maize_price_zscore": "Maize Price Z-Score (\u03c3)",
    "previous_ipc_phase": "Prior Month IPC Acute Phase",
}


def _base_chart_layout(title: str, y_title: str, height: int = 340) -> Dict[str, Any]:
    """Return standardized Plotly layout dictionary."""
    return dict(
        title=dict(text=title, font=dict(size=14, color="#1e293b", family="sans-serif")),
        yaxis=dict(title=y_title, gridcolor="#f1f5f9", zerolinecolor="#cbd5e1"),
        xaxis=dict(gridcolor="#f8fafc", tickangle=-30),
        margin=dict(l=40, r=20, t=40, b=40),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#ffffff",
        height=height,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1.0)
    )


def plot_risk_probability_timeline(df: pd.DataFrame, county_name: str) -> go.Figure:
    """Generate interactive timeline of model-estimated acute food insecurity risk probability.

    Args:
        df: Single-county chronological timeseries DataFrame.
        county_name: Canonical county name.

    Returns:
        Plotly Figure with risk band threshold lines.
    """
    fig = go.Figure()

    # Model Risk Probability Line
    fig.add_trace(go.Scatter(
        x=df["period"],
        y=df["model_risk_prob"] * 100,
        mode="lines+markers",
        name="Model Risk Prob (%)",
        line=dict(color="#1f77b4", width=3),
        marker=dict(size=6, color="#0f172a"),
        hovertemplate="<b>Risk Probability</b>: %{y:.1f}%<extra></extra>"
    ))

    # Reference Thresholds
    fig.add_hline(y=75, line_dash="dash", line_color=RISK_COLORS["High"], line_width=1.5,
                  annotation_text="High Risk (75%)", annotation_position="top right")
    fig.add_hline(y=50, line_dash="dash", line_color=RISK_COLORS["Elevated"], line_width=1.5,
                  annotation_text="Elevated Risk (50%)", annotation_position="top right")
    fig.add_hline(y=25, line_dash="dash", line_color=RISK_COLORS["Moderate"], line_width=1.5,
                  annotation_text="Moderate Risk (25%)", annotation_position="top right")

    fig.update_layout(
        **_base_chart_layout(
            title=f"<b>Model Risk Probability Timeline: {county_name}</b>",
            y_title="Model Estimated Risk Probability (%)",
            height=340
        ),
        yaxis_range=[0, 105]
    )
    return fig


def plot_rainfall_anomaly_timeline(df: pd.DataFrame, county_name: str) -> go.Figure:
    """Generate bar and line chart of monthly rainfall anomalies.

    Args:
        df: Single-county chronological timeseries DataFrame.
        county_name: Canonical county name.

    Returns:
        Plotly Figure with rainfall deficit/surplus visualization.
    """
    fig = go.Figure()

    # 1M Anomaly as bars
    colors = ["#dc2626" if val < 0 else "#2563eb" for val in df["rainfall_anomaly_1m"].fillna(0)]
    fig.add_trace(go.Bar(
        x=df["period"],
        y=df["rainfall_anomaly_1m"],
        name="1M Rain Anomaly (%)",
        marker_color=colors,
        opacity=0.75,
        hovertemplate="1M Anomaly: %{y:+.1f}%<extra></extra>"
    ))

    # 3M Anomaly as line
    fig.add_trace(go.Scatter(
        x=df["period"],
        y=df["rainfall_anomaly_3m"],
        mode="lines+markers",
        name="3M Rolling Anomaly (%)",
        line=dict(color="#0f172a", width=2.5),
        marker=dict(size=4),
        hovertemplate="3M Rolling Anomaly: %{y:+.1f}%<extra></extra>"
    ))

    fig.add_hline(y=0, line_color="#475569", line_width=1)

    fig.update_layout(
        **_base_chart_layout(
            title=f"<b>Rainfall Anomalies vs Baseline: {county_name}</b>",
            y_title="Rainfall Anomaly (%)",
            height=320
        )
    )
    return fig


def plot_ndvi_anomaly_timeline(df: pd.DataFrame, county_name: str) -> go.Figure:
    """Generate NDVI vegetation health anomaly timeline chart.

    Args:
        df: Single-county chronological timeseries DataFrame.
        county_name: Canonical county name.

    Returns:
        Plotly Figure showing vegetation stress trajectory.
    """
    fig = go.Figure()

    # 1M NDVI Anomaly
    fig.add_trace(go.Scatter(
        x=df["period"],
        y=df["ndvi_anomaly_1m"],
        mode="lines",
        name="1M NDVI Anomaly (%)",
        line=dict(color="#10b981", width=1.5, dash="dot"),
        hovertemplate="1M NDVI Anomaly: %{y:+.1f}%<extra></extra>"
    ))

    # 3M NDVI Anomaly with stress fill
    fig.add_trace(go.Scatter(
        x=df["period"],
        y=df["ndvi_anomaly_3m"],
        mode="lines+markers",
        name="3M Rolling NDVI Anomaly (%)",
        line=dict(color="#047857", width=2.5),
        marker=dict(size=4),
        hovertemplate="3M Rolling NDVI Anomaly: %{y:+.1f}%<extra></extra>"
    ))

    fig.add_hline(y=0, line_color="#475569", line_width=1)
    fig.add_hline(y=-10, line_dash="dash", line_color="#d97706", line_width=1,
                  annotation_text="Vegetation Stress Alert (-10%)", annotation_position="bottom right")

    fig.update_layout(
        **_base_chart_layout(
            title=f"<b>Vegetation Index (NDVI) Anomalies: {county_name}</b>",
            y_title="NDVI Anomaly (%)",
            height=320
        )
    )
    return fig


def plot_market_price_timeline(df: pd.DataFrame, county_name: str) -> go.Figure:
    """Generate staple maize price standardized z-score timeline chart.

    Args:
        df: Single-county chronological timeseries DataFrame.
        county_name: Canonical county name.

    Returns:
        Plotly Figure showing price anomaly pressure.
    """
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["period"],
        y=df["maize_price_zscore"],
        mode="lines+markers",
        name="Maize Price Z-Score (\u03c3)",
        line=dict(color="#d97706", width=2.5),
        marker=dict(size=5, color="#b45309"),
        hovertemplate="Price Z-Score: %{y:+.2f}\u03c3<extra></extra>"
    ))

    # Threshold lines for price stress
    fig.add_hline(y=1.0, line_dash="dash", line_color="#f59e0b", line_width=1.2,
                  annotation_text="+1\u03c3 Moderate Price Pressure", annotation_position="top right")
    fig.add_hline(y=2.0, line_dash="dash", line_color="#ef4444", line_width=1.2,
                  annotation_text="+2\u03c3 Severe Price Shock", annotation_position="top right")
    fig.add_hline(y=0.0, line_color="#94a3b8", line_width=1)

    fig.update_layout(
        **_base_chart_layout(
            title=f"<b>Staple Food Market Pressure (Maize Price Z-Score): {county_name}</b>",
            y_title="Standardized Price Z-Score (\u03c3)",
            height=320
        )
    )
    return fig


def plot_ipc_classification_timeline(df: pd.DataFrame, county_name: str) -> go.Figure:
    """Generate stepped timeline of official/historical IPC acute food insecurity phases.

    Args:
        df: Single-county chronological timeseries DataFrame.
        county_name: Canonical county name.

    Returns:
        Plotly Figure clearly indicating official benchmark status.
    """
    fig = go.Figure()

    # Phase numeric mapping
    ipc_labels = {
        1.0: "Phase 1: Minimal",
        2.0: "Phase 2: Stressed",
        3.0: "Phase 3: Crisis",
        4.0: "Phase 4: Emergency",
        5.0: "Phase 5: Catastrophe"
    }

    fig.add_trace(go.Scatter(
        x=df["period"],
        y=df["previous_ipc_phase"],
        mode="lines+markers",
        line=dict(shape="hv", color="#7c3aed", width=3),
        marker=dict(size=7, symbol="diamond", color="#5b21b6"),
        name="Official IPC Phase",
        hovertemplate="<b>Official IPC Phase</b>: %{y}<extra></extra>"
    ))

    # Reference lines for Crisis threshold
    fig.add_hline(y=3.0, line_dash="dash", line_color="#dc2626", line_width=1.5,
                  annotation_text="IPC Phase 3+ (Crisis & Above)", annotation_position="top right")

    layout = _base_chart_layout(
        title=f"<b>Official / Historical IPC Acute Phase History: {county_name}</b>",
        y_title="Official IPC Acute Phase",
        height=320
    )
    layout["yaxis"].update(dict(
        tickmode="array",
        tickvals=[1, 2, 3, 4, 5],
        ticktext=["1: Minimal", "2: Stressed", "3: Crisis", "4: Emergency", "5: Catastrophe"],
        range=[0.8, 4.5],
        gridcolor="#f1f5f9"
    ))
    fig.update_layout(**layout)
    return fig


def plot_global_feature_importance(importance_dict: Dict[str, float], top_n: int = 10) -> go.Figure:
    """Generate horizontal bar chart of global model feature importance.

    Args:
        importance_dict: Dictionary mapping feature column name to importance value.
        top_n: Max features to display.

    Returns:
        Plotly Figure.
    """
    sorted_items = sorted(importance_dict.items(), key=lambda x: x[1], reverse=True)[:top_n]
    features = [FEATURE_LABEL_MAP.get(k, k) for k, v in sorted_items]
    values = [v for k, v in sorted_items]

    # Invert for horizontal bar top-to-bottom display
    features = features[::-1]
    values = values[::-1]

    fig = go.Figure(go.Bar(
        x=values,
        y=features,
        orientation="h",
        marker=dict(
            color=values,
            colorscale="Viridis",
            showscale=False
        ),
        hovertemplate="<b>%{y}</b><br>Importance: %{x:.4f}<extra></extra>"
    ))

    fig.update_layout(
        title=dict(text="<b>Random Forest Feature Importance (Mean Decrease in Impurity)</b>", font=dict(size=14)),
        xaxis=dict(title="Relative Importance Weight", gridcolor="#f1f5f9"),
        yaxis=dict(gridcolor="#f8fafc"),
        margin=dict(l=180, r=20, t=40, b=40),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#ffffff",
        height=380
    )
    return fig


def plot_local_feature_contributions(county_row: pd.Series) -> go.Figure:
    """Generate bar chart of standardized/normalized feature values for a specific county-month.

    Args:
        county_row: Single row Series of feature values.

    Returns:
        Plotly Figure.
    """
    key_features = [
        ("rainfall_anomaly_3m", "3M Rainfall Anomaly (%)", county_row.get("rainfall_anomaly_3m")),
        ("consecutive_dry_months", "Consecutive Dry Months", county_row.get("consecutive_dry_months")),
        ("ndvi_anomaly_3m", "3M NDVI Anomaly (%)", county_row.get("ndvi_anomaly_3m")),
        ("maize_price_zscore", "Maize Price Z-Score (\u03c3)", county_row.get("maize_price_zscore")),
        ("previous_ipc_phase", "Prior IPC Phase", county_row.get("previous_ipc_phase")),
    ]

    labels = []
    vals = []
    colors = []

    for key, label, val in key_features:
        if val is not None and not pd.isna(val):
            labels.append(label)
            vals.append(float(val))
            # Color logic: severe drought / high price / high IPC = red, else blue
            if key == "rainfall_anomaly_3m" and val < -20:
                colors.append("#dc2626")
            elif key == "ndvi_anomaly_3m" and val < -10:
                colors.append("#dc2626")
            elif key == "maize_price_zscore" and val > 1.0:
                colors.append("#dc2626")
            elif key == "consecutive_dry_months" and val >= 2:
                colors.append("#ea580c")
            elif key == "previous_ipc_phase" and val >= 3:
                colors.append("#dc2626")
            else:
                colors.append("#0284c7")

    fig = go.Figure(go.Bar(
        x=vals,
        y=labels,
        orientation="h",
        marker_color=colors,
        text=[f"{v:.1f}" for v in vals],
        textposition="outside",
        hovertemplate="<b>%{y}</b>: %{x:.2f}<extra></extra>"
    ))

    fig.update_layout(
        title=dict(text="<b>Key Environmental & Socioeconomic Indicators for Selected Month</b>", font=dict(size=13)),
        xaxis=dict(title="Indicator Value", gridcolor="#f1f5f9"),
        margin=dict(l=180, r=40, t=40, b=40),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#ffffff",
        height=260
    )
    return fig


def plot_confusion_matrix_heatmap(cm: List[List[int]]) -> go.Figure:
    """Generate confusion matrix heatmap for model performance page.

    Args:
        cm: 2x2 list of confusion matrix counts [[TN, FP], [FN, TP]].

    Returns:
        Plotly Figure.
    """
    z = cm
    x = ["Predicted Normal (0)", "Predicted Crisis+ (1)"]
    y = ["Actual Normal (0)", "Actual Crisis+ (1)"]

    annotations = []
    labels = [["TN", "FP"], ["FN", "TP"]]
    for i in range(2):
        for j in range(2):
            count = z[i][j]
            lbl = labels[i][j]
            annotations.append(dict(
                x=x[j], y=y[i],
                text=f"<b>{lbl}</b><br>{count}",
                showarrow=False,
                font=dict(size=15, color="white" if count > 15 else "#1e293b")
            ))

    fig = go.Figure(data=go.Heatmap(
        z=z, x=x, y=y,
        colorscale="Blues",
        showscale=False
    ))

    fig.update_layout(
        title=dict(text="<b>Test Set Confusion Matrix (2024 Holdout)</b>", font=dict(size=14)),
        annotations=annotations,
        margin=dict(l=60, r=40, t=50, b=40),
        height=320,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#ffffff"
    )
    return fig
