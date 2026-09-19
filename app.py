"""
ARIES — Analysis of Risk In Energy Systems
Single-page Streamlit GUI yang mem-port seluruh modul dari notebook riset:
  1) Dinamika sistem energi-ekonomi (ODE: E, D, P, L)
  2) Analisis kestabilan (Jacobian & eigenvalue)
  3) Analisis risiko ekonomi (Monte Carlo VaR/CVaR + sensitivity analysis)
  4) Perbandingan skenario kebijakan

Jalankan dengan:
    streamlit run app.py
"""

import numpy as np
import pandas as pd
from scipy.integrate import odeint
import plotly.graph_objects as go
import streamlit as st

_trapz = getattr(np, "trapezoid", None) or np.trapz

# ============================================================
# 1. MODELING ENGINE  (persis sama dengan notebook, cell 3 & 5)
# ============================================================

def investment_function(t, params):
    """I(t): laju investasi infrastruktur energi."""
    I0 = params["I0"]
    ramp = params.get("I_ramp", 0.0)
    step_t = params.get("I_step_t", None)
    step_val = params.get("I_step_val", 0.0)
    I_t = I0 + ramp * t
    if step_t is not None and t >= step_t:
        I_t += step_val
    return max(I_t, 0.0)


def activity_function(t, params):
    """G(t): tingkat aktivitas ekonomi (pertumbuhan eksponensial)."""
    G0 = params["G0"]
    g_rate = params.get("g_rate", 0.0)
    return G0 * np.exp(g_rate * t)


def energy_economy_ode(y, t, params):
    E, D, P = y
    delta = params["delta"]; alpha = params["alpha"]
    beta = params["beta"]; gamma = params["gamma"]
    I_t = investment_function(t, params)
    G_t = activity_function(t, params)
    dE = I_t - delta * E
    dD = alpha * G_t - beta * P
    dP = gamma * (D - E)
    return [dE, dD, dP]


def simulate(params, y0, t):
    sol = odeint(energy_economy_ode, y0, t, args=(params,))
    E, D, P = sol[:, 0], sol[:, 1], sol[:, 2]
    L = params["kappa"] * np.maximum(0.0, D - E)
    return E, D, P, L


def equilibrium_and_stability(params):
    """Asumsi I(t)=I0, G(t)=G0 konstan (rata-rata jangka panjang)."""
    delta, beta, gamma = params["delta"], params["beta"], params["gamma"]
    alpha, G0, I0 = params["alpha"], params["G0"], params["I0"]

    E_star = I0 / delta
    P_star = (alpha * G0) / beta
    D_star = E_star

    J = np.array([[-delta, 0.0, 0.0],
                  [0.0, 0.0, -beta],
                  [-gamma, gamma, 0.0]])
    eigvals = np.linalg.eigvals(J)
    max_real = np.max(eigvals.real)
    if max_real < -1e-9:
        status = "STABIL"
    elif abs(max_real) <= 1e-9:
        status = "MARGINAL (osilasi tak teredam)"
    else:
        status = "TIDAK STABIL"
    return {"E_star": E_star, "D_star": D_star, "P_star": P_star,
            "eigvals": eigvals, "status": status, "osc_freq": np.sqrt(beta * gamma)}


def total_economic_loss(params, y0, t):
    _, _, _, L = simulate(params, y0, t)
    return _trapz(L, t)


def monte_carlo_risk(base_params, y0, t, uncertain, n_sim=500, seed=42):
    rng = np.random.default_rng(seed)
    losses = np.zeros(n_sim)
    for i in range(n_sim):
        p = dict(base_params)
        for name, spec in uncertain.items():
            kind = spec[0]
            if kind == "normal":
                _, mean, std = spec
                p[name] = max(rng.normal(mean, std), 1e-6)
            elif kind == "uniform":
                _, low, high = spec
                p[name] = rng.uniform(low, high)
        losses[i] = total_economic_loss(p, y0, t)
    return losses


