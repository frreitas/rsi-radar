import streamlit as st
import requests
import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator

st.set_page_config(page_title="Análise Técnica Cripto", layout="wide")
st.title("📊 Análise Técnica - RSI e EMAs Semanais")

# Lista de moedas suportadas
moedas_disponiveis = {
    "Bitcoin (BTC)": "BTC",
    "Ethereum (ETH)": "ETH",
    "Solana (SOL)": "SOL",
    "XRP (XRP)": "XRP",
    "Litecoin (LTC)": "LTC"
}

# Histórico
if "historico" not in st.session_state:
    st.session_state["historico"] = []

# ===== Seleção da Moeda e Timeframe RSI =====
col1, col2 = st.columns(2)
with col1:
    moeda_nome = st.selectbox("🪙 Escolha a moeda", list(moedas_disponiveis.keys()))
with col2:
    timeframe_rsi = st.selectbox("⏱️ Timeframe do RSI", ["1d", "1w"])

symbol = moedas_disponiveis[moeda_nome]
market = f"{symbol}-USD"

# Obtenção dos candles semanais da CryptoCompare
@st.cache_data(ttl=600)
def get_candles(symbol, aggregate, limit):
    url = f"https://min-api.cryptocompare.com/data/v2/histoday"
    params = {
        "fsym": symbol,
        "tsym": "USD",
        "aggregate": aggregate,
        "limit": limit
    }
    try:
        res = requests.get(url, params=params)
        res.raise_for_status()
        data = res.json()["Data"]["Data"]
        df = pd.DataFrame(data)
        df["close"] = df["close"].astype(float)
        return df
    except Exception as e:
        return None

# Tentativa de buscar dados automáticos
st.subheader("📊 Dados Técnicos (automático se disponível)")

if timeframe_rsi == "1d":
    df = get_candles(symbol, aggregate=1, limit=200)
else:
    df = get_candles(symbol, aggregate=7, limit=200)

auto_data_ok = df is not None and not df.empty

if auto_data_ok:
    preco = round(df["close"].iloc[-1], 2)
    rsi = round(RSIIndicator(close=df["close"]).rsi().iloc[-1], 2)
    ema8 = round(EMAIndicator(close=df["close"], window=8).ema_indicator().iloc[-1], 2)
    ema21 = round(EMAIndicator(close=df["close"], window=21).ema_indicator().iloc[-1], 2)
    ema56 = round(EMAIndicator(close=df["close"], window=56).ema_indicator().iloc[-1], 2)
    ema200 = round(EMAIndicator(close=df["close"], window=200).ema_indicator().iloc[-1], 2)
else:
    st.warning("⚠️ Falha ao obter dados automáticos. Insira os dados manualmente.")
    preco = st.number_input("💰 Preço atual (USD)", min_value=0.0, step=0.01)
    rsi = st.number_input("📈 RSI", min_value=0.0, max_value=100.0, step=0.1)
    ema8 = st.number_input("EMA 8 (semanal)", min_value=0.0, step=0.1)
    ema21 = st.number_input("EMA 21 (semanal)", min_value=0.0, step=0.1)
    ema56 = st.number_input("EMA 56 (semanal)", min_value=0.0, step=0.1)
    ema200 = st.number_input("EMA 200 (semanal)", min_value=0.0, step=0.1)

# Classificação RSI
if rsi <= 30:
    rsi_class = "Sobrevendida"
elif rsi >= 70:
    rsi_class = "Sobrecomprada"
else:
    rsi_class = "Neutra"

# Estrutura de tendência semanal
if ema8 > ema21 > ema56 > ema200:
    estrutura = "Alta consolidada"
elif ema8 < ema21 < ema56 < ema200:
    estrutura = "Baixa consolidada"
else:
    estrutura = "Estrutura neutra / transição"

# Recomendação
if rsi <= 30 and estrutura == "Alta consolidada":
    recomendacao = "🟢 Bom sinal de entrada"
elif estrutura == "Alta consolidada" and rsi_class == "Neutra":
    recomendacao = "🟡 Tendência de alta com RSI neutro"
elif estrutura == "Baixa consolidada":
    recomendacao = "🔴 Tendência de baixa - Cautela"
else:
    recomendacao = "⚪ Sem sinal claro"

# Resultado
resultado = {
    "Moeda": moeda_nome,
    "Timeframe RSI": timeframe_rsi,
    "Preço Atual": preco,
    "RSI": rsi,
    "Classificação RSI": rsi_class,
    "EMA 8": ema8,
    "EMA 21": ema21,
    "EMA 56": ema56,
    "EMA 200": ema200,
    "Tendência": estrutura,
    "Recomendação": recomendacao
}

# Mostrar resultado
st.subheader("📋 Resultado da Análise")
df_result = pd.DataFrame([resultado])
st.dataframe(df_result, use_container_width=True, hide_index=True)

# Botão de salvar no histórico
if st.button("📌 Salvar Análise no Histórico"):
    st.session_state["historico"].append(resultado)
    st.success("Análise salva!")

# Histórico
if st.session_state["historico"]:
    st.subheader("📚 Histórico de Análises")
    df_hist = pd.DataFrame(st.session_state["historico"])
    st.dataframe(df_hist, use_container_width=True, hide_index=True)

    csv = df_hist.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Baixar Histórico CSV", data=csv, file_name="historico_analises.csv", mime="text/csv")

# Botão de reset
if st.button("🧹 Limpar Tudo"):
    st.session_state["historico"] = []
    st.experimental_rerun()
