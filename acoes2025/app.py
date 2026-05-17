import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Ações 2025", layout="wide")

st.title("Ações 2025")
st.markdown(
    """
    Aplicativo em Streamlit para buscar, analisar e visualizar cotações de PETR4, ITUB4 e VALE3 em 2025.
    Os dados são baixados separadamente para cada ticker e depois unidos em um único DataFrame.
    """
)

TICKERS = {
    "PETR4": "PETR4.SA",
    "ITUB4": "ITUB4.SA",
    "VALE3": "VALE3.SA",
}

col_date1, col_date2 = st.columns(2)
with col_date1:
    start_date = st.date_input("Data inicial", value=pd.to_datetime("2025-01-01"))
with col_date2:
    end_date = st.date_input("Data final", value=pd.to_datetime("2025-12-31"))


def normalize_symbol(symbol: str) -> str:
    symbol = symbol.strip().upper()
    return symbol if symbol.endswith(".SA") else f"{symbol}.SA"


def fetch_ticker_data(symbol: str, ticker_name: str, start, end) -> pd.DataFrame | None:
    symbol = normalize_symbol(symbol)
    raw = yf.download(symbol, start=start, end=end + pd.Timedelta(days=1), progress=False)
    if raw.empty:
        return None

    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.droplevel(1)

    if "Close" not in raw.columns:
        candidate = next((c for c in raw.columns if c.lower() in ["close", "adj close"]), None)
        if candidate is None:
            return None
        raw = raw.rename(columns={candidate: "Close"})

    required_columns = ["Open", "High", "Low", "Close", "Volume"]
    if not all(col in raw.columns for col in required_columns):
        return None

    df = raw.loc[:, required_columns].copy()
    df = df.reset_index()
    df["Ticker"] = ticker_name
    return df


if start_date >= end_date:
    st.error("A data inicial deve ser anterior à data final.")
else:
    st.info(f"Buscando dados de {', '.join(TICKERS.keys())} de {start_date} até {end_date}.")

    data_frames = []
    for ticker_name, ticker_symbol in TICKERS.items():
        ticker_data = fetch_ticker_data(ticker_symbol, ticker_name, start_date, end_date)
        if ticker_data is not None:
            data_frames.append(ticker_data)

    if not data_frames:
        st.warning("Não foram encontrados dados para nenhum dos tickers selecionados.")
    else:
        data = pd.concat(data_frames, ignore_index=True)
        data = data.sort_values(["Ticker", "Date"])

        all_parts = []
        for ticker in data["Ticker"].unique():
            t_data = data[data["Ticker"] == ticker].copy()
            t_data["Retorno Diário (%)"] = t_data["Close"].pct_change() * 100
            t_data["Retorno Acumulado (%)"] = (t_data["Close"] / t_data["Close"].iloc[0] - 1) * 100
            all_parts.append(t_data)
        data = pd.concat(all_parts, ignore_index=True)

        # ── Seção de comparação ──────────────────────────────────────────────
        st.subheader("Comparação entre as 3 Ações")

        col_c1, col_c2 = st.columns(2)
        with col_c1:
            price_compare_fig = px.line(
                data,
                x="Date",
                y="Close",
                color="Ticker",
                title="Preço de Fechamento — PETR4, ITUB4 e VALE3",
                labels={"Close": "Preço (R$)", "Date": "Data"},
            )
            price_compare_fig.update_layout(legend_title_text="Ação")
            st.plotly_chart(price_compare_fig, use_container_width=True)

        with col_c2:
            return_compare_fig = px.line(
                data,
                x="Date",
                y="Retorno Acumulado (%)",
                color="Ticker",
                title="Retorno Acumulado — PETR4, ITUB4 e VALE3",
                labels={"Retorno Acumulado (%)": "Retorno acumulado (%)", "Date": "Data"},
            )
            return_compare_fig.update_layout(legend_title_text="Ação")
            st.plotly_chart(return_compare_fig, use_container_width=True)

        # ── Análise individual por aba ───────────────────────────────────────
        st.divider()
        st.subheader("Análise Individual")

        tabs = st.tabs(list(TICKERS.keys()))

        for tab, ticker_name in zip(tabs, TICKERS.keys()):
            with tab:
                ticker_data = data[data["Ticker"] == ticker_name].copy()

                if ticker_data.empty:
                    st.warning(f"Não há dados disponíveis para {ticker_name}.")
                    continue

                last_close = float(ticker_data["Close"].iloc[-1])
                max_close = float(ticker_data["Close"].max())
                min_close = float(ticker_data["Close"].min())
                total_return = float(ticker_data["Retorno Acumulado (%)"].iloc[-1])
                average_volume = float(ticker_data["Volume"].mean())

                col1, col2, col3, col4, col5 = st.columns(5)
                col1.metric("Último preço (R$)", f"{last_close:.2f}")
                col2.metric("Máximo (R$)", f"{max_close:.2f}")
                col3.metric("Mínimo (R$)", f"{min_close:.2f}")
                col4.metric("Retorno acumulado", f"{total_return:.2f}%")
                col5.metric("Volume médio", f"{average_volume:,.0f}".replace(",", "."))

                col_g1, col_g2 = st.columns(2)
                with col_g1:
                    price_fig = px.line(
                        ticker_data,
                        x="Date",
                        y="Close",
                        title=f"Preço de Fechamento — {ticker_name}",
                        labels={"Close": "Preço (R$)", "Date": "Data"},
                    )
                    st.plotly_chart(price_fig, use_container_width=True)

                with col_g2:
                    return_fig = px.line(
                        ticker_data,
                        x="Date",
                        y="Retorno Acumulado (%)",
                        title=f"Retorno Acumulado — {ticker_name}",
                        labels={"Retorno Acumulado (%)": "Retorno acumulado (%)", "Date": "Data"},
                    )
                    st.plotly_chart(return_fig, use_container_width=True)

                st.subheader("Dados Históricos")
                st.dataframe(
                    ticker_data[["Date", "Open", "High", "Low", "Close", "Volume", "Retorno Diário (%)"]]
                    .tail(20)
                    .style.format({
                        "Open": "R$ {:.2f}",
                        "High": "R$ {:.2f}",
                        "Low": "R$ {:.2f}",
                        "Close": "R$ {:.2f}",
                        "Volume": "{:,}",
                        "Retorno Diário (%)": "{:.2f}%",
                    }),
                    use_container_width=True,
                )