def risk_metrics(losses, conf=0.95):
    var = np.percentile(losses, conf * 100)
    tail = losses[losses >= var]
    cvar = tail.mean() if len(tail) > 0 else var
    return var, cvar


def sensitivity_analysis(base_params, y0, t, param_names, pct=0.2):
    base_loss = total_economic_loss(base_params, y0, t)
    results = []
    for name in param_names:
        p_low = dict(base_params); p_low[name] = base_params[name] * (1 - pct)
        p_high = dict(base_params); p_high[name] = base_params[name] * (1 + pct)
        results.append((name, total_economic_loss(p_low, y0, t), base_loss,
                         total_economic_loss(p_high, y0, t)))
    return results


# ============================================================
# 2. SKENARIO & DEFAULT PARAMETER (persis sama dengan notebook cell 7)
# ============================================================

SCENARIOS = {
    "Baseline (Business as Usual)": {},
    "Peningkatan Investasi Energi": {"I_ramp": 0.8},
    "Integrasi Energi Terbarukan": {"I_ramp": 0.5, "beta": 1.3},
    "Subsidi Energi": {"gamma": 0.4},
    "Investasi Darurat (step tahun ke-5)": {"I_step_t": 5, "I_step_val": 15.0},
}

DEFAULT_PARAMS = {
    "I0": 5.0, "delta": 0.08, "alpha": 1.2, "beta": 0.5,
    "gamma": 0.3, "G0": 10.0, "g_rate": 0.05, "kappa": 2.0,
    "I_ramp": 0.0, "I_step_t": None, "I_step_val": 0.0,
}
DEFAULT_Y0 = [50.0, 45.0, 20.0]  # E0, D0, P0

COLORS = {"E": "#2E86AB", "D": "#E63946", "P": "#F4A261", "L": "#6A4C93"}


# ============================================================
# 3. PLOTLY HELPERS
# ============================================================

CHART_HEIGHT = 320
CHART_MARGIN = dict(l=40, r=20, t=30, b=40)


def line_chart(t, y, title, color, fill=False):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=t, y=y, mode="lines", line=dict(color=color),
        fill="tozeroy" if fill else None,
        fillcolor=color if fill else None,
        opacity=1.0,
    ))
    if fill:
        fig.update_traces(fillcolor=_hex_to_rgba(color, 0.25))
    fig.update_layout(title=title, xaxis_title="t (tahun)",
                       height=CHART_HEIGHT, margin=CHART_MARGIN)
    return fig


def _hex_to_rgba(hex_color, alpha):
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


# ============================================================
# 4. STREAMLIT — LAYOUT
# ============================================================

st.set_page_config(page_title="ARIES — Energy Risk DSS", layout="wide")

st.title("⚡ ARIES")
st.caption("**A**nalysis of **R**isk **I**n **E**nergy **S**ystems — "
           "Decision Support System berbasis Mathematical Modeling & System Dynamics")

# ---------------- SIDEBAR: INPUT (Expert Mode) ----------------
st.sidebar.header("⚙️ Input Skenario & Parameter")

scenario_name = st.sidebar.selectbox("Pilih Skenario Kebijakan", list(SCENARIOS.keys()))

