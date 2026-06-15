"""
app.py — Campaign Experimentation & Engagement Intelligence
Run: streamlit run app.py
"""

import os, sys
sys.path.append(os.path.dirname(__file__))

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lift_analysis import run_lift_analysis, lift_by_day, exposure_curve
from engagement_analysis import (engagement_by_subject_strength,
                                 engagement_by_wordcount,
                                 engagement_by_send_time,
                                 fatigue_curve, content_correlations)
from report import generate_briefing

st.set_page_config(page_title="Campaign Intelligence", layout="wide")

INK="#0D1015"; PANEL="#151A22"; LINE="#252C38"; TEXT="#E8EBF0"; MUTE="#8C95A6"
TEAL="#3EB8A5"; AMBER="#E0A84E"; RED="#C96A5A"

st.markdown(f"""
<style>
.stApp {{ background:{INK}; color:{TEXT}; }}
section[data-testid="stSidebar"] {{ background:{PANEL}; border-right:1px solid {LINE}; }}
h1,h2,h3 {{ color:{TEXT}; font-family:Georgia,serif; }}
.kpi {{ background:{PANEL}; border:1px solid {LINE}; border-radius:10px; padding:16px 18px; }}
.kpi .l {{ color:{MUTE}; font-size:11px; text-transform:uppercase; letter-spacing:1.5px; }}
.kpi .v {{ color:{TEXT}; font-size:28px; font-weight:600; font-family:Georgia,serif; }}
.kpi .s {{ color:{TEAL}; font-size:12px; }}
.eyebrow {{ color:{AMBER}; font-size:11px; text-transform:uppercase; letter-spacing:3px; }}
.brief {{ background:{PANEL}; border:1px solid {LINE}; border-left:3px solid {TEAL};
  border-radius:8px; padding:16px 20px; font-family:Menlo,monospace; font-size:12.5px;
  line-height:1.65; white-space:pre-wrap; color:{TEXT}; }}
.caveat {{ background:{PANEL}; border:1px solid {AMBER}; border-radius:8px;
  padding:10px 14px; color:{TEXT}; font-size:13px; }}
</style>""", unsafe_allow_html=True)


@st.cache_data
def load_all():
    return {
        "lift": run_lift_analysis(), "by_day": lift_by_day(),
        "exposure": exposure_curve(),
        "subject": engagement_by_subject_strength(),
        "wordcount": engagement_by_wordcount(),
        "send_time": engagement_by_send_time(),
        "fatigue": fatigue_curve(), "corr": content_correlations(),
    }

D = load_all(); L = D["lift"]

st.markdown("<div class='eyebrow'>Digital Communication Analytics</div>", unsafe_allow_html=True)
st.markdown("# Campaign Experimentation & Engagement Intelligence")
st.markdown(f"<span style='color:{MUTE}'>Incremental lift from a randomized "
            f"588K-user experiment, plus content, timing, and frequency analysis "
            f"of 68K real marketing emails.</span>", unsafe_allow_html=True)
st.write("")

c1,c2,c3,c4 = st.columns(4)
with c1: st.markdown(f"<div class='kpi'><div class='l'>Incremental lift</div>"
    f"<div class='v'>+{L['rel_lift']*100:.0f}%</div>"
    f"<div class='s'>+{L['abs_lift']*100:.2f}pp absolute</div></div>", unsafe_allow_html=True)
with c2: st.markdown(f"<div class='kpi'><div class='l'>Significance</div>"
    f"<div class='v'>z = {L['z']:.1f}</div>"
    f"<div class='s'>p = {L['p_value']:.0e}</div></div>", unsafe_allow_html=True)
with c3: st.markdown(f"<div class='kpi'><div class='l'>Attributable conversions</div>"
    f"<div class='v'>{L['incremental_conversions']:,.0f}</div>"
    f"<div class='s'>across {L['n_treatment']:,} treated users</div></div>", unsafe_allow_html=True)
with c4: st.markdown(f"<div class='kpi'><div class='l'>Holdout design</div>"
    f"<div class='v'>96 / 4</div>"
    f"<div class='s'>{L['n_control']:,} control users</div></div>", unsafe_allow_html=True)

st.write(""); st.markdown("---")

# ---- Experiment section ----
st.markdown("<div class='eyebrow'>Module 1 · Experimentation</div>", unsafe_allow_html=True)
left, right = st.columns(2)

