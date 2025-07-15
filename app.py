import streamlit as st
import pandas as pd
import requests
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator

# ================= CONFIGURAÇÃO DA PÁGINA =================
st.set_page_config(page_title="Análise Técnica de Criptomoedas", layout="wide")
st.title("📊 Análise Técnica de Criptomoedas")
st.markdown("Forneça os dados ou utilize a API para análise automatizada de RSI, EMAs e Volume.")

# ================= FUNÇÕES AUXILIARES =================
@st.cache_data(ttl=600)
def get_crypto_data(symbol="BTC", limit=300):
    url = f"https://min-api.cryptocompare.com/data/v2/histoday?fsym={symbol}&tsym=USD&limit={limit}"
    try:
        res = requests.get(url)
        res.raise_for_status()
        data = res.json()["Data"]["Data"]
        df = pd.DataFrame(data)
        df["close"] = df["close"].astype(float)
        df["volume"] = df["volumeto"].astype(float)
        return df
    except Exception as e:
        st.error(f"Erro ao obter dados da CryptoCompare: {e}")
        return pd.DataFrame()

def classificar_rsi(rsi):
    if rsi < 30:
        return "🔵 Sobrevendido"
    elif rsi > 70:
        return "🔴 Sobrecomprado"
    else:
        return "🟡 Neutro"

def classificar_ema(ema8, ema21, ema56, ema200):
    if ema8 > ema21 > ema56 > ema200:
        return "Alta Forte"
    elif ema8 > ema21:
        return "Alta Moderada"
    elif ema21 > ema8:
        return "Baixa Moderada"
    else:
        return "Baixa Forte"

def avaliar_volume(volume_atual, volume_medio):
    if volume_atual > volume_medio * 1.2:
        return "✅ Volume Alto"
    elif volume_atual < volume_medio * 0.8:
        return "⚠️ Volume Baixo"
    else:
        return "🔸 Volume Normal"

def gerar_recomendacao(tendencia, rsi_class, volume_class):
    if "Alta" in tendencia and "Sobrevendido" in rsi_class and "Alto" in volume_class:
        return "🟢 Sinal Forte de Compra"
    elif "Alta" in tendencia and "Neutro" in rsi_class:
        return "🟢 Tendência de Alta com RSI Neutro – Boa Entrada"
    elif "Baixa" in tendencia and "Sobrecomprado" in rsi_class:
        return "🔴 Tendência de Baixa com RSI Sobrecomprado – Evitar"
    else:
        return "🟡 Aguardar novo sinal ou reversão"

# ================= INTERFACE DE SELEÇÃO =================
opcoes_moedas = ["BTC", "ETH", "XRP", "LTC", "ADA", "SOL", "MATIC", "DOGE", "DOT", "LINK", "AVAX"]

col1, col2 = st.columns([2, 1])
with col1:
    moeda = st.selectbox("💰 Escolha a moeda:", opcoes_moedas, index=0)
with col2:
    timeframe_rsi = st.selectbox("⏱️ Time Frame RSI:", ["1h", "4h", "1d", "1w", "1M"], index=2)

st.divider()
st.subheader("📈 Análise Técnica da Moeda Selecionada")

# ================= OBTENDO E ANALISANDO DADOS =================
with st.spinner("🔄 Carregando dados..."):
    df = get_crypto_data(symbol=moeda, limit=300)
    if df.empty or len(df) < 200:
        st.error("Erro: Dados insuficientes para análise completa (EMA 200 exige 200 candles).")
        st.stop()

    preco_atual = df["close"].iloc[-1]
    variacao = (df["close"].iloc[-1] - df["close"].iloc[-2]) / df["close"].iloc[-2] * 100
    volume_atual = df["volume"].iloc[-1]
    volume_medio = df["volume"].mean()

    rsi = RSIIndicator(close=df["close"], window=14).rsi().iloc[-1]
    rsi_class = classificar_rsi(rsi)

    ema8 = EMAIndicator(close=df["close"], window=8).ema_indicator().iloc[-1]
    ema21 = EMAIndicator(close=df["close"], window=21).ema_indicator().iloc[-1]
    ema56 = EMAIndicator(close=df["close"], window=56).ema_indicator().iloc[-1]
    ema200 = EMAIndicator(close=df["close"], window=200).ema_indicator().iloc[-1]
    tendencia = classificar_ema(ema8, ema21, ema56, ema200)

    volume_class = avaliar_volume(volume_atual, volume_medio)
    recomendacao = gerar_recomendacao(tendencia, rsi_class, volume_class)

# ================= EXIBIÇÃO DOS RESULTADOS =================
col_a, col_b, col_c = st.columns(3)
with col_a:
    st.metric("💵 Preço Atual", f"${preco_atual:,.2f}", f"{variacao:.2f}%")
with col_b:
    st.metric("📊 Volume (24h)", f"${volume_atual:,.2f}")
with col_c:
    st.metric("🔄 Volume Médio", f"${volume_medio:,.2f}")

st.divider()

# Bloco de Análise Técnica
st.subheader(f"📋 Resultado da Análise Técnica – {moeda}")
with st.container():
    st.markdown(f"""
    **🧭 RSI ({timeframe_rsi}):** {round(rsi, 2)} → {rsi_class}  
    **📐 EMAs (Gráfico Semanal):**
    - EMA 8: ${ema8:,.2f}
    - EMA 21: ${ema21:,.2f}
    - EMA 56: ${ema56:,.2f}
    - EMA 200: ${ema200:,.2f}
    - **Tendência identificada:** `{tendencia}`  
    **📊 Volume Atual:** {volume_class}  
    """, unsafe_allow_html=True)

# Recomendação Final
st.subheader("✅ Recomendação Final")
st.markdown(f"### {recomendacao}")