st.sidebar.markdown("---")
st.sidebar.subheader("Adjust Parameter Manual")
I0 = st.sidebar.slider("I0 (investasi dasar)", 0.0, 20.0, DEFAULT_PARAMS["I0"], 0.5)
delta = st.sidebar.slider("δ (depresiasi infrastruktur)", 0.01, 0.5, DEFAULT_PARAMS["delta"], 0.01)
alpha = st.sidebar.slider("α (elastisitas demand thd ekonomi)", 0.1, 3.0, DEFAULT_PARAMS["alpha"], 0.1)
beta = st.sidebar.slider("β (sensitivitas demand thd harga)", 0.1, 3.0, DEFAULT_PARAMS["beta"], 0.1)
gamma = st.sidebar.slider("γ (sensitivitas harga thd gap)", 0.05, 2.0, DEFAULT_PARAMS["gamma"], 0.05)
G0 = st.sidebar.slider("G0 (aktivitas ekonomi awal)", 1.0, 30.0, DEFAULT_PARAMS["G0"], 1.0)
g_rate = st.sidebar.slider("g (laju pertumbuhan ekonomi)", 0.0, 0.2, DEFAULT_PARAMS["g_rate"], 0.01)
kappa = st.sidebar.slider("κ (nilai ekonomi dari shortage)", 0.1, 10.0, DEFAULT_PARAMS["kappa"], 0.1)
T_end = st.sidebar.slider("Horizon Simulasi (tahun)", 5, 60, 15, 1)

st.sidebar.markdown("---")
st.sidebar.subheader("Pengaturan Monte Carlo")
n_sim = st.sidebar.slider("Jumlah simulasi", 100, 3000, 500, 100)
conf = st.sidebar.slider("Confidence level", 0.80, 0.99, 0.95, 0.01)
delta_std = st.sidebar.slider("std(δ)", 0.0, 0.1, 0.02, 0.005)
gamma_std = st.sidebar.slider("std(γ)", 0.0, 0.5, 0.10, 0.01)
I0_std = st.sidebar.slider("std(I0)", 0.0, 5.0, 1.50, 0.10)

st.sidebar.markdown("---")
st.sidebar.subheader("Perbandingan Skenario")
selected_scenarios = st.sidebar.multiselect(
    "Pilih skenario yang dibandingkan", list(SCENARIOS.keys()),
    default=list(SCENARIOS.keys()),
)

# assemble active params
base_params = dict(DEFAULT_PARAMS)
base_params.update({"I0": I0, "delta": delta, "alpha": alpha, "beta": beta,
                     "gamma": gamma, "G0": G0, "g_rate": g_rate, "kappa": kappa})
params = dict(base_params)
params.update(SCENARIOS[scenario_name])

t = np.linspace(0, T_end, 300)

# ============================================================
# SECTION 1 — DINAMIKA SISTEM
# ============================================================
st.header("1. Dinamika Sistem Energi–Ekonomi")
st.markdown(f"Skenario aktif: **{scenario_name}**")

E, D, P, L = simulate(params, DEFAULT_Y0, t)
total_loss = _trapz(L, t)

st.markdown("##### 1.1 Kapasitas Energi E(t)")
st.plotly_chart(line_chart(t, E, "Kapasitas Energi E(t)", COLORS["E"]), use_container_width=True)

st.markdown("##### 1.2 Permintaan Energi D(t)")
st.plotly_chart(line_chart(t, D, "Permintaan Energi D(t)", COLORS["D"]), use_container_width=True)

st.markdown("##### 1.3 Harga Energi P(t)")
st.plotly_chart(line_chart(t, P, "Harga Energi P(t)", COLORS["P"]), use_container_width=True)

st.markdown("##### 1.4 Kerugian Ekonomi L(t)")
st.plotly_chart(line_chart(t, L, "Kerugian Ekonomi L(t)", COLORS["L"], fill=True), use_container_width=True)

c1, c2, c3 = st.columns(3)
c1.metric("Total Kerugian Kumulatif", f"{total_loss:.2f}")
c2.metric("Kapasitas Akhir E(T)", f"{E[-1]:.2f}")
c3.metric("Permintaan Akhir D(T)", f"{D[-1]:.2f}")

# ============================================================
# SECTION 2 — ANALISIS KESTABILAN
# ============================================================
st.header("2. Analisis Kestabilan")

stab = equilibrium_and_stability(params)

