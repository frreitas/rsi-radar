# app.py
import streamlit as st
import pandas as pd
import requests
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator

st.set_page_config(page_title="Radar RSI Cripto", layout="wide")

st.title("📊 Radar RSI com Tendência de Alta")
st.markdown("Filtra moedas com **RSI ≤ 30** e **tendência de alta** (EMA20 > EMA50) usando dados da Binance.")

# Lista de símbolos que deseja acompanhar
symbols = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "DOGEUSDT", "XRPUSDT",
    "ADAUSDT", "AVAXUSDT", "LINKUSDT", "DOTUSDT", "TRXUSDT", "MATICUSDT"
]

@st.cache_data(ttl=300)
def get_klines(symbol, interval="1h", limit=100):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    r = requests.get(url)
    df = pd.DataFrame(r.json(), columns=[
        "timestamp", "open", "high", "low", "close", "volume", "close_time",
        "qav", "trades", "tb_base", "tb_quote", "ignore"
    ])
    df["close"] = df["close"].astype(float)
    return df

def analyze(symbol):
    try:
        df = get_klines(symbol)
        rsi = RSIIndicator(close=df["close"]).rsi()
        ema20 = EMAIndicator(close=df["close"], window=20).ema_indicator()
        ema50 = EMAIndicator(close=df["close"], window=50).ema_indicator()
        last = df.iloc[-1]

        return {
            "Moeda": symbol,
            "Preço": round(last["close"], 4),
            "RSI": round(rsi.iloc[-1], 2),
            "EMA20 > EMA50": ema20.iloc[-1] > ema50.iloc[-1],
        }
    except:
        return None

# Coletar e filtrar
dados = [analyze(sym) for sym in symbols]
df = pd.DataFrame([d for d in dados if d])

# Filtrar
resultado = df[(df["RSI"] <= 30) & (df["EMA20 > EMA50"])]

st.success(f"Moedas encontradas: {len(resultado)}")
st.dataframe(resultado, use_container_width=True)
