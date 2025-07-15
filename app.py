import streamlit as st
import requests
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator
from datetime import datetime, timedelta
import plotly.graph_objects as go

st.set_page_config(page_title="Análise Técnica Cripto", layout="wide")
st.title("📈 Análise Técnica de Criptomoedas")

# ==== FUNÇÃO PARA OBTER TOP 100 COINS ====
@st.cache_data(ttl=3600)
def get_top_100_coins():
    url = "https://min-api.cryptocompare.com/data/top/mktcapfull?limit=100&tsym=USD"
    try:
        res = requests.get(url)
        res.raise_for_status()
        data = res.json().get("Data", [])
        coins = []
        for coin in data:
            symbol = coin["CoinInfo"]["Name"]
            name = coin["CoinInfo"]["FullName"]
            coins.append(f"{name} ({symbol})")
        return coins
    except:
        st.error("Erro ao obter lista de moedas.")
        return ["Bitcoin (BTC)"]

# ==== CONFIGURAÇÕES INICIAIS ====
col1, col2 = st.columns([2, 1])
with col1:
    selected_coin = st.selectbox("💰 Selecione a moeda", get_top_100_coins())
    coin_symbol = selected_coin.split("(")[-1].replace(")", "").strip()

with col2:
    timeframe = st.selectbox("⏱️ Timeframe do RSI", ["1h", "4h", "1d", "1w", "1M"])

# ==== OBTÉM PREÇO, VARIAÇÃO E VOLUME ====
@st.cache_data(ttl=600)
def get_price_info(symbol):
    url = f"https://min-api.cryptocompare.com/data/pricemultifull?fsyms={symbol}&tsyms=USD"
    res = requests.get(url)
    res.raise_for_status()
    data = res.json()["RAW"][symbol]["USD"]
    return {
        "price": data["PRICE"],
        "change_pct": data["CHANGEPCT24HOUR"],
        "volume": data["TOTALVOLUME24H"]
    }

try:
    info = get_price_info(coin_symbol)
    price = info["price"]
    change = info["change_pct"]
    volume = info["volume"]
except:
    price, change, volume = None, None, None
    st.warning("⚠️ Não foi possível obter dados da moeda.")

# ==== EXIBE CARDS ====
col1, col2, col3 = st.columns(3)
col1.metric("💵 Preço Atual", f"${price:,.2f}" if price else "–")
col2.metric("📊 Variação 24h", f"{change:.2f}%" if change else "–")
col3.metric("📈 Volume 24h", f"${volume:,.0f}" if volume else "–")

st.markdown("---")

# ==== INSERÇÃO MANUAL DAS MÉTRICAS ====
st.subheader("📋 Análise Técnica Manual")

col1, col2, col3, col4 = st.columns(4)
with col1:
    rsi_val = st.number_input("RSI Atual", min_value=0.0, max_value=100.0, step=0.1)
with col2:
    ema8 = st.number_input("EMA 8 (Semanal)", step=0.01)
with col3:
    ema21 = st.number_input("EMA 21 (Semanal)", step=0.01)
with col4:
    ema56 = st.number_input("EMA 56 (Semanal)", step=0.01)

ema200 = st.number_input("EMA 200 (Semanal)", step=0.01)

# ==== ESTRUTURA DE ANÁLISE ====
def definir_estrutura_ema(p, e8, e21, e56, e200):
    if all([p > e for e in [e8, e21, e56, e200]]):
        return "Alta consolidada"
    elif all([p < e for e in [e8, e21, e56, e200]]):
        return "Baixa consolidada"
    else:
        return "Neutra/Transição"

def classificar_rsi(rsi):
    if rsi < 30:
        return "Sobrevendido"
    elif rsi > 70:
        return "Sobrecomprado"
    else:
        return "Neutro"

def classificar_volume(v):
    if v is None:
        return "Indefinido"
    elif v > 0:
        return "Subindo"
    else:
        return "Caindo"

def recomendacao_final(estrutura, rsi_class, vol_class):
    if estrutura == "Alta consolidada":
        if rsi_class == "Sobrevendido" and vol_class == "Subindo":
            return "✅ Compra"
        elif rsi_class == "Neutro" and vol_class == "Subindo":
            return "🟡 Acumular / Espera"
        elif rsi_class == "Sobrecomprado":
            return "⚠️ Aguardar correção"
    elif estrutura == "Baixa consolidada":
        return "❌ Venda / Evitar"
    elif estrutura == "Neutra/Transição":
        if rsi_class == "Sobrevendido":
            return "⚠️ Observar"
        elif rsi_class == "Neutro" and vol_class == "Caindo":
            return "🟡 Espera"
        elif rsi_class == "Sobrecomprado":
            return "⚠️ Venda parcial"
    return "–"

# ==== APLICA ANÁLISE ====
if all([price, rsi_val, ema8, ema21, ema56, ema200]):
    estrutura = definir_estrutura_ema(price, ema8, ema21, ema56, ema200)
    rsi_class = classificar_rsi(rsi_val)
    vol_class = classificar_volume(change)
    final = recomendacao_final(estrutura, rsi_class, vol_class)

    st.markdown("### 🔍 Resultado da Análise")
    with st.container():
        st.markdown(f"""
        <div style="border:1px solid #ccc; padding:16px; border-radius:10px;">
            <h4>{selected_coin}</h4>
            <p><strong>Timeframe RSI:</strong> {timeframe}</p>
            <p><strong>RSI:</strong> {rsi_val:.2f} ({rsi_class})</p>
            <p><strong>Estrutura EMAs:</strong> {estrutura}</p>
            <p><strong>Volume:</strong> {vol_class}</p>
            <h5 style="color:#004085; background-color:#d1ecf1; padding:8px; border-radius:5px;">
                Recomendação Final: {final}
            </h5>
        </div>
        """, unsafe_allow_html=True)

# ==== GRÁFICO DE SENTIMENTO ====
st.markdown("---")
st.subheader("📉 Sentimento do Mercado (Fear & Greed Index)")

@st.cache_data(ttl=600)
def get_fear_greed():
    url = "https://api.alternative.me/fng/?limit=1"
    res = requests.get(url)
    res.raise_for_status()
    return int(res.json()["data"][0]["value"])

try:
    fgi = get_fear_greed()
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=fgi,
        title={'text': "Índice Medo & Ganância"},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "black"},
            'steps': [
                {'range': [0, 25], 'color': "red"},
                {'range': [25, 50], 'color': "orange"},
                {'range': [50, 75], 'color': "yellow"},
                {'range': [75, 100], 'color': "green"}
            ]
        }
    ))
    st.plotly_chart(fig, use_container_width=True)
except:
    st.warning("Erro ao carregar Fear & Greed Index.")
