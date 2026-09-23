"""Plotly chart builders + palet warna terpusat.

Aturan warna: merah HANYA untuk risiko/kerugian/kondisi kritis (L(t),
histogram kerugian, garis VaR, badge error). Warna lain netral.
"""

import numpy as np
import plotly.graph_objects as go

CHART_HEIGHT = 320
CHART_MARGIN = dict(l=40, r=20, t=30, b=40)

COLORS = {"E": "#2E86AB", "D": "#6A4C93", "P": "#F4A261", "L": "#E63946"}


def _hex_to_rgba(hex_color, alpha):
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


def line_chart(t, y, color, fill=False, y_unit=None):
    """Chart garis tunggal. Judul TIDAK di-set di sini — sub-heading
    st.markdown di atas chart sudah jadi satu-satunya judul (menghindari
    judul terduplikasi). y_unit tampil sebagai label sumbu-Y kalau diisi."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=t, y=y, mode="lines", line=dict(color=color),
        fill="tozeroy" if fill else None,
        fillcolor=color if fill else None,
    ))
    if fill:
        fig.update_traces(fillcolor=_hex_to_rgba(color, 0.25))
    fig.update_layout(xaxis_title="t (tahun)", yaxis_title=y_unit,
                       height=CHART_HEIGHT, margin=CHART_MARGIN)
    return fig


def histogram_chart(losses, var, conf, unit=""):
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=losses, nbinsx=40, marker_color=COLORS["L"], opacity=0.8))
    fig.add_vline(x=var, line_dash="dash", line_color=COLORS["L"],
                  annotation_text=f"VaR {int(conf*100)}%", annotation_position="top")
    fig.update_layout(xaxis_title=f"Total kerugian ekonomi ({unit})" if unit else "Total kerugian ekonomi",
                       yaxis_title="Frekuensi", height=CHART_HEIGHT, margin=CHART_MARGIN)
    return fig


def tornado_chart(sens, unit=""):
    names = [s[0] for s in sens]; base_val = sens[0][2]
    low_diff = [s[1] - base_val for s in sens]
    high_diff = [s[3] - base_val for s in sens]
    fig = go.Figure()
    fig.add_trace(go.Bar(y=names, x=high_diff, orientation="h",
                          name="+20%", marker_color="#E63946", opacity=0.8))
    fig.add_trace(go.Bar(y=names, x=low_diff, orientation="h",
                          name="-20%", marker_color="#2E86AB", opacity=0.8))
    fig.add_vline(x=0, line_color="black", line_width=0.8)
    fig.update_layout(barmode="overlay",
                       xaxis_title=f"Perubahan total kerugian ({unit})" if unit else "Perubahan total kerugian",
                       height=CHART_HEIGHT, margin=CHART_MARGIN)
    return fig
