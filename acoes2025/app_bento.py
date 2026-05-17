import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Ações 2025 · Bento", layout="wide")

# ── CSS Bento Grid ────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #f0f2f5; color: #1e293b; font-family: 'Inter', 'Segoe UI', sans-serif; }
    /* Card base */
    .bento {
        background: #ffffff;
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.07);
        height: 100%;
    }
    /* Variantes de tamanho visual */
    .bento.accent { background: linear-gradient(135deg, #1e293b 0%, #334155 100%); color: #f8fafc; }
    .bento.accent .bento-label { color: #94a3b8 !important; }
    .bento.accent .bento-value { color: #f8fafc !important; }
    /* Tipografia interna */
    .bento-label { font-size: 11px; font-weight: 600; color: #64748b; letter-spacing: .8px; text-transform: uppercase; margin-bottom: 4px; }
    .bento-value { font-size: 28px; font-weight: 800; color: #1e293b; line-height: 1.1; }
    .bento-sub   { font-size: 13px; color: #94a3b8; margin-top: 4px; }
    .bento-title { font-size: 14px; font-weight: 700; color: #1e293b; margin-bottom: 10px; }
    .bento-title.light { color: #f8fafc; }
    /* Badge de retorno */
    .badge { display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 13px; font-weight: 700; }
    .badge.pos { background: #dcfce7; color: #166534; }
    .badge.neg { background: #fee2e2; color: #991b1b; }
    /* Sparkline overrides */
    [data-testid="stMetricValue"] { font-size: 18px !important; }
    hr { border-color: #e2e8f0; margin: 6px 0; }
</style>
""", unsafe_allow_html=True)

TICKERS = {"PETR4": "PETR4.SA", "ITUB4": "ITUB4.SA", "VALE3": "VALE3.SA"}
COLORS  = {"PETR4": "#f97316", "ITUB4": "#6366f1", "VALE3": "#10b981"}
FILL    = {"PETR4": "rgba(249,115,22,0.12)", "ITUB4": "rgba(99,102,241,0.12)", "VALE3": "rgba(16,185,129,0.12)"}


def fetch(symbol: str, ticker_name: str, start, end) -> pd.DataFrame | None:
    raw = yf.download(symbol, start=start, end=end + pd.Timedelta(days=1), progress=False)
    if raw.empty:
        return None
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.droplevel(1)
    if "Close" not in raw.columns:
        return None
    df = raw[["Open", "High", "Low", "Close", "Volume"]].copy().reset_index()
    df["Ticker"] = ticker_name
    return df


def build_data(start, end) -> pd.DataFrame | None:
    frames = [fetch(sym, name, start, end) for name, sym in TICKERS.items()]
    frames = [f for f in frames if f is not None]
    if not frames:
        return None
    data = pd.concat(frames, ignore_index=True).sort_values(["Ticker", "Date"])
    parts = []
    for t in data["Ticker"].unique():
        d = data[data["Ticker"] == t].copy()
        d["Retorno Diário (%)"]    = d["Close"].pct_change() * 100
        d["Retorno Acumulado (%)"] = (d["Close"] / d["Close"].iloc[0] - 1) * 100
        parts.append(d)
    return pd.concat(parts, ignore_index=True)


def sparkline(td: pd.DataFrame, col: str, color: str, fill: str, title: str = "", height: int = 160) -> go.Figure:
    fig = go.Figure(go.Scatter(
        x=td["Date"], y=td[col],
        mode="lines", line=dict(color=color, width=2),
        fill="tozeroy", fillcolor=fill,
        hovertemplate="%{x|%d/%m/%Y}: %{y:.2f}<extra></extra>",
    ))
    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=22 if title else 4, b=0),
        title=dict(text=title, font=dict(size=12, color="#64748b"), x=0) if title else None,
        xaxis=dict(visible=False),
        yaxis=dict(gridcolor="#f1f5f9", linecolor="rgba(0,0,0,0)", tickfont=dict(size=10, color="#94a3b8")),
        showlegend=False,
    )
    return fig


def badge_html(ret: float) -> str:
    cls  = "pos" if ret >= 0 else "neg"
    sign = "▲" if ret >= 0 else "▼"
    return f'<span class="badge {cls}">{sign} {abs(ret):.2f}%</span>'


# ── Cabeçalho + filtros ───────────────────────────────────────────────────────
col_h1, col_h2, col_h3 = st.columns([3, 1, 1])
with col_h1:
    st.markdown("# Ações 2025 · Bento")
with col_h2:
    start_date = st.date_input("De", value=pd.to_datetime("2025-01-01"))
with col_h3:
    end_date = st.date_input("Até", value=pd.to_datetime("2025-12-31"))

if start_date >= end_date:
    st.error("A data inicial deve ser anterior à data final.")
    st.stop()

data = build_data(start_date, end_date)
if data is None:
    st.warning("Nenhum dado encontrado.")
    st.stop()

# ── Linha 1: 3 cards de preço (1/3 cada) ─────────────────────────────────────
cols1 = st.columns(3)
for col, ticker in zip(cols1, TICKERS.keys()):
    td   = data[data["Ticker"] == ticker]
    last = float(td["Close"].iloc[-1])
    ret  = float(td["Retorno Acumulado (%)"].iloc[-1])
    máx  = float(td["Close"].max())
    mín  = float(td["Close"].min())
    color = COLORS[ticker]
    with col:
        st.markdown(f"""
        <div class="bento" style="border-top: 3px solid {color}">
            <div class="bento-label">{ticker}</div>
            <div class="bento-value">R$ {last:.2f}</div>
            <div class="bento-sub" style="margin-bottom:8px">
                {badge_html(ret)}
                &nbsp; Máx R$ {máx:.2f} · Mín R$ {mín:.2f}
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.plotly_chart(sparkline(td, "Close", color, FILL[ticker]), use_container_width=True, key=f"spark_price_{ticker}")

st.markdown("")

# ── Linha 2: comparativo grande (2/3) + volume médio (1/3) ───────────────────
col_big, col_side = st.columns([2, 1])

with col_big:
    st.markdown('<div class="bento">', unsafe_allow_html=True)
    st.markdown('<div class="bento-title">Retorno Acumulado Comparado</div>', unsafe_allow_html=True)
    fig_compare = go.Figure()
    for ticker in TICKERS:
        td = data[data["Ticker"] == ticker]
        fig_compare.add_trace(go.Scatter(
            x=td["Date"], y=td["Retorno Acumulado (%)"],
            name=ticker, mode="lines",
            line=dict(color=COLORS[ticker], width=2.5),
            hovertemplate=f"<b>{ticker}</b> · %{{x|%d/%m}}: %{{y:.2f}}%<extra></extra>",
        ))
    fig_compare.update_layout(
        height=320,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=8, b=0),
        legend=dict(orientation="h", y=1.08, x=0, font=dict(size=12)),
        xaxis=dict(gridcolor="#f1f5f9", linecolor="#e2e8f0"),
        yaxis=dict(gridcolor="#f1f5f9", linecolor="#e2e8f0", ticksuffix="%"),
        hovermode="x unified",
    )
    st.plotly_chart(fig_compare, use_container_width=True, key="compare_ret")
    st.markdown('</div>', unsafe_allow_html=True)

with col_side:
    st.markdown('<div class="bento accent">', unsafe_allow_html=True)
    st.markdown('<div class="bento-title light">Volume Médio Diário</div>', unsafe_allow_html=True)
    for ticker in TICKERS:
        td      = data[data["Ticker"] == ticker]
        vol     = float(td["Volume"].mean())
        vol_fmt = f"{vol:,.0f}".replace(",", ".")
        st.markdown(f"""
        <div style='margin-bottom:16px'>
            <div class='bento-label' style='color:#94a3b8'>{ticker}</div>
            <div style='font-size:20px;font-weight:700;color:#f8fafc'>{vol_fmt}</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='border-bottom:1px solid #475569;margin:8px 0'></div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("")

# ── Linha 3: sparklines de retorno acumulado (1/3 cada) ──────────────────────
cols3 = st.columns(3)
for col, ticker in zip(cols3, TICKERS.keys()):
    td    = data[data["Ticker"] == ticker]
    ret   = float(td["Retorno Acumulado (%)"].iloc[-1])
    color = COLORS[ticker]
    with col:
        st.markdown(f"""
        <div class="bento" style="border-top: 3px solid {color}">
            <div class="bento-label">{ticker} · Retorno Acumulado</div>
            <div class="bento-value" style="font-size:22px">{badge_html(ret)}</div>
        </div>
        """, unsafe_allow_html=True)
        st.plotly_chart(
            sparkline(td, "Retorno Acumulado (%)", color, FILL[ticker], height=140),
            use_container_width=True,
            key=f"spark_ret_{ticker}",
        )

st.markdown("")

# ── Linha 4: gráfico de preço comparativo (full width) ───────────────────────
st.markdown("**Preço de Fechamento — Comparativo**")
fig_price = go.Figure()
for ticker in TICKERS:
    td = data[data["Ticker"] == ticker]
    fig_price.add_trace(go.Scatter(
        x=td["Date"], y=td["Close"],
        name=ticker, mode="lines",
        line=dict(color=COLORS[ticker], width=2),
        hovertemplate=f"<b>{ticker}</b> · %{{x|%d/%m}}: R$ %{{y:.2f}}<extra></extra>",
    ))
fig_price.update_layout(
    height=300,
    paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
    margin=dict(l=0, r=0, t=8, b=0),
    legend=dict(orientation="h", y=1.08, x=0),
    xaxis=dict(gridcolor="#f1f5f9"),
    yaxis=dict(gridcolor="#f1f5f9", tickprefix="R$ "),
    hovermode="x unified",
)
st.plotly_chart(fig_price, use_container_width=True, key="price_full")

st.markdown("")

# ── Linha 5: tabelas históricas lado a lado ───────────────────────────────────
st.markdown("**Dados Históricos — Últimos 20 pregões**")
col_t1, col_t2, col_t3 = st.columns(3)
for col, ticker in zip([col_t1, col_t2, col_t3], TICKERS.keys()):
    td = data[data["Ticker"] == ticker]
    with col:
        st.markdown(f"**{ticker}**")
        st.dataframe(
            td[["Date", "Close", "Volume", "Retorno Diário (%)"]].tail(20)
            .style.format({
                "Close": "R$ {:.2f}",
                "Volume": "{:,}",
                "Retorno Diário (%)": "{:.2f}%",
            }),
            use_container_width=True,
            height=320,
        )