st.markdown("##### 2.1 Titik Ekuilibrium")
e1, e2, e3 = st.columns(3)
e1.metric("E*", f"{stab['E_star']:.3f}")
e2.metric("D*", f"{stab['D_star']:.3f}")
e3.metric("P*", f"{stab['P_star']:.3f}")

st.markdown("##### 2.2 Eigenvalue Jacobian")
eig_df = pd.DataFrame({
    "λ": [f"λ{i+1}" for i in range(len(stab["eigvals"]))],
    "Re(λ)": [f"{ev.real:.4f}" for ev in stab["eigvals"]],
    "Im(λ)": [f"{ev.imag:+.4f}i" for ev in stab["eigvals"]],
})
st.dataframe(eig_df, hide_index=True, use_container_width=True)

st.markdown("##### 2.3 Frekuensi & Periode Osilasi (D–P)")
if stab["osc_freq"] > 0:
    st.latex(r"\omega = \sqrt{\beta \gamma} \qquad\qquad T = \dfrac{2\pi}{\omega}")
    f1, f2 = st.columns(2)
    f1.metric("ω (frekuensi)", f"{stab['osc_freq']:.4f}")
    f2.metric("T (periode)", f"{2*np.pi/stab['osc_freq']:.2f} tahun")

st.markdown("##### 2.4 Status Sistem")
if stab["status"] == "STABIL":
    st.success(f"Status sistem: {stab['status']}")
elif "MARGINAL" in stab["status"]:
    st.warning(f"Status sistem: {stab['status']}")
else:
    st.error(f"Status sistem: {stab['status']}")

# ============================================================
# SECTION 3 — ANALISIS RISIKO (MONTE CARLO + SENSITIVITY)
# ============================================================
st.header("3. Analisis Risiko Ekonomi (Monte Carlo)")

mc_inputs = {
    "scenario_name": scenario_name, "T_end": T_end, "n_sim": n_sim, "conf": conf,
    "delta_std": delta_std, "gamma_std": gamma_std, "I0_std": I0_std, "params": params,
}

run_mc = st.button("▶ Jalankan Monte Carlo")
if run_mc:
    uncertain = {
        "delta": ("normal", params["delta"], delta_std),
        "gamma": ("normal", params["gamma"], gamma_std),
        "I0": ("normal", params["I0"], I0_std),
    }
    losses = monte_carlo_risk(params, DEFAULT_Y0, t, uncertain, n_sim=n_sim)
    var, cvar = risk_metrics(losses, conf)
    sens = sensitivity_analysis(params, DEFAULT_Y0, t,
                                 ["delta", "alpha", "beta", "gamma", "kappa", "I0", "g_rate"])
    st.session_state["mc_results"] = {
        "losses": losses, "var": var, "cvar": cvar, "sens": sens, "inputs": mc_inputs,
    }

mc_results = st.session_state.get("mc_results")

if mc_results is None:
    st.info("Klik tombol **Jalankan Monte Carlo** di atas untuk menghitung VaR/CVaR "
            "dan sensitivity analysis.")
