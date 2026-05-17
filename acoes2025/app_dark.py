import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Trading Desk 2025", layout="wide", initial_sidebar_state="expanded")

# ── Tema escuro via CSS ──────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Fundo geral */
    .stApp { background-color: #0d1117; color: #e6edf3; }
    section[data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
    /* Cards de preço */
    .price-card {
        background: linear-gradient(135deg, #1c2128 0%, #21262d 100%);
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 10px;
    }
    .price-card .ticker { font-size: 13px; font-weight: 600; color: #8b949e; letter-spacing: 1px; }
    .price-card .price  { font-size: 28px; font-weight: 700; color: #e6edf3; margin: 4px 0; }
    .price-card .up     { font-size: 15px; font-weight: 600; color: #3fb950; }
    .price-card .down   { font-size: 15px; font-weight: 600; color: #f85149; }
    /* Títulos */
    h1, h2, h3 { color: #e6edf3 !important; }
    /* Métricas */
    [data-testid="stMetricValue"]  { color: #e6edf3 !important; font-size: 22px !important; }
    [data-testid="stMetricLabel"]  { color: #8b949e !important; }
    [data-testid="stMetricDelta"]  svg { display: none; }
    /* Divider */
    hr { border-color: #30363d; }
    /* Dataframe */
    .stDataFrame { background-color: #161b22; }
</style>
""", unsafe_allow_html=True)

TICKERS = {"PETR4": "PETR4.SA", "ITUB4": "ITUB4.SA", "VALE3": "VALE3.SA"}
COLORS  = {"PETR4": "#58a6ff", "ITUB4": "#3fb950", "VALE3": "#d2a8ff"}

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## Trading Desk 2025")
    st.markdown("---")
    page = st.radio(
        "Navegação",
        ["Visão Geral", "PETR4", "ITUB4", "VALE3"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    start_date = st.date_input("De", value=pd.to_datetime("2025-01-01"))
    end_date   = st.date_input("Até", value=pd.to_datetime("2025-12-31"))
    st.markdown("---")
    st.caption("Dados: Yahoo Finance · B3")


def fetch(symbol: str, ticker_name: str, start, end) -> pd.DataFrame | None:
    symbol = symbol if symbol.endswith(".SA") else f"{symbol}.SA"
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
    frames = []
    for name, sym in TICKERS.items():
        df = fetch(sym, name, start, end)
        if df is not None:
            frames.append(df)
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


def dark_layout() -> dict:
    return dict(
        paper_bgcolor="#0d1117",
        plot_bgcolor="#0d1117",
        font=dict(color="#8b949e", family="monospace"),
        xaxis=dict(gridcolor="#21262d", linecolor="#30363d", zerolinecolor="#30363d"),
        yaxis=dict(gridcolor="#21262d", linecolor="#30363d", zerolinecolor="#30363d"),
        legend=dict(bgcolor="#161b22", bordercolor="#30363d", borderwidth=1),
        margin=dict(l=10, r=10, t=40, b=10),
    )


def price_card(ticker: str, last: float, ret: float) -> str:
    cls   = "up" if ret >= 0 else "down"
    sign  = "▲" if ret >= 0 else "▼"
    color = COLORS[ticker]
    return f"""
    <div class="price-card" style="border-left: 3px solid {color};">
        <div class="ticker">{ticker}</div>
        <div class="price">R$ {last:.2f}</div>
        <div class="{cls}">{sign} {abs(ret):.2f}%</div>
    </div>
    """


if start_date >= end_date:
    st.error("A data inicial deve ser anterior à data final.")
    st.stop()

data = build_data(start_date, end_date)
if data is None:
    st.warning("Nenhum dado encontrado.")
    st.stop()

# ── Página: Visão Geral ──────────────────────────────────────────────────────
if page == "Visão Geral":
    st.markdown("## Visão Geral do Mercado")

    # Cards laterais + gráfico principal
    col_cards, col_main = st.columns([1, 3])

    with col_cards:
        for ticker in TICKERS:
            td = data[data["Ticker"] == ticker]
            if td.empty:
                continue
            last   = float(td["Close"].iloc[-1])
            ret    = float(td["Retorno Acumulado (%)"].iloc[-1])
            st.markdown(price_card(ticker, last, ret), unsafe_allow_html=True)

    with col_main:
        fig = go.Figure()
        for ticker in TICKERS:
            td = data[data["Ticker"] == ticker]
            fig.add_trace(go.Scatter(
                x=td["Date"], y=td["Retorno Acumulado (%)"],
                name=ticker, line=dict(color=COLORS[ticker], width=2),
                hovertemplate=f"<b>{ticker}</b><br>Data: %{{x|%d/%m/%Y}}<br>Retorno: %{{y:.2f}}%<extra></extra>",
            ))
        fig.update_layout(title="Retorno Acumulado (%)", **dark_layout())
        st.plotly_chart(fig, use_container_width=True)

    # Gráfico de preços comparativo
    fig2 = go.Figure()
    for ticker in TICKERS:
        td = data[data["Ticker"] == ticker]
        fig2.add_trace(go.Scatter(
            x=td["Date"], y=td["Close"],
            name=ticker, line=dict(color=COLORS[ticker], width=1.5),
            hovertemplate=f"<b>{ticker}</b><br>%{{x|%d/%m/%Y}}<br>R$ %{{y:.2f}}<extra></extra>",
        ))
    fig2.update_layout(title="Preço de Fechamento (R$)", **dark_layout())
    st.plotly_chart(fig2, use_container_width=True)

# ── Página: ação individual ──────────────────────────────────────────────────
else:
    ticker = page
    td = data[data["Ticker"] == ticker].copy()

    if td.empty:
        st.warning(f"Sem dados para {ticker}.")
        st.stop()

    color  = COLORS[ticker]
    last   = float(td["Close"].iloc[-1])
    máx    = float(td["Close"].max())
    mín    = float(td["Close"].min())
    ret    = float(td["Retorno Acumulado (%)"].iloc[-1])
    vol    = float(td["Volume"].mean())

    st.markdown(f"## {ticker}")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Preço atual",       f"R$ {last:.2f}")
    c2.metric("Máximo",            f"R$ {máx:.2f}")
    c3.metric("Mínimo",            f"R$ {mín:.2f}")
    c4.metric("Retorno acumulado", f"{ret:.2f}%")
    c5.metric("Volume médio",      f"{vol:,.0f}".replace(",", "."))

    # Candlestick + volume em subplot
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.75, 0.25], vertical_spacing=0.03)
    fig.add_trace(go.Candlestick(
        x=td["Date"], open=td["Open"], high=td["High"], low=td["Low"], close=td["Close"],
        name="OHLC",
        increasing_line_color=color, decreasing_line_color="#f85149",
    ), row=1, col=1)
    bar_colors = [color if v >= 0 else "#f85149" for v in td["Retorno Diário (%)"].fillna(0)]
    fig.add_trace(go.Bar(
        x=td["Date"], y=td["Volume"], name="Volume",
        marker_color=bar_colors, opacity=0.6,
    ), row=2, col=1)
    layout = dark_layout()
    layout["xaxis2"] = dict(gridcolor="#21262d", linecolor="#30363d", rangeslider=dict(visible=False))
    layout["yaxis2"] = dict(gridcolor="#21262d", linecolor="#30363d")
    layout["title"]  = f"Candlestick — {ticker}"
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True)

    # Retorno acumulado individual
    fig3 = go.Figure(go.Scatter(
        x=td["Date"], y=td["Retorno Acumulado (%)"],
        fill="tozeroy", line=dict(color=color, width=2),
        fillcolor=color.replace(")", ", 0.15)").replace("rgb", "rgba") if "rgb" in color else f"{color}26",
        hovertemplate="%{x|%d/%m/%Y}<br>Retorno: %{y:.2f}%<extra></extra>",
    ))
    fig3.update_layout(title=f"Retorno Acumulado — {ticker}", **dark_layout())
    st.plotly_chart(fig3, use_container_width=True)

    # Tabela
    st.markdown("#### Últimos 20 pregões")
    st.dataframe(
        td[["Date", "Open", "High", "Low", "Close", "Volume", "Retorno Diário (%)"]].tail(20)
        .style.format({
            "Open": "R$ {:.2f}", "High": "R$ {:.2f}", "Low": "R$ {:.2f}",
            "Close": "R$ {:.2f}", "Volume": "{:,}", "Retorno Diário (%)": "{:.2f}%",
        }),
        use_container_width=True,
    )
