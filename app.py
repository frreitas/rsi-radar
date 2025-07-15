import streamlit as st
import pandas as pd
import requests
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator

st.set_page_config(page_title="Análise Técnica de Criptomoedas", layout="wide")
st.title("📊 Análise Técnica de Criptomoedas")

# ========= Funções auxiliares =========

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
        return "Sobrevendido"
    elif rsi > 70:
        return "Sobrecomprado"
    else:
        return "Neutro"

def classificar_tendencia(ema8, ema21, ema56, ema200):
    if ema8 > ema21 > ema56 > ema200:
        return "Alta consolidada"
    elif ema8 < ema21 < ema56 < ema200:
        return "Baixa consolidada"
    else:
        return "Neutra/Transição"

def classificar_volume(volume_atual, volume_medio):
    return "Subindo" if volume_atual >= volume_medio else "Caindo"

def obter_recomendacao(tendencia, rsi, volume):
    if tendencia == "Alta consolidada":
        if rsi == "Sobrevendido" and volume == "Subindo":
            return "✅ Compra"
        elif rsi == "Neutro" and volume == "Subindo":
            return "🟡 Acumular / Espera"
        elif rsi == "Sobrecomprado" and volume == "Subindo":
            return "⚠️ Aguardar correção"
    elif tendencia == "Baixa consolidada":
        return "❌ Venda / Evitar"
    elif tendencia == "Neutra/Transição":
        if rsi == "Sobrevendido" and volume == "Subindo":
            return "⚠️ Observar"
        elif rsi == "Neutro" and volume == "Caindo":
            return "🟡 Espera"
        elif rsi == "Sobrecomprado" and volume == "Subindo":
            return "⚠️ Venda parcial"
    return "🟡 Aguardar"

# ========= Interface =========

col1, col2 = st.columns([2, 1])
opcoes_moedas = ["BTC", "ETH", "XRP", "LTC", "ADA", "SOL", "MATIC", "DOGE", "DOT", "LINK", "AVAX"]

with col1:
    moeda = st.selectbox("💰 Moeda:", opcoes_moedas, index=0)
with col2:
    timeframe_rsi = st.selectbox("⏱️ Time Frame RSI:", ["1h", "4h", "1d", "1w", "1M"], index=2)

st.divider()
st.subheader("📈 Análise Técnica da Moeda Selecionada")

with st.spinner("🔄 Carregando dados..."):
    df = get_crypto_data(symbol=moeda)
    if df.empty or len(df) < 200:
        st.error("Erro: Dados insuficientes para análise.")
        st.stop()

    preco_atual = df["close"].iloc[-1]
    variacao = (df["close"].iloc[-1] - df["close"].iloc[-2]) / df["close"].iloc[-2] * 100
    volume_atual = df["volume"].iloc[-1]
    volume_medio = df["volume"].mean()

    rsi_valor = RSIIndicator(close=df["close"], window=14).rsi().iloc[-1]
    rsi_class = classificar_rsi(rsi_valor)

    ema8 = EMAIndicator(close=df["close"], window=8).ema_indicator().iloc[-1]
    ema21 = EMAIndicator(close=df["close"], window=21).ema_indicator().iloc[-1]
    ema56 = EMAIndicator(close=df["close"], window=56).ema_indicator().iloc[-1]
    ema200 = EMAIndicator(close=df["close"], window=200).ema_indicator().iloc[-1]
    tendencia = classificar_tendencia(ema8, ema21, ema56, ema200)

    volume_class = classificar_volume(volume_atual, volume_medio)
    recomendacao = obter_recomendacao(tendencia, rsi_class, volume_class)

# ========= Exibição =========

col_a, col_b, col_c = st.columns(3)
with col_a:
    st.metric("💵 Preço Atual", f"${preco_atual:,.2f}", f"{variacao:.2f}%")
with col_b:
    st.metric("📊 Volume (24h)", f"${volume_atual:,.2f}")
with col_c:
    st.metric("🔄 Volume Médio", f"${volume_medio:,.2f}")

st.divider()
st.subheader(f"📋 Análise Técnica – {moeda}")

st.markdown(f"""
- **Tendência (EMAs Semanais):** `{tendencia}`
- **RSI ({timeframe_rsi}):** `{round(rsi_valor, 2)} – {rsi_class}`
- **Volume Atual vs. Médio:** `{volume_class}`
""")

st.subheader("✅ Recomendação Final")
st.markdown(f"### {recomendacao}")
