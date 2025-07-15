import streamlit as st
import pandas as pd
import requests
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator
import time

st.set_page_config(page_title="Radar Técnico Cripto", layout="wide")
st.title("📈 Radar Técnico Cripto - RSI + EMA20 + EMA50")
st.markdown("""
Aplicativo para análise técnica das principais criptomoedas.
- Dados de moedas via CoinGecko API
- Candles via Binance API
- Indicadores calculados localmente com `ta`
""")

INTERVALOS_BINANCE = {
    "1h": "1h",
    "4h": "4h",
    "1d": "1d"
}

@st.cache_data(ttl=600)
def get_top_coins(n=100):
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": n,
        "page": 1,
        "sparkline": False
    }
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Erro ao buscar top moedas CoinGecko: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=600)
def get_binance_symbols():
    url = "https://api.binance.com/api/v3/exchangeInfo"
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        data = r.json()
        return [s["symbol"] for s in data["symbols"]]
    except Exception as e:
        st.error(f"Erro ao obter símbolos da Binance: {e}")
        return []

@st.cache_data(ttl=300)
def get_binance_klines(symbol: str, interval: str, limit: int = 500):
    url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        df = pd.DataFrame(data, columns=[
            "open_time", "open", "high", "low", "close", "volume",
            "close_time", "quote_asset_volume", "number_of_trades",
            "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"
        ])
        df["close"] = df["close"].astype(float)
        df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
        return df
    except Exception as e:
        st.error(f"Erro ao obter candles Binance para {symbol}: {e}")
        return pd.DataFrame()

def calcular_indicadores(df):
    if df.empty or len(df) < 50:
        return None

    close = df["close"]
    rsi = RSIIndicator(close=close, window=14).rsi()
    ema20 = EMAIndicator(close=close, window=20).ema_indicator()
    ema50 = EMAIndicator(close=close, window=50).ema_indicator()

    rsi_ult = rsi.iloc[-1]
    ema20_ult = ema20.iloc[-1]
    ema50_ult = ema50.iloc[-1]

    if rsi_ult <= 30:
        rsi_class = "Sobrevendida"
    elif rsi_ult >= 70:
        rsi_class = "Sobrecomprada"
    else:
        rsi_class = "Neutra"

    if ema20_ult > ema50_ult:
        tendencia = "Alta"
    elif ema20_ult < ema50_ult:
        tendencia = "Baixa"
    else:
        tendencia = "Neutra"

    return {
        "RSI": round(rsi_ult, 2),
        "Classificação RSI": rsi_class,
        "EMA20": round(ema20_ult, 2),
        "EMA50": round(ema50_ult, 2),
        "Tendência": tendencia
    }

# Inputs UI
top_n = st.slider("Número de moedas a analisar (top N do mercado)", 5, 100, 20)
intervalo = st.selectbox("Intervalo de tempo", list(INTERVALOS_BINANCE.keys()), index=0)
filtro_rsi = st.multiselect("Filtrar por classificação RSI", ["Sobrevendida", "Neutra", "Sobrecomprada"], default=["Sobrevendida", "Neutra", "Sobrecomprada"])
input_moeda = st.text_input("Pesquisar símbolo de moeda (ex: BTCUSDT). Deixe vazio para usar top N.")

botao_analise = st.button("Iniciar análise")

if botao_analise:
    with st.spinner("Buscando dados e calculando indicadores..."):
        df_moedas = get_top_coins(top_n)
        if df_moedas.empty:
            st.warning("Nenhuma moeda encontrada no CoinGecko.")
            st.stop()

        symbols_binance = get_binance_symbols()
        if not symbols_binance:
            st.warning("Não foi possível obter lista de símbolos da Binance.")
            st.stop()

        if input_moeda.strip():
            symbols = [input_moeda.strip().upper()]
        else:
            symbols = []
            for _, row in df_moedas.iterrows():
                symbol_binance = row["symbol"].upper() + "USDT"
                symbols.append(symbol_binance)

        resultados = []
        for symbol in symbols:
            if symbol not in symbols_binance:
                st.warning(f"Símbolo {symbol} não listado na Binance. Ignorando.")
                continue

            df_candles = get_binance_klines(symbol, INTERVALOS_BINANCE[intervalo])
            if df_candles.empty:
                st.warning(f"Sem dados de candles para {symbol}")
                continue

            indicadores = calcular_indicadores(df_candles)
            if not indicadores:
                st.warning(f"Indicadores insuficientes para {symbol}")
                continue

            preco_atual = df_candles["close"].iloc[-1]
            resultado = {
                "Moeda": symbol,
                "Preço Atual (USDT)": round(preco_atual, 4),
                **indicadores
            }
            resultados.append(resultado)

            time.sleep(0.15)  # Evita limite API

        if resultados:
            df_result = pd.DataFrame(resultados)
            df_filtrado = df_result[df_result["Classificação RSI"].isin(filtro_rsi)]

            def alerta_row(row):
                if row["RSI"] <= 30 and row["Tendência"] == "Alta":
                    return "🔔"
                return ""

            df_filtrado["Alerta"] = df_filtrado.apply(alerta_row, axis=1)

            st.subheader("📋 Resultados da análise técnica")
            st.dataframe(df_filtrado.style.applymap(lambda v: "background-color: lightgreen" if v == "🔔" else "", subset=["Alerta"]), use_container_width=True)

            if df_filtrado["Alerta"].str.contains("🔔").any():
                st.success("Moedas com RSI ≤ 30 e Tendência de Alta destacadas!")
            else:
                st.info("Nenhuma moeda com alerta no momento.")
        else:
            st.warning("Nenhum resultado obtido. Tente outro filtro ou símbolo.")
