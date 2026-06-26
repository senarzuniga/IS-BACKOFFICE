from typing import Any, Dict, List


def _try_import_plotly():
    try:
        import plotly.graph_objects as go  # type: ignore

        return go
    except Exception:
        return None


def flow_chart(state_counts: Dict[str, int]) -> Any:
    """Return a flow-chart representation. If Plotly available, return a figure, else dict."""
    go = _try_import_plotly()
    labels = list(state_counts.keys())
    values = [state_counts[k] for k in labels]
    if go:
        fig = go.Figure(go.Bar(x=values, y=labels, orientation="h"))
        fig.update_layout(title_text="Flow: reels per zone")
        return fig
    return {"type": "bar", "labels": labels, "values": values}


def saturation_chart(utilization: Dict[str, float]) -> Any:
    go = _try_import_plotly()
    labels = list(utilization.keys())
    values = [utilization[k] for k in labels]
    if go:
        fig = go.Figure(go.Bar(x=values, y=labels, orientation="h"))
        fig.update_layout(title_text="Saturation / Utilization (%)")
        return fig
    return {"type": "bar", "labels": labels, "values": values}


def oee_chart(oee_by_stand: Dict[str, float]) -> Any:
    go = _try_import_plotly()
    labels = list(oee_by_stand.keys())
    values = [oee_by_stand[k] for k in labels]
    if go:
        fig = go.Figure(go.Bar(x=labels, y=values))
        fig.update_layout(title_text="OEE per Roll Stand (%)")
        return fig
    return {"type": "bar", "labels": labels, "values": values}
