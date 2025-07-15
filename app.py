import streamlit as st
import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator

st.set_page_config(page_title="Radar RSI Cripto", layout="wide")
st.title("📊 Radar RSI com Tendência de Alta")
st.markdown("Analisa as principais criptos com RSI e EMAs em tempo real via Binance API.")

# ===== INTERVALOS E PARÂMETROS =====
intervalo = st.selectbox("⏱️ Intervalo de tempo", ["1h", "4h", "1d"], index=0)
binance_interval = {"1h": "1h", "4h": "4h", "1d": "1d"}[intervalo]
limite_velas = 100

# Filtro por Top moedas
limite_moedas = st.selectbox("🏆 Quantidade de moedas a analisar", [20, 50, 100], index=2)

# Botão de atualização
executar_analise = st.button("🔄 Atualizar agora")

# ===== FUNÇÕES AUXILIARES =====
@st.cache_data(ttl=300)
def get_top_symbols(limit=100):
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": limit,
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
        st.error(f"Erro ao buscar top moedas: {e}")
        return []

@st.cache_data(ttl=300)
def get_klines(symbol, interval="1h", limit=100):
    url = f"https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    r = requests.get(url, params=params)
    if r.status_code != 200:
        return None
    df = pd.DataFrame(r.json(), columns=[
        "timestamp", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_vol_