else:
    if mc_results["inputs"] != mc_inputs:
        st.caption("⚠️ Parameter berubah — klik ulang untuk memperbarui.")

    losses, var, cvar, sens = (mc_results["losses"], mc_results["var"],
                                mc_results["cvar"], mc_results["sens"])
    mc_conf = mc_results["inputs"]["conf"]

    c1, c2, c3 = st.columns(3)
    c1.metric("Rata-rata Kerugian", f"{losses.mean():.2f}")
    c2.metric(f"VaR {int(mc_conf*100)}%", f"{var:.2f}")
    c3.metric(f"CVaR {int(mc_conf*100)}%", f"{cvar:.2f}")

    st.markdown("##### 3.1 Distribusi Total Kerugian Ekonomi (Monte Carlo)")
    fig_hist = go.Figure()
    fig_hist.add_trace(go.Histogram(x=losses, nbinsx=40, marker_color=COLORS["L"], opacity=0.8))
    fig_hist.add_vline(x=var, line_dash="dash", line_color="red",
                        annotation_text=f"VaR {int(mc_conf*100)}%", annotation_position="top")
    fig_hist.update_layout(xaxis_title="Total kerugian ekonomi", yaxis_title="Frekuensi",
                            height=CHART_HEIGHT, margin=CHART_MARGIN)
    st.plotly_chart(fig_hist, use_container_width=True)

    st.markdown("##### 3.2 Sensitivitas Parameter (±20%)")
    names = [s[0] for s in sens]; base_val = sens[0][2]
    low_diff = [s[1] - base_val for s in sens]
    high_diff = [s[3] - base_val for s in sens]
    fig_tornado = go.Figure()
    fig_tornado.add_trace(go.Bar(y=names, x=high_diff, orientation="h",
                                  name="+20%", marker_color="#E63946", opacity=0.8))
    fig_tornado.add_trace(go.Bar(y=names, x=low_diff, orientation="h",
                                  name="-20%", marker_color="#2E86AB", opacity=0.8))
    fig_tornado.add_vline(x=0, line_color="black", line_width=0.8)
    fig_tornado.update_layout(barmode="overlay", xaxis_title="Perubahan total kerugian",
                               height=CHART_HEIGHT, margin=CHART_MARGIN)
    st.plotly_chart(fig_tornado, use_container_width=True)

# ============================================================
# SECTION 4 — PERBANDINGAN SKENARIO
# ============================================================
st.header("4. Perbandingan Skenario Kebijakan")

if not selected_scenarios:
    st.info("Pilih minimal satu skenario di sidebar untuk membandingkan.")
elif len(selected_scenarios) == 1:
    name = selected_scenarios[0]
    p = dict(base_params); p.update(SCENARIOS[name])
    _, _, _, L_i = simulate(p, DEFAULT_Y0, t)
    loss_i = _trapz(L_i, t)

    st.markdown(f"Skenario terpilih: **{name}**")
    st.markdown("##### 4.1 Kerugian Ekonomi L(t)")
    st.plotly_chart(line_chart(t, L_i, f"Kerugian Ekonomi L(t) — {name}", COLORS["L"], fill=True),
                     use_container_width=True)
    st.metric("Total Kerugian Kumulatif", f"{loss_i:.2f}")
    st.caption("Pilih 2+ skenario untuk grafik perbandingan.")
else:
    bar_names, bar_losses = [], []
    fig_cmp = go.Figure()
    for name in selected_scenarios:
        p = dict(base_params); p.update(SCENARIOS[name])
        _, _, _, L_i = simulate(p, DEFAULT_Y0, t)
        fig_cmp.add_trace(go.Scatter(x=t, y=L_i, mode="lines", name=name))
        bar_names.append(name); bar_losses.append(_trapz(L_i, t))

    st.markdown("##### 4.1 Kerugian Ekonomi L(t) per Skenario")
    fig_cmp.update_layout(xaxis_title="t (tahun)", height=CHART_HEIGHT, margin=CHART_MARGIN,
                           legend=dict(font=dict(size=9)))
    st.plotly_chart(fig_cmp, use_container_width=True)

    st.markdown("##### 4.2 Total Kerugian Ekonomi Kumulatif")
    fig_bar = go.Figure(go.Bar(x=bar_names, y=bar_losses, marker_color="#F4A261"))
    fig_bar.update_layout(height=CHART_HEIGHT, margin=CHART_MARGIN,
                           xaxis=dict(tickfont=dict(size=9)))
    st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("**Ringkasan Total Kerugian**")
    st.dataframe(pd.DataFrame({"Skenario": bar_names,
                                "Total Kerugian": [f"{v:.2f}" for v in bar_losses]}),
                 hide_index=True, use_container_width=True)

st.markdown("---")
st.caption("ARIES · Prototipe riset.")
