import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator
import plotly.graph_objects as go

st.set_page_config(page_title="Análise Técnica de Criptomoedas", layout="wide")
st.title("📊 Análise Técnica de Criptomoedas")

# ========= Funções auxiliares =========

@st.cache_data(ttl=3600)
def get_top_100_cryptos():
    url = "https://min-api.cryptocompare.com/data/top/mktcapfull?limit=100&tsym=USD"
    try:
        res = requests.get(url)
        res.raise_for_status()
        data = res.json()["Data"]
        return [f"{c['CoinInfo']['FullName']} ({c['CoinInfo']['Name']})" for c in data]
    except:
        return ["Bitcoin (BTC)", "Ethereum (ETH)", "Solana (SOL)"]

def extrair_simbolo(moeda_str):
    return moeda_str.split("(")[-1].replace(")", "").strip()

@st.cache_data(ttl=600)
def get_timeframe_endpoint(timeframe):
    if timeframe in ["1h", "4h"]:
        return "histohour"
    return "histoday"

@st.cache_data(ttl=600)
def get_crypto_data(symbol, endpoint="histoday", limit=400):
    url = f"https://min-api.cryptocompare.com/data/v2/{endpoint}?fsym={symbol}&tsym=USD&limit={limit}"
    try:
        r = requests.get(url)
        r.raise_for_status()
        data = r.json()["Data"]["Data"]
        df = pd.DataFrame(data)
        df["close"] = df["close"].astype(float)
        df["volume"] = df["volumeto"].astype(float)
        return df
    except Exception as e:
        st.error(f"Erro ao buscar dados de {symbol}: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=1800)
def get_fear_greed_index():
    url = "https://api.alternative.me/fng/?limit=1"
    try:
        r = requests.get(url)
        r.raise_for_status()
        valor = int(r.json()["data"][0]["value"])
        return valor
    except:
        return None

def classificar_rsi(rsi):
    if rsi < 30: return "Sobrevendido"
    elif rsi > 70: return "Sobrecomprado"
    else: return "Neutro"

def classificar_tendencia(ema8, ema21, ema56, ema200):
    if ema8 > ema21 > ema56 > ema200:
        return "Alta consolidada"
    elif ema8 < ema21 < ema56 < ema200:
        return "Baixa consolidada"
    return "Neutra/Transição"

def classificar_volume(v_atual, v_medio):
    return "Subindo" if v_atual >= v_medio else "Caindo"

def obter_recomendacao(tendencia, rsi, volume):
    if tendencia == "Alta consolidada":
        if rsi == "Sobrevendido" and volume == "Subindo":
            return "Compra"
        elif rsi == "Neutro" and volume == "Subindo":
            return "Acumular / Espera"
        elif rsi == "Sobrecomprado" and volume == "Subindo":
            return "Aguardar correção"
    elif tendencia == "Baixa consolidada":
        return "Venda / Evitar"
    elif tendencia == "Neutra/Transição":
        if rsi == "Sobrevendido" and volume == "Subindo":
            return "Observar"
        elif rsi == "Neutro" and volume == "Caindo":
            return "Espera"
        elif rsi == "Sobrecomprado" and volume == "Subindo":
            return "Venda parcial"
    return "Aguardar"

# ========= Layout =========

top_moedas = get_top_100_cryptos()
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    moeda_selecionada = st.selectbox("Moeda", top_moedas)
    simbolo = extrair_simbolo(moeda_selecionada)
with col2:
    timeframe_rsi = st.selectbox("Timeframe RSI", ["1h", "4h", "1d", "1w", "1M"], index=2)
with col3:
    fear_greed = get_fear_greed_index()
    if fear_greed is not None:
        gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=fear_greed,
            title={"text": "Sentimento (F&G)"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 25], 'color': "#d9534f"},
                    {'range': [25, 50], 'color': "#f0ad4e"},
                    {'range': [50, 75], 'color': "#5bc0de"},
                    {'range': [75, 100], 'color': "#5cb85c"},
                ],
            }))
        st.plotly_chart(gauge, use_container_width=True)

st.divider()
st.subheader("📈 Dados Técnicos")

with st.spinner("Carregando..."):

    # Coleta dos dados
    df_rsi = get_crypto_data(simbolo, get_timeframe_endpoint(timeframe_rsi))
    df_diario = get_crypto_data(simbolo, "histoday")  # sempre para preco atual e EMAs

    if df_rsi.empty or df_diario.empty or len(df_diario) < 200:
        st.error("Erro: Dados insuficientes.")
        st.stop()

    preco_atual = df_diario["close"].iloc[-1]
    preco_ontem = df_diario["close"].iloc[-2]
    variacao_dia = (preco_atual - preco_ontem) / preco_ontem * 100

    volume_atual = df_diario["volume"].iloc[-1]
    volume_medio = df_diario["volume"].mean()

    rsi_valor = RSIIndicator(close=df_rsi["close"], window=14).rsi().iloc[-1]
    rsi_class = classificar_rsi(rsi_valor)

    ema8 = EMAIndicator(close=df_diario["close"], window=8).ema_indicator().iloc[-1]
    ema21 = EMAIndicator(close=df_diario["close"], window=21).ema_indicator().iloc[-1]
    ema56 = EMAIndicator(close=df_diario["close"], window=56).ema_indicator().iloc[-1]
    ema200 = EMAIndicator(close=df_diario["close"], window=200).ema_indicator().iloc[-1]

    tendencia = classificar_tendencia(ema8, ema21, ema56, ema200)
    volume_class = classificar_volume(volume_atual, volume_medio)
    recomendacao = obter_recomendacao(tendencia, rsi_class, volume_class)

# ========= Exibição dos Resultados =========

met1, met2, met3 = st.columns(3)
met1.metric("Preço Atual (USD)", f"${preco_atual:,.2f}", f"{variacao_dia:.2f}%")
met2.metric("Volume (24h)", f"${volume_atual:,.2f}")
met3.metric("Volume Médio", f"${volume_medio:,.2f}")

st.divider()

st.subheader(f"🔍 Análise Técnica – {moeda_selecionada}")

st.markdown(f"""
- **Tendência (EMAs Semanais):** `{tendencia}`
- **RSI ({timeframe_rsi}):** `{rsi_valor:.2f}` → `{rsi_class}`
- **Volume:** `{volume_class}`
""")

st.subheader("📌 Recomendação Final")
st.markdown(f"## {recomendacao}")
