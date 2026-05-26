# backend/verticals/analyst/tools/chart_tool.py
"""
Chart generation tool using Plotly.
Returns base64-encoded PNG charts for the React UI.
"""
import base64
import logging
import json
from io import BytesIO
from typing import Literal

logger = logging.getLogger(__name__)

ChartType = Literal["bar", "line", "scatter", "pie", "histogram", "heatmap"]


async def generate_chart(
    chart_type:  ChartType,
    data:        dict,          # {"x": [...], "y": [...], "labels": [...]}
    title:       str = "",
    x_label:     str = "",
    y_label:     str = "",
    color:       str = "#534AB7",
) -> str | None:
    """
    Generate a Plotly chart and return as base64 PNG.
    Returns None if chart generation fails.
    """
    try:
        import plotly.graph_objects as go
        import plotly.io as pio

        x      = data.get("x", [])
        y      = data.get("y", [])
        labels = data.get("labels", x)

        fig = go.Figure()

        if chart_type == "bar":
            fig.add_trace(go.Bar(x=x, y=y, marker_color=color))
        elif chart_type == "line":
            fig.add_trace(go.Scatter(x=x, y=y, mode="lines+markers",
                                     line=dict(color=color, width=2)))
        elif chart_type == "scatter":
            fig.add_trace(go.Scatter(x=x, y=y, mode="markers",
                                     marker=dict(color=color, size=8)))
        elif chart_type == "pie":
            fig.add_trace(go.Pie(labels=labels, values=y, hole=0.3))
        elif chart_type == "histogram":
            fig.add_trace(go.Histogram(x=x, marker_color=color))
        else:
            fig.add_trace(go.Bar(x=x, y=y, marker_color=color))

        fig.update_layout(
            title=dict(text=title, font=dict(size=14)),
            xaxis_title=x_label,
            yaxis_title=y_label,
            plot_bgcolor="white",
            paper_bgcolor="white",
            font=dict(family="sans-serif", size=11),
            margin=dict(l=40, r=20, t=50, b=40),
            width=700,
            height=400,
        )

        img_bytes = pio.to_image(fig, format="png", scale=2)
        b64       = base64.b64encode(img_bytes).decode("utf-8")
        logger.info(f"Chart generated: {chart_type} '{title}' ({len(b64)} chars)")
        return b64

    except ImportError:
        logger.warning("Plotly not installed — install with: pip install plotly kaleido")
        return None
    except Exception as e:
        logger.error(f"Chart generation failed: {e}")
        return None


async def generate_chart_from_sql_result(
    sql_result:  dict,
    chart_type:  ChartType = "bar",
    x_column:    str = "",
    y_column:    str = "",
    title:       str = "",
) -> str | None:
    """
    Generate a chart directly from SQL query results.
    Auto-detects appropriate x and y columns if not specified.
    """
    rows    = sql_result.get("rows", [])
    columns = sql_result.get("columns", [])

    if not rows or not columns:
        return None

    # Auto-detect columns
    if not x_column and columns:
        x_column = columns[0]
    if not y_column and len(columns) > 1:
        y_column = columns[1]

    x_data = [str(row.get(x_column, "")) for row in rows]
    # FIXED: filter out NaN/None y values and their paired x labels to avoid silent chart corruption
    raw_y  = [row.get(y_column) for row in rows]
    paired = [(xv, yv) for xv, yv in zip(x_data, raw_y) if yv is not None]
    if not paired:
        logger.warning(f"Chart skipped: all values for column '{y_column}' are None/NaN")
        return None
    x_data, y_vals = zip(*paired)
    x_data = list(x_data)
    y_data = [float(v) for v in y_vals]

    return await generate_chart(
        chart_type=chart_type,
        data={"x": x_data, "y": y_data},
        title=title or f"{y_column} by {x_column}",
        x_label=x_column,
        y_label=y_column,
    )