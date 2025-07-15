import streamlit as st
import pandas as pd
import requests
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator
from datetime import datetime, timedelta
import time

st.set_page_config(page_title="Radar Técnico Cripto - Coinbase", layout="wide")
st.title("📈 Radar Técnico Cripto - RSI + EMA20 + EMA50 (Coinbase)")

INTERVALOS = {
    "1h": 3600,
    "4h": 3600 * 4,
    "1d": 3600 * 24
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

def get_coinbase_candles(product_id: str, interval_seconds: int, days_back: int = 30):
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=days_back)
    url = f"https://api.pro.coinbase.com/products/{product_id}/candles"
    params = {
        "start": start_time.isoformat() + "Z",
        "end": end_time.isoformat() + "Z",
        "granularity": interval_seconds
    }
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        # Coinbase retorna [time, low, high, open, close, volume]
        df = pd.DataFrame(data, columns=["time", "low", "high", "open", "close", "volume"])
        df["time"] = pd.to_datetime(df["time"], unit='s')
        df = df.sort_values("time")
        return df
    except Exception as e:
        st.warning(f"Erro ao obter candles Coinbase para {product_id}: {e}")
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

# UI Inputs
top_n = st.slider("Número de moedas a analisar (top N do mercado)", 5, 50, 20)
intervalo = st.selectbox("Intervalo de tempo", list(INTERVALOS.keys()), index=0)
filtro_rsi = st.multiselect("Filtrar por classificação RSI", ["Sobrevendida", "Neutra", "Sobrecomprada"], default=["Sobrevendida", "Neutra", "Sobrecomprada"])
input_moeda = st.text_input("Pesquisar símbolo de moeda (ex: BTC-USD). Deixe vazio para usar top N.")

botao_analise = st.button("Iniciar análise")

if botao_analise:
    with st.spinner("Buscando dados e calculando indicadores..."):
        df_moedas = get_top_coins(top_n)
        if df_moedas.empty:
            st.warning("Nenhuma moeda encontrada no CoinGecko.")
            st.stop()

        if input_moeda.strip():
            symbols = [input_moeda.strip().upper()]
        else:
            symbols = []
            for _, row in df_moedas.iterrows():
                # Coinbase usa formato "BTC-USD"
                symbol_cb = row["symbol"].upper() + "-USD"
                symbols.append(symbol_cb)

        resultados = []
        for symbol in symbols:
            df_candles = get_coinbase_candles(symbol, INTERVALOS[intervalo])
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
                "Preço Atual (USD)": round(preco_atual, 4),
                **indicadores
            }
            resultados.append(resultado)

            time.sleep(0.15)  # para evitar throttling

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
