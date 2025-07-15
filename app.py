import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator

st.set_page_config(page_title="Análise Cripto Técnica", layout="wide")
st.title("📊 Análise Técnica de Criptomoedas com RSI, EMAs e Volume")

# ========== Funções utilitárias ==========

@st.cache_data(ttl=600)
def get_crypto_data(symbol="BTC", limit=90):
    url = f"https://min-api.cryptocompare.com/data/v2/histoday?fsym={symbol}&tsym=USD&limit={limit}"
    r = requests.get(url)
    data = r.json()
    if data.get("Response") != "Success":
        return None
    df = pd.DataFrame(data["Data"]["Data"])
    df["time"] = pd.to_datetime(df["time"], unit="s")
    df.set_index("time", inplace=True)
    df["close"] = df["close"].astype(float)
    df["volume"] = df["volumeto"]
    return df

def classificar_rsi(rsi):
    if rsi < 30:
        return "Sobrevendido"
    elif rsi > 70:
        return "Sobrecomprado"
    else:
        return "Neutro"

def classificar_ema(ema8, ema21, ema56, ema200):
    if ema8 > ema21 > ema56 > ema200:
        return "Alta consolidada"
    elif ema8 < ema21 < ema56 < ema200:
        return "Baixa consolidada"
    else:
        return "Transição / Neutra"

def avaliar_volume(volume_atual, volume_medio):
    if volume_atual > volume_medio * 1.1:
        return "Subindo"
    elif volume_atual < volume_medio * 0.9:
        return "Caindo"
    else:
        return "Estável"

def gerar_recomendacao(tendencia, rsi_status, volume_status):
    if tendencia == "Alta consolidada":
        if rsi_status == "Sobrevendido" and volume_status == "Subindo":
            return "✅ Compra"
        elif rsi_status == "Neutro" and volume_status == "Subindo":
            return "🟡 Acumular / Esperar"
        elif rsi_status == "Sobrecomprado":
            return "⚠️ Aguardar correção"
    elif tendencia == "Baixa consolidada":
        return "❌ Venda / Evitar"
    else:
        if rsi_status == "Sobrevendido" and volume_status == "Subindo":
            return "⚠️ Observar possível reversão"
        return "🟡 Esperar"
    return "🔎 Análise inconclusiva"

# ========== Interface ==========

moedas = ["BTC", "ETH", "SOL", "XRP", "ADA", "DOGE", "AVAX", "DOT", "SHIB", "LTC"]
moeda = st.selectbox("💰 Selecione a moeda", moedas)
rsi_tf = st.selectbox("⏱️ Timeframe do RSI", ["1h", "4h", "1d", "1w"])

# ========== Dados da moeda ==========

with st.spinner("🔄 Carregando dados..."):
    df = get_crypto_data(symbol=moeda)
    if df is None or df.empty:
        st.error("Erro ao obter dados da moeda.")
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
    rec = gerar_recomendacao(tendencia, rsi_class, volume_class)

# ========== Exibição dos Dados ==========

st.markdown("### 💵 Dados de Mercado")
col1, col2, col3 = st.columns(3)
col1.metric("💰 Preço Atual (USD)", f"${preco_atual:,.2f}")
col2.metric("📈 Variação Diária", f"{variacao:.2f}%")
col3.metric("🔊 Volume do Dia", f"${volume_atual:,.0f}")

st.markdown("### 🧠 Análise Técnica")

with st.container():
    st.markdown("---")
    st.markdown(f"#### 📌 Recomendação Final: {rec}")

    col_a, col_b = st.columns(2)

    with col_a:
        st.write(f"**Moeda:** {moeda}")
        st.write(f"**Timeframe RSI:** {rsi_tf}")
        st.write(f"**RSI Atual:** {rsi:.2f} ({rsi_class})")
        st.write(f"**Volume:** {volume_class}")

    with col_b:
        st.write(f"**EMA 8:** {ema8:.2f}")
        st.write(f"**EMA 21:** {ema21:.2f}")
        st.write(f"**EMA 56:** {ema56:.2f}")
        st.write(f"**EMA 200:** {ema200:.2f}")
        st.write(f"**Tendência pelas EMAs:** {tendencia}")
