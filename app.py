# This file is the Streamlit entry point for the AI Feature Prioritisation Engine — Elite UI.

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import math
from collections import Counter
from dotenv import load_dotenv
import html
from datetime import datetime

try:
    from fpdf import FPDF
except ImportError:
    import subprocess
    subprocess.run(["pip", "install", "fpdf2"], check=True)
    from fpdf import FPDF

from prioritiser import prioritise_features

load_dotenv()

# ══════════════════════════════════════════════════════════════════════════════
# CONFIG & STATE
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="AI Feature Prioritisation Engine",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

for k, v in {
    "features": [],
    "results": None,
    "error": None,
    "expanded_cards": set(),
    "theme": "dark",
    "scroll_to_results": False,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

EXAMPLE_FEATURES = [
    {"name": "AI size recommendation", "reach": 8, "impact": 7, "confidence": 8, "effort": 5,
     "description": "38% of returns are size-related costing Rs 420 Cr per year", "strategic_goal": "Retention"},
    {"name": "Dark mode",              "reach": 6, "impact": 4, "confidence": 9, "effort": 2,
     "description": "Users request dark mode for evening browsing",                "strategic_goal": "Delight"},
    {"name": "B2B bulk order pricing", "reach": 4, "impact": 9, "confidence": 6, "effort": 7,
     "description": "B2B buyers want volume discounts, no tiered pricing exists",  "strategic_goal": "Revenue"},
]

KANO_DARK  = {"Must-have": "#8B5CF6", "Performance": "#3B82F6", "Delight": "#EC4899", "Indifferent": "#6B7280"}
KANO_LIGHT = {"Must-have": "#7C3AED", "Performance": "#2563EB", "Delight": "#DB2777", "Indifferent": "#52525B"}
GOAL_C  = {"Retention": "#3B82F6", "Acquisition": "#F59E0B", "Revenue": "#22C55E", "Efficiency": "#8B5CF6", "Delight": "#EC4899"}
QTR_C   = {"Q1": "#3B82F6", "Q2": "#22C55E", "Q3": "#F59E0B", "Q4": "#EC4899"}

is_light = st.session_state.theme == "light"
KANO = KANO_LIGHT if is_light else KANO_DARK

def rs(f): return round(f["reach"] * f["impact"] * f["confidence"] / f["effort"], 1)

def pill(t, c):
    return (f'<span style="background:{c}1A;color:{c};border:1px solid {c}40;border-radius:20px;'
            f'font-size:11px;font-weight:500;padding:3px 10px;font-family:Inter,sans-serif;white-space:nowrap;">{t}</span>')

def ring(conf, delay=0):
    r, circ = 20, 2 * math.pi * 20
    target = circ * (1 - conf / 10)
    c = "#22C55E" if conf >= 7 else "#F59E0B" if conf >= 4 else "#EF4444"
    track = "rgba(0,0,0,0.08)" if is_light else "rgba(255,255,255,0.08)"
    return (f'<svg width="52" height="52" viewBox="0 0 52 52" fill="none" style="flex-shrink:0;">'
            f'<circle cx="26" cy="26" r="{r}" stroke="{track}" stroke-width="3" fill="none"/>'
            f'<circle cx="26" cy="26" r="{r}" stroke="{c}" stroke-width="3" fill="none"'
            f' stroke-dasharray="{circ:.2f}" stroke-dashoffset="{circ:.2f}" stroke-linecap="round"'
            f' transform="rotate(-90 26 26)"'
            f' style="--ring-target:{target:.2f}px;animation:ring-fill 800ms ease-out {delay}ms both;"/>'
            f'<text x="26" y="30" text-anchor="middle" font-family="JetBrains Mono,monospace"'
            f' font-size="10" fill="{c}">{conf*10}%</text></svg>')

def card_header(r, idx):
    """Returns compact single-line HTML for the card header (always visible)."""
    rank  = r.get("priority_rank", idx+1)
    name  = html.escape(str(r.get("feature_name", "")))
    rice  = r.get("rice_score", 0)
    kano  = html.escape(str(r.get("kano_category", "")))
    qtr   = html.escape(str(r.get("ship_quarter", "Q2")))
    top   = (rank == 1)
    kc    = KANO.get(r.get("kano_category", ""), "#6B7280")
    qc    = QTR_C.get(r.get("ship_quarter", "Q2"), "#6B7280")
    delay = idx * 80
    match = [f for f in st.session_state.features if f["name"] == r.get("feature_name", "")]
    conf  = match[0]["confidence"] if match else 7
    svg   = ring(conf, delay + 300)
    if top:
        if is_light:
            bdr  = "border:1px solid rgba(79,70,229,0.3);border-bottom:none;background:linear-gradient(135deg,rgba(79,70,229,0.06),#FFFFFF 55%);"
        else:
            bdr  = "border:1px solid rgba(99,102,241,0.35);border-bottom:none;background:linear-gradient(135deg,rgba(99,102,241,0.07),#0D0D12 55%);"
        line = '<div style="position:absolute;top:0;left:0;right:0;height:1px;background:linear-gradient(90deg,transparent,rgba(99,102,241,0.75),transparent);"></div>'
        rc   = "#4F46E5" if is_light else "#6366F1"
        nc   = "#4F46E5" if is_light else "#6366F1"
    else:
        bdr  = "border:1px solid rgba(0,0,0,0.08);border-bottom:none;background:#FFFFFF;" if is_light else "border:1px solid rgba(255,255,255,0.06);border-bottom:none;background:#0D0D12;"
        line = ""
        rc   = "#0F0F14" if is_light else "#F0F0F5"
        nc   = "#A1A1AA" if is_light else "#4B4B5E"

    label_c = "#52525B" if is_light else "#4B4B5E"
    h  = f'<div style="position:relative;{bdr}border-radius:14px 14px 0 0;overflow:hidden;">'
    h += line
    h += f'<div style="padding:20px 24px;display:flex;align-items:flex-start;gap:16px;">'
    h += f'<div style="font-family:JetBrains Mono,monospace;font-size:28px;font-weight:500;color:{nc};line-height:1;flex-shrink:0;min-width:32px;margin-top:4px;">{rank:02d}</div>'
    h += f'<div style="flex:1;min-width:0;">'
    h += f'<div style="font-size:18px;font-weight:600;color:{rc if top else ("var(--text-primary,#0F0F14)" if is_light else "var(--text-primary,#F0F0F5)")};letter-spacing:-0.02em;line-height:1.2;margin-bottom:8px;font-family:Inter,sans-serif;">{name}</div>'
    h += f'<div style="display:flex;gap:8px;flex-wrap:wrap;">{pill(kano, kc)} {pill("Ship " + qtr, qc)}</div>'
    h += '</div>'
    h += f'<div style="display:flex;align-items:center;gap:14px;flex-shrink:0;">{svg}'
    h += '<div style="text-align:right;">'
    h += f'<div style="font-size:10px;font-weight:500;letter-spacing:0.08em;text-transform:uppercase;color:{label_c};font-family:Inter,sans-serif;margin-bottom:2px;">RICE</div>'
    h += f'<div style="font-family:JetBrains Mono,monospace;font-size:24px;font-weight:500;color:{rc};">{rice}</div>'
    h += '</div></div></div></div>'
    return h

def card_detail(r):
    """Returns compact single-line HTML for the expanded detail panel."""
    rat  = html.escape(str(r.get("rationale", "")))
    risk = html.escape(str(r.get("risk", "")))
    rank = r.get("priority_rank", 1)
    top  = (rank == 1)
    if is_light:
        if top:
            bdr = "border:1px solid rgba(79,70,229,0.3);border-top:1px solid rgba(79,70,229,0.1);background:linear-gradient(135deg,rgba(79,70,229,0.04),#FFFFFF 55%);"
        else:
            bdr = "border:1px solid rgba(0,0,0,0.08);border-top:1px solid rgba(0,0,0,0.04);background:#FFFFFF;"
        label_c   = "#52525B"
        body_c    = "#52525B"
        rat_border = "rgba(79,70,229,0.35)"
        risk_border = "rgba(220,38,38,0.3)"
    else:
        if top:
            bdr = "border:1px solid rgba(99,102,241,0.35);border-top:1px solid rgba(99,102,241,0.15);background:linear-gradient(135deg,rgba(99,102,241,0.05),#0D0D12 55%);"
        else:
            bdr = "border:1px solid rgba(255,255,255,0.06);border-top:1px solid rgba(255,255,255,0.04);background:#0D0D12;"
        label_c   = "#4B4B5E"
        body_c    = "#8B8B9E"
        rat_border = "rgba(99,102,241,0.4)"
        risk_border = "rgba(239,68,68,0.3)"

    h  = f'<div style="{bdr}border-radius:0 0 14px 14px;padding:0 24px 20px;margin-bottom:12px;">'
    h += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;padding-top:16px;">'
    h += f'<div style="border-left:2px solid {rat_border};padding-left:12px;">'
    h += f'<div style="font-size:10px;font-weight:500;letter-spacing:0.08em;text-transform:uppercase;color:{label_c};font-family:Inter,sans-serif;margin-bottom:5px;">AI Rationale</div>'
    h += f'<div style="font-size:13px;line-height:20px;color:{body_c};font-style:italic;font-family:Inter,sans-serif;">{rat}</div>'
    h += '</div>'
    h += f'<div style="border-left:2px solid {risk_border};padding-left:12px;">'
    h += f'<div style="font-size:10px;font-weight:500;letter-spacing:0.08em;text-transform:uppercase;color:{label_c};font-family:Inter,sans-serif;margin-bottom:5px;">Risk</div>'
    h += f'<div style="font-size:13px;line-height:20px;color:{body_c};font-family:Inter,sans-serif;">{risk}</div>'
    h += '</div></div></div>'
    return h

def backlog_html():
    feats = st.session_state.features
    dot_bg = "rgba(0,0,0,0.06)" if is_light else "rgba(255,255,255,0.06)"
    empty_c = "#A1A1AA" if is_light else "#4B4B5E"
    if not feats:
        dots = "".join(f'<div style="width:3px;height:3px;border-radius:50%;background:{dot_bg};"></div>' for _ in range(25))
        return (f'<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;'
                f'min-height:340px;gap:20px;">'
                f'<div style="display:grid;grid-template-columns:repeat(5,3px);gap:12px;">{dots}</div>'
                f'<p style="color:{empty_c};font-size:13px;text-align:center;font-family:Inter,sans-serif;margin:0;">'
                f'Your features appear here<br>'
                f'<span style="font-size:11px;opacity:0.6;">Add a feature using the form</span>'
                f'</p></div>')
    sf = sorted(feats, key=rs, reverse=True)
    rows = ""
    rank_c = "#A1A1AA" if is_light else "#4B4B5E"
    name_c = "#0F0F14" if is_light else "#F0F0F5"
    goal_c = "#52525B" if is_light else "#4B4B5E"
    div_c  = "rgba(0,0,0,0.05)" if is_light else "rgba(255,255,255,0.04)"
    for i, f in enumerate(sf):
        r = rs(f)
        div = f"border-bottom:1px solid {div_c};" if i < len(sf)-1 else ""
        rows += (f'<div style="display:flex;align-items:center;gap:12px;padding:10px 0;{div}">'
                 f'<span style="font-family:\'JetBrains Mono\',monospace;color:{rank_c};font-size:11px;'
                 f'width:18px;flex-shrink:0;text-align:right;">{i+1:02d}</span>'
                 f'<div style="flex:1;min-width:0;">'
                 f'<div style="color:{name_c};font-size:14px;font-weight:500;font-family:Inter,sans-serif;'
                 f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{html.escape(f["name"])}</div>'
                 f'<div style="color:{goal_c};font-size:11px;font-family:Inter,sans-serif;margin-top:1px;">'
                 f'{html.escape(f.get("strategic_goal",""))}</div></div>'
                 f'<span style="font-family:\'JetBrains Mono\',monospace;color:var(--accent-indigo);font-size:12px;'
                 f'font-weight:500;flex-shrink:0;">{r}</span></div>')
    cnt = len(feats)
    lbl_c = "#A1A1AA" if is_light else "#4B4B5E"
    return (f'<div><div style="font-size:11px;font-weight:500;letter-spacing:0.08em;text-transform:uppercase;'
            f'color:{lbl_c};font-family:Inter,sans-serif;margin-bottom:14px;">Backlog '
            f'<span style="background:var(--accent-indigo-glow);color:var(--accent-indigo);border-radius:20px;'
            f'padding:2px 8px;margin-left:6px;font-family:\'JetBrains Mono\',monospace;font-size:11px;">{cnt}</span>'
            f'</div>{rows}</div>')

# ══════════════════════════════════════════════════════════════════════════════
# PDF GENERATOR
# ══════════════════════════════════════════════════════════════════════════════
def generate_pdf(features: list, results: list, product_context: str = "") -> bytes:
    from fpdf.enums import XPos, YPos
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # ── COVER HEADER ──────────────────────────────────────────────────────────
    pdf.set_fill_color(99, 102, 241)
    pdf.rect(0, 0, 210, 32, "F")

    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(14, 8)
    pdf.cell(0, 10, "AI Feature Prioritisation Report", new_x=XPos.RIGHT, new_y=YPos.TOP)

    date_str = datetime.now().strftime("%d %B %Y")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(200, 200, 240)
    pdf.set_xy(140, 12)
    pdf.cell(56, 6, date_str, align="R")

    pdf.set_xy(14, 22)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(200, 200, 240)
    pdf.cell(0, 6, f"{len(results)} features analysed · Groq Llama 3.3 70B · RICE + Kano")

    pdf.ln(20)

    # ── SUMMARY ROW ───────────────────────────────────────────────────────────
    if results:
        top_r = results[0]
        pdf.set_fill_color(245, 245, 250)
        pdf.set_draw_color(220, 220, 235)
        pdf.set_line_width(0.3)
        pdf.rect(14, pdf.get_y(), 182, 22, "FD")

        pdf.set_xy(18, pdf.get_y() + 4)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(99, 102, 241)
        pdf.cell(0, 5, "TOP PRIORITY", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.set_x(18)
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(15, 15, 20)
        pdf.cell(120, 6, top_r.get("feature_name", top_r.get("name", ""))[:40], new_x=XPos.RIGHT, new_y=YPos.TOP)

        rice_val = top_r.get("rice_score", 0)
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(99, 102, 241)
        pdf.cell(0, 6, f"RICE {rice_val}", align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.ln(14)

    # ── FEATURE CARDS ─────────────────────────────────────────────────────────
    for i, feature in enumerate(results):
        if pdf.get_y() > 240:
            pdf.add_page()

        rank     = feature.get("priority_rank", i + 1)
        fname    = feature.get("feature_name", feature.get("name", ""))[:40]
        kano     = feature.get("kano_category", "")
        rice_s   = feature.get("rice_score", 0)
        quarter  = feature.get("ship_quarter", "")
        rational = feature.get("rationale", "")
        risk_t   = feature.get("risk", "")

        # Match confidence from original features list
        conf_match = [f for f in features if f["name"] == feature.get("feature_name", "")]
        conf_val = conf_match[0]["confidence"] * 10 if conf_match else 70

        card_y = pdf.get_y()
        if rank == 1:
            pdf.set_fill_color(240, 240, 255)
            pdf.set_draw_color(99, 102, 241)
            pdf.set_line_width(0.5)
        else:
            pdf.set_fill_color(250, 250, 252)
            pdf.set_draw_color(220, 220, 228)
            pdf.set_line_width(0.3)
        pdf.rect(14, card_y, 182, 52, "FD")

        if rank == 1:
            pdf.set_fill_color(99, 102, 241)
            pdf.rect(14, card_y, 3, 52, "F")

        # Rank number
        pdf.set_xy(20, card_y + 5)
        pdf.set_font("Helvetica", "B", 22)
        pdf.set_text_color(180, 180, 200)
        pdf.cell(14, 12, f"0{rank}" if rank < 10 else str(rank), new_x=XPos.RIGHT, new_y=YPos.TOP)

        # Feature name
        pdf.set_xy(38, card_y + 5)
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(15, 15, 20)
        pdf.cell(100, 7, fname, new_x=XPos.RIGHT, new_y=YPos.TOP)

        # RICE score
        pdf.set_font("Helvetica", "B", 16)
        pdf.set_text_color(99, 102, 241)
        pdf.set_xy(152, card_y + 3)
        pdf.cell(40, 8, f"{rice_s}", align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_xy(152, card_y + 11)
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(160, 160, 180)
        pdf.cell(40, 4, "RICE SCORE", align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Kano badge
        kano_map = {"Must-have": (139,92,246), "Performance": (59,130,246), "Delight": (236,72,153), "Indifferent": (107,114,128)}
        kc_rgb = kano_map.get(kano, (107, 114, 128))
        pdf.set_fill_color(*kc_rgb)
        pdf.set_text_color(255, 255, 255)
        pdf.set_xy(38, card_y + 14)
        pdf.set_font("Helvetica", "B", 7)
        pdf.cell(len(kano) * 2.5 + 4, 5, f" {kano} ", fill=True, new_x=XPos.RIGHT, new_y=YPos.TOP)

        # Ship quarter badge
        pdf.set_fill_color(34, 197, 94)
        pdf.set_xy(38 + len(kano) * 2.5 + 6, card_y + 14)
        pdf.cell(16, 5, f" {quarter} ", fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Confidence bar
        pdf.set_xy(38, card_y + 22)
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(100, 100, 120)
        pdf.cell(22, 4, f"Confidence: {conf_val}%", new_x=XPos.RIGHT, new_y=YPos.TOP)
        bar_x, bar_y = 64, card_y + 23
        pdf.set_fill_color(220, 220, 235)
        pdf.rect(bar_x, bar_y, 60, 3, "F")
        bar_fill = min(60, int(60 * conf_val / 100))
        fill_col = (34,197,94) if conf_val >= 70 else (245,158,11) if conf_val >= 40 else (239,68,68)
        pdf.set_fill_color(*fill_col)
        pdf.rect(bar_x, bar_y, bar_fill, 3, "F")

        # Rationale
        pdf.set_xy(20, card_y + 29)
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(80, 80, 100)
        rat_text = rational[:160] + "..." if len(rational) > 160 else rational
        pdf.multi_cell(170, 4, rat_text)

        # Risk
        if risk_t:
            pdf.set_x(20)
            pdf.set_font("Helvetica", "B", 7)
            pdf.set_text_color(239, 68, 68)
            pdf.cell(12, 4, "RISK: ", new_x=XPos.RIGHT, new_y=YPos.TOP)
            pdf.set_font("Helvetica", "", 7)
            pdf.set_text_color(120, 60, 60)
            risk_short = risk_t[:120] + "..." if len(risk_t) > 120 else risk_t
            pdf.cell(0, 4, risk_short, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.ln(8)

    # ── FULL SUMMARY TABLE ────────────────────────────────────────────────────
    if pdf.get_y() > 210:
        pdf.add_page()

    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(15, 15, 20)
    pdf.set_x(14)
    pdf.cell(0, 7, "Full Prioritisation Summary", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)

    headers = ["#", "Feature", "Kano", "Quarter", "RICE", "Confidence"]
    widths  = [10, 70, 28, 20, 22, 28]

    pdf.set_fill_color(99, 102, 241)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_x(14)
    for h_txt, w in zip(headers, widths):
        pdf.cell(w, 7, h_txt, border=0, fill=True, align="C")
    pdf.ln()

    for i, feature in enumerate(results):
        pdf.set_x(14)
        pdf.set_fill_color(248, 248, 252) if i % 2 == 0 else pdf.set_fill_color(255, 255, 255)
        pdf.set_text_color(40, 40, 60)
        pdf.set_font("Helvetica", "B" if i == 0 else "", 8)

        conf_m = [f for f in features if f["name"] == feature.get("feature_name", "")]
        conf_pct = f"{conf_m[0]['confidence']*10}%" if conf_m else "—"

        row_data = [
            str(feature.get("priority_rank", i+1)),
            feature.get("feature_name", feature.get("name", ""))[:30],
            feature.get("kano_category", ""),
            feature.get("ship_quarter", ""),
            str(feature.get("rice_score", "")),
            conf_pct,
        ]
        for d, w in zip(row_data, widths):
            pdf.cell(w, 6, d, border=0, fill=True, align="C")
        pdf.ln()

    pdf.ln(8)

    # ── FOOTER ON EVERY PAGE ──────────────────────────────────────────────────
    total_pages = pdf.page
    for p in range(1, total_pages + 1):
        pdf.page = p
        pdf.set_xy(14, 284)
        pdf.set_draw_color(200, 200, 215)
        pdf.set_line_width(0.3)
        pdf.line(14, 284, 196, 284)
        pdf.set_xy(14, 287)
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(150, 150, 170)
        pdf.cell(80, 4, "~ made by Sankalp Dusane", new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.cell(62, 4, "AI Feature Prioritisation Engine · Groq · Streamlit", align="C", new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.cell(0, 4, f"Page {p} of {total_pages}", align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    return bytes(pdf.output())

# ══════════════════════════════════════════════════════════════════════════════
# CSS — DUAL THEME VARIABLE SYSTEM
# ══════════════════════════════════════════════════════════════════════════════
_theme_vars = """
:root {
  --bg-void: #F4F4F6;
  --bg-card: #FFFFFF;
  --bg-card-hover: #FAFAFA;
  --bg-elevated: #F0F0F5;
  --bg-input: #F8F8FB;
  --bg-input-focus: #FFFFFF;
  --border-subtle: rgba(0,0,0,0.06);
  --border-medium: rgba(0,0,0,0.12);
  --border-accent: rgba(79,70,229,0.4);
  --text-primary: #0F0F14;
  --text-secondary: #52525B;
  --text-tertiary: #A1A1AA;
  --accent-indigo: #4F46E5;
  --accent-indigo-glow: rgba(79,70,229,0.08);
  --shadow-card: 0 1px 3px rgba(0,0,0,0.07), 0 4px 12px rgba(0,0,0,0.04);
  --shadow-card-hover: 0 4px 16px rgba(0,0,0,0.10), 0 1px 4px rgba(0,0,0,0.06);
}
""" if is_light else """
:root {
  --bg-void: #060608;
  --bg-card: #0D0D12;
  --bg-card-hover: #12121A;
  --bg-elevated: #16161F;
  --bg-input: rgba(255,255,255,0.03);
  --bg-input-focus: rgba(255,255,255,0.05);
  --border-subtle: rgba(255,255,255,0.06);
  --border-medium: rgba(255,255,255,0.12);
  --border-accent: rgba(99,102,241,0.5);
  --text-primary: #F0F0F5;
  --text-secondary: #8B8B9E;
  --text-tertiary: #4B4B5E;
  --accent-indigo: #6366F1;
  --accent-indigo-glow: rgba(99,102,241,0.15);
  --shadow-card: 0 1px 2px rgba(0,0,0,0.4), 0 4px 12px rgba(0,0,0,0.3);
  --shadow-card-hover: 0 0 40px rgba(99,102,241,0.08), 0 4px 24px rgba(0,0,0,0.5);
}
"""

st.markdown(f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Theme Variable Definitions ── */
{_theme_vars}
</style>""", unsafe_allow_html=True)



st.markdown(f"""<style>
/* ── 300ms smooth theme transition on all elements ── */
*, *::before, *::after {{
  transition:
    background-color 0.3s ease,
    color 0.3s ease,
    border-color 0.3s ease,
    box-shadow 0.3s ease !important;
}}
/* Interactions stay instant (transform only, not color) */
button, .stButton > button, input, [data-interactive="true"] {{
  transition:
    background-color 0.3s ease,
    color 0.3s ease,
    border-color 0.3s ease,
    box-shadow 0.3s ease,
    transform 0.15s cubic-bezier(0.16,1,0.3,1) !important;
}}

/* ── Chrome (hide Streamlit chrome) ── */
header[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stDecoration"],
[data-testid="stStatusWidget"],[data-testid="stSidebar"],[data-testid="collapsedControl"],
footer,#MainMenu {{ display:none !important; }}

/* ── Base ── */
html,body,.stApp {{ background:var(--bg-void,#060608) !important; color:var(--text-primary,#F0F0F5) !important; font-family:'Inter',-apple-system,sans-serif !important; -webkit-font-smoothing:antialiased !important; }}
*{{box-sizing:border-box !important;}}
a{{color:inherit !important;text-decoration:none !important;}}
p,span,div,label,li{{color:inherit !important;}}
/* Ensure Streamlit's own text elements pick up theme color */
.stApp p, .stApp span, .stApp label {{ color:var(--text-primary,#F0F0F5) !important; }}
.main .block-container{{padding:0 !important;max-width:100% !important;}}
::-webkit-scrollbar{{width:4px;}} ::-webkit-scrollbar-track{{background:transparent;}} ::-webkit-scrollbar-thumb{{background:var(--accent-indigo);border-radius:2px;}}
[data-testid="InputInstructions"],[class*="InputInstructions"]{{display:none !important;}}

/* ── Inputs ── */
[data-testid="stTextInput"] > div > div, [data-testid="stTextArea"] > div > div {{
    background: transparent !important;
}}
[data-testid="stTextInput"] input,[data-testid="stTextArea"] textarea {{
    background:var(--bg-input) !important; border:1px solid var(--border-medium) !important;
    border-radius:8px !important; padding:10px 14px !important; color:var(--text-primary) !important;
    font-family:'Inter',sans-serif !important; font-size:14px !important;
    caret-color:var(--accent-indigo) !important;
}}
[data-testid="stTextInput"] input:focus,[data-testid="stTextArea"] textarea:focus {{
    border-color:var(--accent-indigo) !important; box-shadow:0 0 0 3px var(--accent-indigo-glow) !important; outline:none !important;
}}
[data-testid="stTextInput"] input::placeholder,[data-testid="stTextArea"] textarea::placeholder {{ color:var(--text-tertiary) !important; font-size:13px !important; }}
[data-testid="stTextInput"] label,[data-testid="stTextArea"] label{{display:none !important;}}

/* ── Sliders ── */
.stSlider label {{
    color:var(--text-secondary) !important; font-family:'Inter',sans-serif !important;
    font-size:12px !important; font-weight:500 !important;
    letter-spacing:0.06em !important; text-transform:uppercase !important;
}}
[data-testid="stTickBar"] {{ display:none !important; }}
[data-testid="stSlider"] p {{ display:none !important; }}
[data-testid="stSlider"] > div > div > div {{
    background:var(--border-medium) !important; height:4px !important;
}}
[data-testid="stSlider"] > div > div > div > div {{ background:var(--accent-indigo) !important; }}
[data-testid="stSlider"] > div > div > div > div > div {{
    background:var(--accent-indigo) !important; width:18px !important; height:18px !important;
    border-radius:50% !important; border:2px solid var(--bg-void) !important;
    box-shadow:0 0 0 3px var(--accent-indigo-glow) !important;
}}
[data-testid="stSliderThumbValue"] {{
    background:var(--accent-indigo) !important; color:white !important;
    font-family:'JetBrains Mono',monospace !important; font-size:11px !important;
    font-weight:500 !important; padding:2px 6px !important; border-radius:4px !important;
}}

/* ── Radio pills ── */
[data-testid="stRadio"] label:not([data-testid="stRadio"] > div > label){{display:none !important;}}
[data-testid="stRadio"] > div {{ display:flex !important; flex-direction:row !important; flex-wrap:wrap !important; gap:6px !important; margin-top:2px !important; }}
[data-testid="stRadio"] > div > label {{
    display:flex !important; align-items:center !important;
    background:var(--bg-elevated) !important; border:1px solid var(--border-medium) !important;
    border-radius:20px !important; padding:5px 14px !important; font-size:12px !important;
    font-weight:500 !important; color:var(--text-secondary) !important; cursor:pointer !important;
    font-family:'Inter',sans-serif !important;
}}
[data-testid="stRadio"] > div > label:hover {{ border-color:var(--border-accent) !important; color:var(--text-primary) !important; background:var(--bg-card-hover) !important; }}
[data-testid="stRadio"] > div > label > div:first-child{{display:none !important;}}
[data-testid="stRadio"] > div > label > div:last-child p{{font-size:12px !important;font-weight:500 !important;line-height:1 !important;margin:0 !important;color:inherit !important;}}
[data-testid="stRadio"] > div > label:has(input:checked) {{ background:var(--accent-indigo-glow) !important; border-color:var(--accent-indigo) !important; color:var(--accent-indigo) !important; }}

/* ── Form ── */
[data-testid="stForm"]{{background:transparent !important;border:none !important;padding:0 !important;}}
[data-testid="stFormSubmitButton"] > button {{
    background:var(--accent-indigo) !important; color:white !important; border:none !important;
    border-radius:10px !important; height:44px !important; width:100% !important;
    font-size:14px !important; font-weight:500 !important; letter-spacing:0.01em !important;
    font-family:'Inter',sans-serif !important; cursor:pointer !important;
}}
[data-testid="stFormSubmitButton"] > button:hover {{ background:#5254D4 !important; box-shadow:0 0 30px rgba(99,102,241,0.25),0 0 60px rgba(99,102,241,0.12) !important; transform:translateY(-1px) !important; }}

/* ── Primary button ── */
.stButton > button[kind="primary"] {{
    background:linear-gradient(135deg,#6366F1,#8B5CF6) !important; color:white !important;
    border:none !important; border-radius:12px !important; height:52px !important;
    font-size:15px !important; font-weight:600 !important; letter-spacing:-0.01em !important;
    font-family:'Inter',sans-serif !important; cursor:pointer !important; width:100% !important;
}}
.stButton > button[kind="primary"]:hover {{ box-shadow:0 0 40px rgba(99,102,241,0.4) !important; transform:translateY(-2px) !important; }}
.stButton > button[kind="primary"]:active {{ transform:scale(0.98) translateY(0) !important; }}

/* ── Ghost buttons ── */
.stButton > button:not([kind="primary"]) {{
    background:transparent !important; color:var(--text-secondary) !important;
    border:1px solid var(--border-medium) !important; border-radius:8px !important;
    font-family:'Inter',sans-serif !important; font-size:13px !important; cursor:pointer !important;
    padding:8px 16px !important;
}}
.stButton > button:not([kind="primary"]):hover {{ border-color:var(--border-accent) !important; color:var(--text-primary) !important; background:var(--bg-elevated) !important; }}

.stButton > button[data-testid*="expand_"] {{
    border-radius: 0 0 12px 12px !important;
    border-top: none !important;
    background: var(--bg-elevated) !important;
    color: var(--text-tertiary) !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    letter-spacing: 0.04em !important;
    padding: 7px 20px !important;
    margin: 0 !important;
    border: 1px solid var(--border-subtle) !important;
}}
.stButton > button[data-testid*="expand_"]:hover {{
    color: var(--text-secondary) !important;
    background: var(--bg-card-hover) !important;
}}
""" + f"""

/* ── Download ── */
.stDownloadButton > button {{ background:transparent !important; color:var(--text-secondary) !important; border:1px solid var(--border-medium) !important; border-radius:8px !important; font-family:'Inter',sans-serif !important; font-size:13px !important; padding:8px 16px !important; }}
.stDownloadButton > button:hover {{ border-color:var(--accent-indigo) !important; color:var(--accent-indigo) !important; }}

/* ── Column layout ── */
[data-testid="stHorizontalBlock"]{{padding:0 32px !important;gap:16px !important;align-items:stretch !important;}}
[data-testid="stColumn"]{{padding:0 !important;}}

/* ── Bento grid columns → cards ── */
[data-testid="stColumn"] > div {{
    background:var(--bg-card,#0D0D12); border:1px solid var(--border-subtle,rgba(255,255,255,0.06));
    border-radius:16px; padding:24px; height:100%;
}}
[data-testid="stColumn"] > div:hover {{ border-color:var(--border-medium,rgba(255,255,255,0.10)); box-shadow:var(--shadow-card-hover); }}

/* ── Reset nested columns ── */
[data-testid="stColumn"] [data-testid="stColumn"] > div {{
    background:transparent !important; border:none !important; border-radius:0 !important;
    padding:4px 0 !important; height:auto !important; box-shadow:none !important;
}}
[data-testid="stColumn"] [data-testid="stColumn"] > div:hover {{ border-color:transparent !important; box-shadow:none !important; }}

/* ── Reset subsequent horizontal blocks ── */
[data-testid="stHorizontalBlock"] ~ [data-testid="stHorizontalBlock"] [data-testid="stColumn"] > div {{
    background:transparent !important; border:none !important; border-radius:0 !important;
    padding:0 !important; height:auto !important; box-shadow:none !important;
}}
[data-testid="stHorizontalBlock"] ~ [data-testid="stHorizontalBlock"] [data-testid="stColumn"] > div:hover {{ border-color:transparent !important; box-shadow:none !important; }}

/* ── Chart card ── */
[data-testid="stPlotlyChart"] {{
    background:var(--bg-card,#0D0D12) !important; border:1px solid var(--border-subtle,rgba(255,255,255,0.06)) !important;
    border-radius:16px !important; overflow:hidden !important; padding:16px 0 0 0 !important;
}}

/* ── Hide unused ── */
[data-testid="stAlert"],[data-testid="stMetric"],[data-testid="stToggle"],[data-testid="stSpinner"]{{display:none !important;}}

/* ── Details/summary ── */
details{{outline:none;}}
details>summary::-webkit-details-marker,details>summary::marker{{display:none;}}

/* ── Kill Streamlit default top padding ── */
[data-testid="stMainBlockContainer"] {{ padding-top: 0 !important; padding-bottom: 0 !important; }}
section[data-testid="stMain"] > div:first-child {{ padding-top: 0 !important; }}

/* ── PDF button animation ── */
@keyframes pdf-throb {{
  0%,100% {{ box-shadow: 0 0 0 0 rgba(99,102,241,0.0); }}
  50% {{ box-shadow: 0 0 0 8px rgba(99,102,241,0.15); }}
}}
.pdf-btn-wrap .stDownloadButton > button {{
  background: linear-gradient(135deg,#6366F1,#8B5CF6) !important;
  color: white !important;
  border: none !important;
  font-family: Inter,sans-serif !important;
  font-size: 13px !important;
  font-weight: 500 !important;
  border-radius: 8px !important;
  width: 100% !important;
  animation: pdf-throb 2.5s ease-in-out infinite !important;
}}
.pdf-btn-wrap .stDownloadButton > button:hover {{
  background: linear-gradient(135deg,#5254d4,#7c3aed) !important;
  box-shadow: 0 4px 20px rgba(99,102,241,0.40) !important;
  transform: translateY(-1px) !important;
  animation: none !important;
}}

/* ── Animations ── */
@keyframes pulse-indigo{{0%,100%{{box-shadow:0 0 0 0 rgba(99,102,241,0.7);opacity:1;}}50%{{box-shadow:0 0 0 6px rgba(99,102,241,0);opacity:.75;}}}}
@keyframes pulse-red{{0%,100%{{box-shadow:0 0 0 0 rgba(239,68,68,0.7);}}50%{{box-shadow:0 0 0 5px rgba(239,68,68,0);}}}}
@keyframes gradient-shift{{0%{{background-position:0% 50%;}}50%{{background-position:100% 50%;}}100%{{background-position:0% 50%;}}}}
@keyframes card-enter{{
  from{{opacity:0;transform:translateY(28px) scale(0.97);filter:blur(4px);}}
  to{{opacity:1;transform:translateY(0) scale(1);filter:blur(0);}}
}}
@keyframes section-enter{{
  from{{opacity:0;transform:translateY(16px);}}
  to{{opacity:1;transform:translateY(0);}}
}}
@keyframes ring-fill{{to{{stroke-dashoffset:var(--ring-target);}}}}
@keyframes dot-a{{0%,80%,100%{{transform:scale(0.6);opacity:.3;}}20%{{transform:scale(1);opacity:1;}}}}
@keyframes dot-b{{0%,80%,100%{{transform:scale(0.6);opacity:.3;}}40%{{transform:scale(1);opacity:1;}}}}
@keyframes dot-c{{0%,80%,100%{{transform:scale(0.6);opacity:.3;}}60%{{transform:scale(1);opacity:1;}}}}
@keyframes loading-pulse{{0%,100%{{opacity:.4;}}50%{{opacity:1;}}}}
@keyframes progress-fill{{0%{{width:0%;}}85%{{width:80%;}}100%{{width:85%;}}}}

.precision-grad{{background:linear-gradient(90deg,#6366F1,#8B5CF6,#EC4899,#6366F1);background-size:300% 100%;animation:gradient-shift 6s ease infinite;-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}}
</style>""", unsafe_allow_html=True)

# ── Python-side theme variables ──────────────────────────────────────────────
_hdr_bg        = "rgba(255,255,255,0.92)" if is_light else "rgba(6,6,8,0.92)"
_hdr_border    = "rgba(0,0,0,0.08)"       if is_light else "rgba(255,255,255,0.06)"
_txt_secondary = "#52525B"                if is_light else "#8B8B9E"
_txt_tertiary  = "#A1A1AA"                if is_light else "#4B4B5E"
_badge_bg      = "#F0F0F5"                if is_light else "#16161F"
_badge_border  = "rgba(0,0,0,0.07)"       if is_light else "rgba(255,255,255,0.06)"
_hero_title_c  = "#0F0F14"                if is_light else "#F0F0F5"
_hero_sub_c    = "#52525B"                if is_light else "#8B8B9E"

# ══════════════════════════════════════════════════════════════════════════════
# THEME TOGGLE — CSS :has() approach
# ══════════════════════════════════════════════════════════════════════════════
current_theme = st.session_state.theme
icon          = "☀️" if current_theme == "dark" else "🌙"
toggle_label  = "Light" if current_theme == "dark" else "Dark"

st.markdown('<div class="theme-toggle-marker"></div>', unsafe_allow_html=True)
st.markdown('''<style>
/* Hide the marker container itself */
.element-container:has(.theme-toggle-marker) {
    display: none !important;
}
/* Position the very next element-container (which will be the button) */
.element-container:has(.theme-toggle-marker) + .element-container {
    position: fixed !important;
    top: 14px !important;
    right: 20px !important;
    z-index: 9999 !important;
    width: auto !important;
    height: auto !important;
}
/* Style the button inside that specific container */
.element-container:has(.theme-toggle-marker) + .element-container .stButton > button {
    background: var(--bg-card, #0D0D12) !important;
    border: 1px solid var(--border-medium, rgba(255,255,255,0.12)) !important;
    border-radius: 100px !important;
    padding: 4px 14px !important;
    color: var(--text-secondary, #8B8B9E) !important;
    backdrop-filter: blur(12px) !important;
    -webkit-backdrop-filter: blur(12px) !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    height: 36px !important;
    min-height: 36px !important;
}
.element-container:has(.theme-toggle-marker) + .element-container .stButton > button:hover {
    border-color: var(--accent-indigo, #6366F1) !important;
    color: var(--text-primary, #F0F0F5) !important;
}
</style>''', unsafe_allow_html=True)

if st.button(f"{icon} {toggle_label}", key="theme_btn"):
    st.session_state.theme = "light" if current_theme == "dark" else "dark"
    st.session_state.expanded_cards = set()
    st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# HERO HEADER BAR
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<div style="border-bottom:1px solid {_hdr_border};padding:20px 32px;
            display:flex;align-items:center;justify-content:space-between;
            background:{_hdr_bg};backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);
            position:sticky;top:0;z-index:100;">
  <div style="display:flex;align-items:center;gap:10px;">
    <div style="width:6px;height:6px;border-radius:50%;background:var(--accent-indigo);
                animation:pulse-indigo 2s ease-in-out infinite;"></div>
    <span style="color:{_txt_secondary};font-size:13px;font-weight:400;font-family:'Inter',sans-serif;">
      AI Feature Prioritisation Engine
    </span>
  </div>
  <div style="background:{_badge_bg};border:1px solid {_badge_border};border-radius:6px;padding:4px 12px;">
    <span style="color:{_txt_tertiary};font-size:11px;font-family:'JetBrains Mono',monospace;">Powered by Llama 3.3 70B</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# HERO SECTION
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<div style="text-align:center;padding:64px 32px 48px;">
  <h1 style="font-size:48px;line-height:52px;font-weight:600;letter-spacing:-0.04em;
             color:{_hero_title_c};margin:0 0 20px 0;font-family:'Inter',sans-serif;">
    Prioritise with<br><span class="precision-grad">precision.</span>
  </h1>
  <p style="color:{_hero_sub_c};font-size:15px;line-height:24px;max-width:480px;
            margin:0 auto;font-family:'Inter',sans-serif;">
    Enter your product backlog. Get RICE scores, Kano classification, and AI reasoning —
    with a skeptical stakeholder who argues back.
  </p>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# BENTO GRID
# ══════════════════════════════════════════════════════════════════════════════
features = st.session_state.features
left_col, right_col = st.columns([6, 4])

_form_section_c = "#52525B" if is_light else "#8B8B9E"
_form_title_c   = "#0F0F14" if is_light else "#F0F0F5"

with left_col:
    st.markdown(f'<div style="margin-bottom:16px;">'
                f'<div style="font-size:11px;font-weight:500;letter-spacing:0.08em;text-transform:uppercase;'
                f'color:{_form_section_c};font-family:Inter,sans-serif;margin-bottom:6px;">Add Feature</div>'
                f'<div style="font-size:22px;font-weight:600;color:{_form_title_c};'
                f'font-family:Inter,sans-serif;letter-spacing:-0.02em;">Build your backlog</div>'
                f'</div>', unsafe_allow_html=True)

    with st.form("feature_form", clear_on_submit=True):
        name = st.text_input("Feature name", placeholder="Feature name (e.g. 'AI size recommendation')", label_visibility="collapsed")
        desc = st.text_area("Description", placeholder="User pain or opportunity — include data if you have it", height=80, label_visibility="collapsed")

        goal_options = ["Retention", "Acquisition", "Revenue", "Efficiency", "Delight"]
        st.markdown(f'<div style="margin:10px 0 4px;font-size:11px;font-weight:500;letter-spacing:0.08em;'
                    f'text-transform:uppercase;color:{_form_section_c};font-family:Inter,sans-serif;">Strategic Goal</div>',
                    unsafe_allow_html=True)
        goal = st.radio("Strategic Goal", goal_options, horizontal=True, label_visibility="collapsed")

        st.markdown(f'<div style="margin:14px 0 8px;">'
                    f'<span style="color:{_form_section_c};font-size:11px;font-weight:500;letter-spacing:0.08em;'
                    f'text-transform:uppercase;font-family:\'Inter\',sans-serif;">RICE Dimensions</span>'
                    f'</div>', unsafe_allow_html=True)

        sc1, sc2 = st.columns(2)
        with sc1:
            st.markdown(f'<div style="display:flex;justify-content:space-between;align-items:center;'
                        f'margin-bottom:4px;margin-top:12px;">'
                        f'<span style="font-family:\'Inter\',sans-serif;font-size:11px;font-weight:500;'
                        f'color:{_form_section_c};letter-spacing:0.06em;text-transform:uppercase;">Reach</span>'
                        f'<span style="font-family:\'JetBrains Mono\',monospace;font-size:13px;font-weight:500;'
                        f'color:var(--accent-indigo);background:rgba(99,102,241,0.1);padding:2px 8px;border-radius:6px;">5</span>'
                        f'</div>', unsafe_allow_html=True)
            reach = st.slider("Reach", 1, 10, 5, label_visibility="collapsed")
            st.markdown(f'<div style="display:flex;justify-content:space-between;align-items:center;'
                        f'margin-bottom:4px;margin-top:12px;">'
                        f'<span style="font-family:\'Inter\',sans-serif;font-size:11px;font-weight:500;'
                        f'color:{_form_section_c};letter-spacing:0.06em;text-transform:uppercase;">Impact</span>'
                        f'<span style="font-family:\'JetBrains Mono\',monospace;font-size:13px;font-weight:500;'
                        f'color:var(--accent-indigo);background:rgba(99,102,241,0.1);padding:2px 8px;border-radius:6px;">5</span>'
                        f'</div>', unsafe_allow_html=True)
            impact = st.slider("Impact", 1, 10, 5, label_visibility="collapsed")
        with sc2:
            st.markdown(f'<div style="display:flex;justify-content:space-between;align-items:center;'
                        f'margin-bottom:4px;margin-top:12px;">'
                        f'<span style="font-family:\'Inter\',sans-serif;font-size:11px;font-weight:500;'
                        f'color:{_form_section_c};letter-spacing:0.06em;text-transform:uppercase;">Confidence</span>'
                        f'<span style="font-family:\'JetBrains Mono\',monospace;font-size:13px;font-weight:500;'
                        f'color:var(--accent-indigo);background:rgba(99,102,241,0.1);padding:2px 8px;border-radius:6px;">7</span>'
                        f'</div>', unsafe_allow_html=True)
            confidence = st.slider("Confidence", 1, 10, 7, label_visibility="collapsed")
            st.markdown(f'<div style="display:flex;justify-content:space-between;align-items:center;'
                        f'margin-bottom:4px;margin-top:12px;">'
                        f'<span style="font-family:\'Inter\',sans-serif;font-size:11px;font-weight:500;'
                        f'color:{_form_section_c};letter-spacing:0.06em;text-transform:uppercase;">Effort</span>'
                        f'<span style="font-family:\'JetBrains Mono\',monospace;font-size:13px;font-weight:500;'
                        f'color:var(--accent-indigo);background:rgba(99,102,241,0.1);padding:2px 8px;border-radius:6px;">5</span>'
                        f'</div>', unsafe_allow_html=True)
            effort = st.slider("Effort", 1, 10, 5, label_visibility="collapsed")

        prev = round(reach * impact * confidence / effort, 1)
        _preview_bg     = "rgba(79,70,229,0.05)"  if is_light else "rgba(99,102,241,0.06)"
        _preview_border = "rgba(79,70,229,0.15)"  if is_light else "rgba(99,102,241,0.18)"
        _preview_lbl_c  = "#A1A1AA" if is_light else "#4B4B5E"
        _preview_sub_c  = "#52525B" if is_light else "#6B6B7E"
        st.markdown(f'<div style="background:{_preview_bg};border:1px solid {_preview_border};'
                    f'border-radius:8px;padding:12px 16px;display:flex;align-items:center;'
                    f'justify-content:space-between;margin:12px 0 14px;">'
                    f'<div>'
                    f'<div style="color:{_preview_lbl_c};font-size:10px;font-weight:500;letter-spacing:0.08em;'
                    f'text-transform:uppercase;font-family:\'Inter\',sans-serif;">RICE Preview</div>'
                    f'<div style="color:{_preview_sub_c};font-size:11px;font-family:\'Inter\',sans-serif;margin-top:2px;">'
                    f'R × I × C ÷ Effort</div>'
                    f'</div>'
                    f'<div style="color:var(--accent-indigo);font-size:28px;font-family:\'JetBrains Mono\',monospace;'
                    f'font-weight:500;">{prev}</div>'
                    f'</div>', unsafe_allow_html=True)

        submitted = st.form_submit_button("＋  Add Feature", use_container_width=True)
        if submitted and name.strip():
            st.session_state.features.append({
                "name": name.strip(), "description": desc.strip(),
                "strategic_goal": goal, "reach": reach,
                "impact": impact, "confidence": confidence, "effort": effort,
            })
            st.session_state.results = None
            st.rerun()

with right_col:
    st.markdown(backlog_html(), unsafe_allow_html=True)

    if not features:
        if st.button("⚡  Load example backlog", key="load_example"):
            st.session_state.features = list(EXAMPLE_FEATURES)
            st.rerun()
    else:
        st.markdown(f'<div style="margin-top:16px;padding-top:14px;border-top:1px solid {_hdr_border};"></div>',
                    unsafe_allow_html=True)
        if st.button("Clear backlog", key="clear_btn"):
            st.session_state.features = []
            st.session_state.results  = None
            st.session_state.error    = None
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# ANALYSE BUTTON
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div style="height:24px;"></div>', unsafe_allow_html=True)
features = st.session_state.features   # re-read after form submit

if len(features) >= 2:
    (btn_col,) = st.columns([1])
    with btn_col:
        analyse = st.button("⚡  Prioritise with AI", type="primary",
                            use_container_width=True, key="analyse_btn")

    st.markdown(f'<div style="text-align:center;padding:10px 0 4px;">'
                f'<span style="color:{_txt_tertiary};font-size:11px;font-family:\'JetBrains Mono\',monospace;">'
                f'Groq 70B · Rate limited</span></div>', unsafe_allow_html=True)

    if analyse:
        slot = st.empty()
        _loading_bg     = "#FFFFFF" if is_light else "#0D0D12"
        _loading_border = "rgba(79,70,229,0.2)" if is_light else "rgba(99,102,241,0.2)"
        _loading_txt_c  = "#52525B" if is_light else "#8B8B9E"
        slot.markdown(f'<div style="background:{_loading_bg};border:1px solid {_loading_border};'
                      f'border-radius:16px;padding:40px;text-align:center;overflow:hidden;'
                      f'position:relative;margin:16px 32px;">'
                      f'<div style="display:flex;justify-content:center;gap:8px;margin-bottom:18px;">'
                      f'<div style="width:8px;height:8px;border-radius:50%;background:var(--accent-indigo);animation:dot-a 1.4s ease-in-out infinite;"></div>'
                      f'<div style="width:8px;height:8px;border-radius:50%;background:var(--accent-indigo);animation:dot-b 1.4s ease-in-out infinite;"></div>'
                      f'<div style="width:8px;height:8px;border-radius:50%;background:var(--accent-indigo);animation:dot-c 1.4s ease-in-out infinite;"></div>'
                      f'</div>'
                      f'<p style="color:{_loading_txt_c};font-size:13px;font-family:\'Inter\',sans-serif;margin:0;'
                      f'animation:loading-pulse 2s ease-in-out infinite;">Generating RICE scores and Kano classification…</p>'
                      f'<div style="position:absolute;bottom:0;left:0;height:2px;background:var(--accent-indigo);'
                      f'width:0;border-radius:0 0 16px 16px;animation:progress-fill 8s ease-out forwards;"></div>'
                      f'</div>', unsafe_allow_html=True)

        try:
            st.session_state.results = prioritise_features(st.session_state.features)
            st.session_state.error   = None
            st.session_state.scroll_to_results = True
        except Exception as exc:
            st.session_state.error   = str(exc)
            st.session_state.results = None

        slot.empty()
        st.rerun()

elif features:
    _info_bg     = "rgba(0,0,0,0.03)" if is_light else "rgba(255,255,255,0.02)"
    _info_border = "rgba(0,0,0,0.08)" if is_light else "rgba(255,255,255,0.06)"
    st.markdown(f'<div style="margin:0 32px;padding:14px 18px;border:1px solid {_info_border};'
                f'background:{_info_bg};border-radius:10px;">'
                f'<span style="color:{_txt_tertiary};font-size:13px;font-family:\'Inter\',sans-serif;">'
                f'Add at least 2 features to enable AI prioritisation.</span>'
                f'</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# ERROR STATE
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.error:
    err_text = html.escape(str(st.session_state.error))
    e_h  = '<div style="background:rgba(239,68,68,0.06);border:1px solid rgba(239,68,68,0.2);border-radius:12px;padding:16px 20px;margin:16px 32px 0;">'
    e_h += '<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">'
    e_h += '<div style="width:6px;height:6px;border-radius:50%;background:#EF4444;animation:pulse-red 2s ease-in-out infinite;"></div>'
    e_h += '<span style="color:rgba(239,68,68,0.8);font-size:11px;font-weight:500;letter-spacing:0.08em;text-transform:uppercase;font-family:Inter,sans-serif;">Error</span>'
    e_h += '</div>'
    e_h += f'<p style="color:{_txt_secondary};font-size:14px;font-family:Inter,sans-serif;margin:0 0 6px;">{err_text}</p>'
    e_h += '</div>'
    st.markdown(e_h, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# RESULTS
# ══════════════════════════════════════════════════════════════════════════════
results = st.session_state.results
if results:
    # ── Auto-scroll anchor ────────────────────────────────────────────────
    st.markdown('<div id="results-top" style="height:40px;"></div>', unsafe_allow_html=True)
    if st.session_state.get('scroll_to_results'):
        st.session_state.scroll_to_results = False
        components.html("""
<script>
setTimeout(function() {
  var el = window.parent.document.getElementById('results-top');
  if (el) el.scrollIntoView({behavior: 'smooth', block: 'start'});
}, 250);
</script>""", height=0)

    _section_lbl_c = "#A1A1AA" if is_light else "#4B4B5E"
    _section_badge_bg = "#F0F0F5" if is_light else "#16161F"
    _section_title_c = "#0F0F14" if is_light else "#F0F0F5"

    # Section header
    h_bar  = f'<div style="display:flex;align-items:center;justify-content:space-between;padding:0 32px;margin-bottom:20px;">'
    h_bar += f'<div style="display:flex;align-items:center;gap:12px;">'
    h_bar += f'<h2 style="font-size:24px;font-weight:600;letter-spacing:-0.025em;color:{_section_title_c};margin:0;font-family:\'Inter\',sans-serif;">Prioritised Backlog</h2>'
    h_bar += f'<span style="background:{_section_badge_bg};border:1px solid {_hdr_border};border-radius:6px;padding:3px 10px;color:{_section_lbl_c};font-size:11px;font-family:\'JetBrains Mono\',monospace;">RICE + Kano</span>'
    h_bar += f'<span style="background:{_section_badge_bg};border:1px solid {_hdr_border};border-radius:6px;padding:3px 10px;color:var(--accent-indigo);font-size:11px;font-family:\'JetBrains Mono\',monospace;">{len(results)} features</span>'
    h_bar += '</div></div>'
    st.markdown(f'<div style="animation:section-enter 0.5s cubic-bezier(0.16,1,0.3,1) both;">{h_bar}</div>', unsafe_allow_html=True)

    # Cards — session-state expand/collapse (no HTML details/summary)
    sorted_results = sorted(results, key=lambda x: x["priority_rank"])
    for i, r in enumerate(sorted_results):
        rank   = r.get("priority_rank", i + 1)
        is_top = (rank == 1)
        card_key = f"expand_{i}"
        is_expanded = i in st.session_state.expanded_cards

        # Auto-expand rank 1 on first render
        if is_top and i not in st.session_state.expanded_cards and card_key + "_seen" not in st.session_state:
            st.session_state.expanded_cards.add(i)
            st.session_state[card_key + "_seen"] = True
            is_expanded = True

        # Card header (always visible) — wrapped in staggered entrance animation
        card_delay = i * 90  # 90ms stagger between cards
        anim_style = f"animation:card-enter 0.55s cubic-bezier(0.16,1,0.3,1) {card_delay}ms both;"
        st.markdown(
            f'<div style="padding:0 32px 0;{anim_style}">'
            f'{card_header(r, i)}</div>',
            unsafe_allow_html=True,
        )

        # Expand/collapse button
        btn_label = "▲ Collapse" if is_expanded else "▼ Details"
        if st.button(btn_label, key=card_key, use_container_width=True):
            if i in st.session_state.expanded_cards:
                st.session_state.expanded_cards.discard(i)
            else:
                st.session_state.expanded_cards.add(i)
            st.rerun()

        # Expanded detail
        if is_expanded:
            st.markdown(f'<div style="padding:0 32px;">{card_detail(r)}</div>',
                        unsafe_allow_html=True)

        st.markdown('<div style="height:4px;"></div>', unsafe_allow_html=True)

    # Stakeholder objection for rank 1
    r1 = next((r for r in results if r.get("priority_rank") == 1), None)
    if r1:
        obj_text = html.escape(str(r1.get("risk", "")))
        obj_bg = "rgba(220,38,38,0.04)" if is_light else "rgba(239,68,68,0.06)"
        obj_h  = f'<div style="margin:4px 32px 16px;background:{obj_bg};border:1px solid rgba(239,68,68,0.2);border-radius:12px;padding:16px 20px;">'
        obj_h += '<div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;">'
        obj_h += '<div style="width:6px;height:6px;border-radius:50%;background:#EF4444;animation:pulse-red 2s ease-in-out infinite;"></div>'
        obj_h += '<span style="color:rgba(239,68,68,0.8);font-size:11px;font-weight:500;letter-spacing:0.08em;text-transform:uppercase;font-family:Inter,sans-serif;">Stakeholder Objection</span>'
        obj_h += '</div>'
        obj_h += f'<p style="color:{_txt_secondary};font-size:14px;font-family:Inter,sans-serif;font-style:italic;margin:0;">"{obj_text} — Are you certain this deserves #1?"</p>'
        obj_h += '</div>'
        st.markdown(obj_h, unsafe_allow_html=True)

    # ── Download buttons ──────────────────────────────────────────────────────
    st.markdown('<div style="padding:0 32px;">', unsafe_allow_html=True)
    csv = pd.DataFrame(results).to_csv(index=False).encode("utf-8")

    try:
        pdf_bytes = generate_pdf(features, results)
        pdf_ok = True
    except Exception as pdf_err:
        pdf_ok = False
        pdf_err_msg = str(pdf_err)

    col_csv, col_pdf = st.columns([1, 1], gap="small")
    with col_csv:
        st.download_button("⬇  Download CSV", data=csv,
                           file_name="prioritisation.csv", mime="text/csv",
                           use_container_width=True)
    with col_pdf:
        if pdf_ok:
            st.markdown("""
<style>
.pdf-btn-wrap { display:block; }
</style>
<div class="pdf-btn-wrap">""", unsafe_allow_html=True)
            st.download_button(
                label="📄  Export as PDF",
                data=pdf_bytes,
                file_name="prioritisation-report.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="pdf_download",
            )
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="color:#EF4444;font-size:11px;padding:8px 0;">PDF error: {html.escape(pdf_err_msg)}</div>',
                        unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Chart ─────────────────────────────────────────────────────────────────
    st.markdown('<div style="height:24px;"></div>', unsafe_allow_html=True)
    _chart_lbl_c = "#18181B" if is_light else "#4B4B5E"
    st.markdown(f'<div style="padding:0 32px 8px;">'
                f'<div style="font-size:11px;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;'
                f'color:{_chart_lbl_c};font-family:\'Inter\',sans-serif;">Feature Map</div>'
                f'<div style="font-size:12px;font-weight:500;color:{_chart_lbl_c};font-family:\'Inter\',sans-serif;margin-top:2px;opacity:0.75;">'
                f'Effort vs Impact — bubble size = RICE score</div>'
                f'</div>', unsafe_allow_html=True)

    # Theme-aware chart colors
    grid_color    = "rgba(0,0,0,0.10)"       if is_light else "rgba(255,255,255,0.05)"
    axis_color    = "#27272A"                 if is_light else "#8B8B9E"
    legend_bg     = "rgba(255,255,255,0.96)" if is_light else "rgba(13,13,18,0.85)"
    legend_border = "rgba(0,0,0,0.12)"       if is_light else "rgba(255,255,255,0.08)"
    hover_bg      = "#FFFFFF"                 if is_light else "#16161F"
    hover_txt     = "#0F0F14"                 if is_light else "#F0F0F5"
    quad_lbl_c    = "#52525B"                 if is_light else "rgba(255,255,255,0.25)"
    quad_line_c   = "rgba(0,0,0,0.15)"       if is_light else "rgba(255,255,255,0.08)"
    kano_colors = KANO_LIGHT if is_light else KANO_DARK

    # Build chart dataframe — merge results with original feature inputs
    chart_rows = []
    for row in results:
        m = [f for f in features if f["name"] == row["feature_name"]]
        if not m: continue
        f = m[0]
        chart_rows.append({
            "name":          row["feature_name"],
            "effort":        f["effort"],
            "impact":        f["impact"],
            "rice_score":    float(row["rice_score"]),
            "kano_category": row["kano_category"],
        })
    df_chart = pd.DataFrame(chart_rows)

    fig = px.scatter(
        df_chart,
        x="effort", y="impact",
        size="rice_score",
        color="kano_category",
        color_discrete_map=kano_colors,
        hover_name="name",
        hover_data={"rice_score": ":.1f", "kano_category": True, "effort": False, "impact": False},
        size_max=40,
        height=320,
    )

    fig.update_traces(
        mode="markers",
        marker=dict(opacity=0.85, line=dict(width=1.5, color="rgba(255,255,255,0.15)" if not is_light else "rgba(0,0,0,0.10)")),
        hovertemplate=(
            "<b>%{hovertext}</b><br>"
            "RICE Score: %{customdata[0]:.1f}<br>"
            "Kano: %{customdata[1]}<br>"
            "<extra></extra>"
        ),
    )

    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color=axis_color, size=11),
        xaxis=dict(title=dict(text="Effort →", font=dict(size=11)), gridcolor=grid_color,
                   zerolinecolor=quad_line_c, tickfont=dict(family="JetBrains Mono", size=10), range=[0, 11]),
        yaxis=dict(title=dict(text="Impact ↑", font=dict(size=11)), gridcolor=grid_color,
                   zerolinecolor=quad_line_c, tickfont=dict(family="JetBrains Mono", size=10), range=[0, 11]),
        legend=dict(bgcolor=legend_bg, bordercolor=legend_border, borderwidth=1,
                    font=dict(size=11), x=0.02, y=0.98, xanchor="left", yanchor="top"),
        hoverlabel=dict(bgcolor=hover_bg, bordercolor="rgba(99,102,241,0.4)",
                        font=dict(family="Inter", size=12, color=hover_txt), align="left"),
        margin=dict(l=20, r=20, t=20, b=20),
    )

    fig.add_hline(y=5.5, line_dash="dot", line_color=quad_line_c, line_width=1)
    fig.add_vline(x=5.5, line_dash="dot", line_color=quad_line_c, line_width=1)

    for qx, qy, qtxt in [
        (2,   9.5, "HIGH IMPACT<br>LOW EFFORT"),
        (8.5, 9.5, "HIGH IMPACT<br>HIGH EFFORT"),
        (2,   0.5, "LOW IMPACT<br>LOW EFFORT"),
        (8.5, 0.5, "LOW IMPACT<br>HIGH EFFORT"),
    ]:
        fig.add_annotation(x=qx, y=qy, text=qtxt, showarrow=False,
                           font=dict(size=8, color=quad_lbl_c, family="Inter"), align="center")

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ══════════════════════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════════════════════
_footer_border = "rgba(0,0,0,0.06)" if is_light else "rgba(255,255,255,0.06)"
st.markdown(f"""
<div style="border-top:1px solid {_footer_border};padding:32px;margin-top:48px;
            display:flex;align-items:center;justify-content:space-between;">
  <div></div>
  <p style="color:{_txt_tertiary};font-size:12px;font-family:'JetBrains Mono',monospace;margin:0;text-align:center;">
    ~ made by Sankalp Dusane
  </p>
  <p style="color:{_txt_tertiary};font-size:12px;font-family:'JetBrains Mono',monospace;margin:0;text-align:right;">
    AI Prioritisation Engine · Groq · Streamlit
  </p>
</div>
""", unsafe_allow_html=True)

# Fixed bottom-right signature
st.markdown(f"""
<div style="position:fixed;bottom:16px;right:20px;z-index:9998;
            font-family:'JetBrains Mono',monospace;font-size:10px;
            color:{_txt_tertiary};letter-spacing:0.06em;pointer-events:none;">
  ~ made by Sankalp Dusane
</div>
""", unsafe_allow_html=True)
