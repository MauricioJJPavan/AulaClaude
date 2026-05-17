import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Ações 2025 · Executive", layout="wide")

# ── CSS corporativo limpo ────────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #f8f9fa; color: #1a1a2e; font-family: 'Segoe UI', sans-serif; }
    /* Header faixa azul corporativa */
    .corp-header {
        background: linear-gradient(90deg, #1a1a2e 0%, #16213e 60%, #0f3460 100%);
        padding: 20px 32px;
        border-radius: 10px;
        margin-bottom: 24px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .corp-header h1 { color: #ffffff !important; font-size: 22px; margin: 0; font-weight: 600; }
    .corp-header .sub { color: #a0aec0; font-size: 13px; }
    /* Cards de resumo */
    .summary-card {
        background: #ffffff;
        border-radius: 10px;
        padding: 18px 22px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.06);
        border-top: 3px solid var(--accent);
        margin-bottom: 12px;
    }
    .summary-card .s-label { font-size: 11px; font-weight: 600; color: #718096; letter-spacing: .8px; text-transform: uppercase; }
    .summary-card .s-value { font-size: 24px; font-weight: 700; color: #1a1a2e; margin: 6px 0 2px; }
    .summary-card .s-sub   { font-size: 13px; color: #718096; }
    .s-pos { color: #276749 !important; font-weight: 600; }
    .s-neg { color: #c53030 !important; font-weight: 600; }
    /* Seção */
    .section-title { font-size: 15px; font-weight: 700; color: #2d3748; border-left: 4px solid #0f3460; padding-left: 10px; margin: 24px 0 12px; }
    /* Barra filtro */
    .filter-bar {
        background: #ffffff;
        border-radius: 8px;
        padding: 12px 20px;
        margin-bottom: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.07);
        display: flex;
        gap: 16px;
        align-items: center;
    }
    hr { border-color: #e2e8f0; }
    [data-testid="stMetricValue"] { font-size: 20px !important; }
</style>
""", unsafe_allow_html=True)

TICKERS = {"PETR4": "PETR4.SA", "ITUB4": "ITUB4.SA", "VALE3": "VALE3.SA"}
COLORS  = {"PETR4": "#e53e3e", "ITUB4": "#2b6cb0", "VALE3": "#276749"}
FILL    = {"PETR4": "rgba(229,62,62,0.08)", "ITUB4": "rgba(43,108,176,0.08)", "VALE3": "rgba(39,103,73,0.08)"}


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


def light_layout(title: str = "") -> dict:
    return dict(
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font=dict(color="#2d3748", family="Segoe UI, sans-serif", size=12),
        title=dict(text=title, font=dict(size=14, color="#1a1a2e"), x=0.01),
        xaxis=dict(gridcolor="#edf2f7", linecolor="#e2e8f0", tickfont=dict(color="#718096")),
        yaxis=dict(gridcolor="#edf2f7", linecolor="#e2e8f0", tickfont=dict(color="#718096")),
        legend=dict(bgcolor="#f8f9fa", bordercolor="#e2e8f0", borderwidth=1, font=dict(color="#2d3748")),
        margin=dict(l=10, r=10, t=45, b=10),
        hovermode="x unified",
    )


def summary_card(label: str, value: str, sub: str, accent: str, sub_class: str = "") -> str:
    return f"""
    <div class="summary-card" style="--accent:{accent}">
        <div class="s-label">{label}</div>
        <div class="s-value">{value}</div>
        <div class="s-sub {sub_class}">{sub}</div>
    </div>
    """


# ── Header ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="corp-header">
    <div>
        <h1>Painel Executivo · Ações 2025</h1>
        <div class="sub">PETR4 &nbsp;·&nbsp; ITUB4 &nbsp;·&nbsp; VALE3 &nbsp;·&nbsp; B3 / Yahoo Finance</div>
    </div>
</div>
""", unsafe_allow_html=True)

col_d1, col_d2, _ = st.columns([1, 1, 3])
with col_d1:
    start_date = st.date_input("Período inicial", value=pd.to_datetime("2025-01-01"))
with col_d2:
    end_date = st.date_input("Período final", value=pd.to_datetime("2025-12-31"))

if start_date >= end_date:
    st.error("A data inicial deve ser anterior à data final.")
    st.stop()

data = build_data(start_date, end_date)
if data is None:
    st.warning("Nenhum dado encontrado.")
    st.stop()

# ── Cards de resumo ──────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Resumo Executivo</div>', unsafe_allow_html=True)
cols = st.columns(3)
for col, ticker in zip(cols, TICKERS):
    td  = data[data["Ticker"] == ticker]
    if td.empty:
        continue
    last = float(td["Close"].iloc[-1])
    ret  = float(td["Retorno Acumulado (%)"].iloc[-1])
    vol  = float(td["Volume"].mean())
    máx  = float(td["Close"].max())
    mín  = float(td["Close"].min())
    sign = "▲" if ret >= 0 else "▼"
    cls  = "s-pos" if ret >= 0 else "s-neg"
    with col:
        st.markdown(
            summary_card(ticker, f"R$ {last:.2f}", f"{sign} {abs(ret):.2f}% acumulado", COLORS[ticker], cls),
            unsafe_allow_html=True,
        )
        st.markdown(
            summary_card("Máx / Mín", f"R$ {máx:.2f}", f"Mín: R$ {mín:.2f}", COLORS[ticker]),
            unsafe_allow_html=True,
        )
        st.markdown(
            summary_card("Volume médio", f"{vol:,.0f}".replace(",", "."), "contratos/dia", COLORS[ticker]),
            unsafe_allow_html=True,
        )

st.markdown("---")

# ── Gráfico de área comparativo — retorno acumulado ──────────────────────────
st.markdown('<div class="section-title">Retorno Acumulado Comparado</div>', unsafe_allow_html=True)
fig_ret = go.Figure()
for ticker in TICKERS:
    td = data[data["Ticker"] == ticker]
    fig_ret.add_trace(go.Scatter(
        x=td["Date"], y=td["Retorno Acumulado (%)"],
        name=ticker, mode="lines",
        line=dict(color=COLORS[ticker], width=2),
        fill="tozeroy", fillcolor=FILL[ticker],
        hovertemplate=(
            f"<b>{ticker}</b><br>"
            "Data: %{x|%d/%m/%Y}<br>"
            "Retorno: <b>%{y:.2f}%</b><br>"
            "<extra></extra>"
        ),
    ))
fig_ret.update_layout(**light_layout("Retorno acumulado desde o início do período (%)"))
st.plotly_chart(fig_ret, use_container_width=True)

st.markdown("---")

# ── Gráfico de área — preço de fechamento ────────────────────────────────────
st.markdown('<div class="section-title">Preço de Fechamento</div>', unsafe_allow_html=True)
fig_price = go.Figure()
for ticker in TICKERS:
    td = data[data["Ticker"] == ticker]
    fig_price.add_trace(go.Scatter(
        x=td["Date"], y=td["Close"],
        name=ticker, mode="lines",
        line=dict(color=COLORS[ticker], width=2),
        fill="tozeroy", fillcolor=FILL[ticker],
        hovertemplate=(
            f"<b>{ticker}</b><br>"
            "Data: %{x|%d/%m/%Y}<br>"
            "Fechamento: <b>R$ %{y:.2f}</b><br>"
            "<extra></extra>"
        ),
    ))
fig_price.update_layout(**light_layout("Preço de fechamento (R$)"))
st.plotly_chart(fig_price, use_container_width=True)

st.markdown("---")

# ── Análise individual em abas ────────────────────────────────────────────────
st.markdown('<div class="section-title">Análise Individual</div>', unsafe_allow_html=True)
tabs = st.tabs(list(TICKERS.keys()))

for tab, ticker in zip(tabs, TICKERS.keys()):
    with tab:
        td = data[data["Ticker"] == ticker].copy()
        if td.empty:
            st.warning(f"Sem dados para {ticker}.")
            continue

        last = float(td["Close"].iloc[-1])
        ret  = float(td["Retorno Acumulado (%)"].iloc[-1])
        color = COLORS[ticker]

        # Gráfico de área individual com tooltip rico
        fig_ind = go.Figure()
        fig_ind.add_trace(go.Scatter(
            x=td["Date"], y=td["Close"],
            name="Fechamento", mode="lines",
            line=dict(color=color, width=2.5),
            fill="tozeroy", fillcolor=FILL[ticker],
            hovertemplate=(
                "Data: %{x|%d/%m/%Y}<br>"
                "Abertura: R$ %{customdata[0]:.2f}<br>"
                "Máxima: R$ %{customdata[1]:.2f}<br>"
                "Mínima: R$ %{customdata[2]:.2f}<br>"
                "Fechamento: <b>R$ %{y:.2f}</b><br>"
                "Volume: %{customdata[3]:,.0f}<br>"
                "Retorno do dia: %{customdata[4]:.2f}%<br>"
                "<extra></extra>"
            ),
            customdata=td[["Open", "High", "Low", "Volume", "Retorno Diário (%)"]].values,
        ))
        layout_ind = light_layout(f"Preço de Fechamento — {ticker}")
        layout_ind["hovermode"] = "x"
        fig_ind.update_layout(**layout_ind)
        st.plotly_chart(fig_ind, use_container_width=True)

        # Retorno acumulado individual
        fig_ra = go.Figure(go.Scatter(
            x=td["Date"], y=td["Retorno Acumulado (%)"],
            mode="lines", fill="tozeroy",
            line=dict(color=color, width=2),
            fillcolor=FILL[ticker],
            hovertemplate="Data: %{x|%d/%m/%Y}<br>Retorno: <b>%{y:.2f}%</b><extra></extra>",
        ))
        fig_ra.update_layout(**light_layout(f"Retorno Acumulado — {ticker} (%)"))
        st.plotly_chart(fig_ra, use_container_width=True)

        st.markdown("##### Últimos 20 pregões")
        st.dataframe(
            td[["Date", "Open", "High", "Low", "Close", "Volume", "Retorno Diário (%)"]].tail(20)
            .style.format({
                "Open": "R$ {:.2f}", "High": "R$ {:.2f}", "Low": "R$ {:.2f}",
                "Close": "R$ {:.2f}", "Volume": "{:,}", "Retorno Diário (%)": "{:.2f}%",
            }),
            use_container_width=True,
        )