with left:
    st.markdown("### Lift by day of week")
    bd = D["by_day"]
    fig = go.Figure()
    colors = [TEAL if s else MUTE for s in bd["significant"]]
    fig.add_trace(go.Bar(x=bd["day"].astype(str), y=bd["abs_lift_pp"],
                         marker_color=colors,
                         text=[f"+{v:.2f}pp" for v in bd["abs_lift_pp"]],
                         textposition="outside"))
    fig.update_layout(height=330, paper_bgcolor=PANEL, plot_bgcolor=PANEL,
                      font_color=TEXT, margin=dict(l=10,r=10,t=10,b=10),
                      yaxis=dict(title="absolute lift (pp)", gridcolor=LINE),
                      xaxis=dict(gridcolor=LINE))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Teal = statistically significant (p<0.05). Thursday and Sunday "
               "show no measurable lift; early-week spend works hardest.")

with right:
    st.markdown("### Conversion vs ad exposure")
    ex = D["exposure"]
    fig = go.Figure(go.Bar(x=ex["exposure_band"].astype(str), y=ex["conv_rate_pct"],
                           marker_color=AMBER,
                           text=[f"{v:.1f}%" for v in ex["conv_rate_pct"]],
                           textposition="outside"))
    fig.update_layout(height=330, paper_bgcolor=PANEL, plot_bgcolor=PANEL,
                      font_color=TEXT, margin=dict(l=10,r=10,t=10,b=10),
                      yaxis=dict(title="conversion %", gridcolor=LINE),
                      xaxis=dict(title="ads seen", gridcolor=LINE, type="category"))
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("<div class='caveat'>Correlational, not causal: heavily-exposed "
                "users are more active people who convert more anyway. The causal "
                "estimate is the randomized comparison above.</div>",
                unsafe_allow_html=True)

st.markdown("---")

# ---- Engagement section ----
st.markdown("<div class='eyebrow'>Module 2 · Content & Engagement (68K emails)</div>",
            unsafe_allow_html=True)
a,b,c = st.columns(3)

with a:
    st.markdown("### Subject-line strength")
    sj = D["subject"]
    fig = go.Figure(go.Bar(x=sj["subject_strength"].astype(str), y=sj["engagement_pct"],
                           marker_color=TEAL))
    fig.update_layout(height=300, paper_bgcolor=PANEL, plot_bgcolor=PANEL,
                      font_color=TEXT, margin=dict(l=10,r=10,t=10,b=10),
                      yaxis=dict(title="engagement %", gridcolor=LINE),
                      xaxis=dict(gridcolor=LINE))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Counterintuitive: 'hotter' (salesy) subject lines engage LESS.")

with b:
    st.markdown("### Body length")
    wc = D["wordcount"]
    fig = go.Figure(go.Bar(x=wc["wc_band"].astype(str), y=wc["engagement_pct"],
                           marker_color=TEAL))
    fig.update_layout(height=300, paper_bgcolor=PANEL, plot_bgcolor=PANEL,
                      font_color=TEXT, margin=dict(l=10,r=10,t=10,b=10),
                      yaxis=dict(title="engagement %", gridcolor=LINE),
                      xaxis=dict(gridcolor=LINE))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Shorter emails win, monotonically: 33% vs 12% engagement.")

with c:
    st.markdown("### Frequency curve")
    ft = D["fatigue"]
    fig = go.Figure(go.Scatter(x=ft["past_comm_bucket"], y=ft["engagement_pct"],
                               mode="lines+markers", line=dict(color=RED, width=2)))
    fig.update_layout(height=300, paper_bgcolor=PANEL, plot_bgcolor=PANEL,
                      font_color=TEXT, margin=dict(l=10,r=10,t=10,b=10),
                      yaxis=dict(title="engagement %", gridcolor=LINE),
                      xaxis=dict(title="prior communications", gridcolor=LINE))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("U-shaped; right side is survivorship, not causation. See briefing.")

st.markdown("---")

# ---- Briefing + SQL ----
l2, r2 = st.columns([1,1])
with l2:
    st.markdown("<div class='eyebrow'>Auto-generated</div>", unsafe_allow_html=True)
    st.markdown("### Campaign briefing")
    brief = generate_briefing(L, D["by_day"], D["subject"], D["wordcount"], D["fatigue"])
    st.markdown(f"<div class='brief'>{brief}</div>", unsafe_allow_html=True)

with r2:
    st.markdown("<div class='eyebrow'>SQL layer</div>", unsafe_allow_html=True)
    st.markdown("### The queries behind the numbers")
    sql_dir = os.path.join(os.path.dirname(__file__), "..", "sql")
    files = sorted(f for f in os.listdir(sql_dir) if f.endswith(".sql"))
    pick = st.selectbox("Query", files)
    with open(os.path.join(sql_dir, pick)) as f:
        st.code(f.read(), language="sql")

st.markdown("---")
st.caption("Built by Satyam Patel. Data: two real public datasets (Kaggle): a "
           "588K-user randomized marketing experiment and 68K marketing emails "
           "with engagement outcomes. All lift claims come from the randomized "
           "comparison; correlational views are labeled as such.")
