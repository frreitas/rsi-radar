import streamlit as st
import pandas as pd
import requests
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator

st.set_page_config(page_title="Radar RSI Cripto", layout="wide")
st.title("📊 Radar RSI com Tendência de Alta")
st.markdown("Analisa as 100 principais criptos com RSI e EMAs em tempo real via Binance API.")

# ====== INTERVALO ESCOLHIDO PELO USUÁRIO ======
intervalo = st.selectbox("⏱️ Intervalo de tempo", ["1h", "4h", "1d"], index=0)
binance_interval = {"1h": "1h", "4h": "4h", "1d": "1d"}[intervalo]
limite_velas = 100

# ====== FUNÇÕES AUXILIARES ======
@st.cache_data(ttl=300)
def get_top_100_symbols():
    """
    Retorna os 100 principais símbolos de moedas via CoinGecko API,
    transformando para o padrão da Binance (ex: BTC → BTCUSDT).
    """
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 100,
        "page": 1
    }
    try:
        res = requests.get(url, params=params)
        res.raise_for_status()
        coins = res.json()
        symbols = []
        for coin in coins:
            if "symbol" in coin and coin["symbol"]:
                symbol = coin["symbol"].upper()
                if symbol != "USDT":
                    symbols.append(symbol + "USDT")
        return symbols
    except Exception as e:
        st.error(f"Erro ao buscar top 100 moedas: {e}")
        return []

@st.cache_data(ttl=300)
def get_klines(symbol, interval="1h", limit=100):
    """Pega histórico de candles do Binance"""
    url = f"https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    r = requests.get(url, params=params)
    if r.status_code != 200:
        return None
    df = pd.DataFrame(r.json(), columns=[
        "timestamp", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "number_of_trades",
        "taker_buy_base", "taker_buy_quote", "ignore"
    ])
    df["close"] = df["close"].astype(float)
    return df

def classificar_rsi(rsi):
    if rsi <= 30:
        return "Sobrevendida"
    elif rsi >= 70:
        return "Sobrecomprada"
    else:
        return "Neutra"

def classificar_tendencia(ema20, ema50):
    if ema20 > ema50:
        return "Alta"
    elif ema20 < ema50:
        return "Baixa"
    else:
        return "Neutra"

def analisar_moeda(symbol):
    df = get_klines(symbol, interval=binance_interval, limit=limite_velas)
    if df is None or df.empty or len(df) < 50:
        return None

    rsi = RSIIndicator(close=df["close"]).rsi().iloc[-1]
    ema20 = EMAIndicator(close=df["close"], window=20).ema_indicator().iloc[-1]
    ema50 = EMAIndicator(close=df["close"], window=50).ema_indicator().iloc[-1]
    preco = df["close"].iloc[-1]

    return {
        "Moeda": symbol.replace("USDT", ""),
        "Preço (USDT)": round(preco, 4),
        "RSI": round(rsi, 2),
        "Classificação RSI": classificar_rsi(rsi),
        "Tendência": classificar_tendencia(ema20, ema50),
        "Alerta": "✅ RSI ≤ 30 e Tendência de Alta" if rsi <= 30 and ema20 > ema50 else ""
    }

# ====== EXECUÇÃO PRINCIPAL ======
with st.spinner("🔍 Analisando mercado..."):
    symbols = get_top_100_symbols()
    resultados = []
    for sym in symbols:
        analise = analisar_moeda(sym)
        if analise:
            resultados.append(analise)

# ====== EXIBIÇÃO ======
if resultados:
    df = pd.DataFrame(resultados)
    alertas = df[df["Alerta"] != ""]

    st.subheader("📋 Resultado Geral")
    st.dataframe(df, use_container_width=True)

    if not alertas.empty:
        st.subheader("🚨 Alertas Encontrados")
        st.dataframe(alertas, use_container_width=True)
    else:
        st.success("Nenhuma moeda com RSI ≤ 30 e tendência de alta no momento.")
else:
    st.warning("⚠️ Nenhum dado válido retornado pela API.")
