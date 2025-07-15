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
limite_vela_
