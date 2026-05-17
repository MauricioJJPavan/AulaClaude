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

selected_ticker = st.selectbox(
    "Selecione a ação", list(TICKERS.keys()), index=0)
start_date = st.date_input("Data inicial", value=pd.to_datetime("2025-01-01"))
end_date = st.date_input("Data final", value=pd.to_datetime("2025-12-31"))


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[-1] if isinstance(c, tuple) else c for c in df.columns]
    return df


def normalize_symbol(symbol: str) -> str:
    symbol = symbol.strip().upper()
    return symbol if symbol.endswith(".SA") else f"{symbol}.SA"


def fetch_ticker_data(symbol: str, ticker_name: str, start, end) -> pd.DataFrame | None:
    symbol = normalize_symbol(symbol)
    raw = yf.download(symbol, start=start, end=end +
                      pd.Timedelta(days=1), progress=False)
    if raw.empty:
        return None

    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.droplevel(1)

    if "Close" not in raw.columns:
        candidate = next((c for c in raw.columns if c.lower()
                         in ["close", "adj close"]), None)
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
    st.info(
        f"Buscando dados de {', '.join(TICKERS.keys())} de {start_date} até {end_date}.")

    data_frames = []
    for ticker_name, ticker_symbol in TICKERS.items():
        ticker_data = fetch_ticker_data(
            ticker_symbol, ticker_name, start_date, end_date)
        if ticker_data is not None:
            data_frames.append(ticker_data)

    if not data_frames:
        st.warning(
            "Não foram encontrados dados para nenhum dos tickers selecionados.")
    else:
        data = pd.concat(data_frames, ignore_index=True)
        data = data.sort_values(["Ticker", "Date"])

        # Retorno acumulado para todas as ações (usado no gráfico comparativo)
        all_returns = []
        for ticker in data["Ticker"].unique():
            t_data = data[data["Ticker"] == ticker].copy()
            t_data["Retorno Acumulado (%)"] = (
                t_data["Close"] / t_data["Close"].iloc[0] - 1) * 100
            all_returns.append(t_data)
        data = pd.concat(all_returns, ignore_index=True)

        st.subheader("Comparação: Retorno Acumulado das 3 Ações")
        compare_fig = px.line(
            data,
            x="Date",
            y="Retorno Acumulado (%)",
            color="Ticker",
            title="Retorno Acumulado Comparado — PETR4, ITUB4 e VALE3",
            labels={"Retorno Acumulado (%)": "Retorno acumulado (%)", "Date": "Data"},
        )
        compare_fig.update_layout(legend_title_text="Ação")
        st.plotly_chart(compare_fig, use_container_width=True)

        st.divider()
        st.subheader(f"Análise individual: {selected_ticker}")

        selected_data = data[data["Ticker"] == selected_ticker].copy()
        if selected_data.empty:
            st.warning(f"Não há dados disponíveis para {selected_ticker}.")
        else:
            selected_data["Retorno Diário (%)"] = selected_data["Close"].pct_change() * 100

            last_close = float(selected_data["Close"].iloc[-1])
            max_close = float(selected_data["Close"].max())
            min_close = float(selected_data["Close"].min())
            total_return = float(
                selected_data["Retorno Acumulado (%)"].iloc[-1])
            average_volume = float(selected_data["Volume"].mean())

            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Resumo")
                st.metric("Último preço (R$)", f"{last_close:.2f}")
                st.metric("Máximo 2025 (R$)", f"{max_close:.2f}")
                st.metric("Mínimo 2025 (R$)", f"{min_close:.2f}")

            with col2:
                st.subheader("Performance")
                st.metric("Retorno acumulado", f"{total_return:.2f}%")
                st.metric("Volume médio",
                          f"{average_volume:,.0f}".replace(",", "."))

            st.subheader("Preço")
            price_fig = px.line(
                selected_data,
                x="Date",
                y="Close",
                title=f"Preço de {selected_ticker} em 2025",
                labels={"Close": "Preço (R$)", "Date": "Data"},
            )
            st.plotly_chart(price_fig, use_container_width=True)

            st.subheader("Retorno Acumulado")
            return_fig = px.line(
                selected_data,
                x="Date",
                y="Retorno Acumulado (%)",
                title=f"Retorno Acumulado de {selected_ticker} em 2025",
                labels={
                    "Retorno Acumulado (%)": "Retorno acumulado (%)", "Date": "Data"},
            )
            st.plotly_chart(return_fig, use_container_width=True)

            st.subheader("Dados Históricos")
            st.dataframe(
                selected_data[["Date", "Open", "High", "Low",
                               "Close", "Volume", "Retorno Diário (%)"]]
                .tail(20)
                .style.format({
                    "Open": "R$ {:.2f}",
                    "High": "R$ {:.2f}",
                    "Low": "R$ {:.2f}",
                    "Close": "R$ {:.2f}",
                    "Volume": "{:,}",
                    "Retorno Diário (%)": "{:.2f}%",
                })
            )

            st.subheader("Dados de todos os tickers")
            st.dataframe(
                data[["Date", "Ticker", "Open", "High", "Low", "Close", "Volume"]]
                .tail(30)
            )
