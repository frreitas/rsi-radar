import streamlit as st
import requests
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator
from datetime import datetime

st.set_page_config(page_title="Radar Cripto Avançado", layout="wide")
st.title("📊 Radar RSI + EMAs + Volume")

if "historico" not in st.session_state:
    st.session_state["historico"] = []

@st.cache_data(ttl=3600)
def get_top_cryptos(limit=100):
    url = "https://min-api.cryptocompare.com/data/top/mktcapfull"
    params = {"limit": limit, "tsym": "USD"}
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()["Data"]
    return {f"{c['CoinInfo']['FullName']} ({c['CoinInfo']['Name']})": c["CoinInfo"]["Name"]
            for c in data if "CoinInfo" in c}

@st.cache_data(ttl=600)
def get_hist(symbol:str, endpoint:str, aggregate:int, limit:int=200):
    url = f"https://min-api.cryptocompare.com/data/v2/{endpoint}"
    params = {"fsym": symbol, "tsym": "USD", "aggregate": aggregate, "limit": limit}
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    df = pd.DataFrame(r.json()["Data"]["Data"])
    df["close"] = df["close"].astype(float)
    df["open"] = df["open"].astype(float)
    df["vol"] = df["volumeto"].astype(float)
    return df

moedas = get_top_cryptos()
if not moedas:
    st.stop()

col1, col2 = st.columns([2, 1])
symbol_name = col1.selectbox("💰 Escolha a Moeda", list(moedas.keys()))
timeframe = col2.selectbox("🕒 Timeframe RSI", ["1h", "4h", "1d", "1w"])
symbol = moedas[symbol_name]

mapa_trade = {"1h": "Day Trade", "4h": "Swing Trade", "1d": "Position", "1w": "Longo Prazo"}
tipo_trade = mapa_trade[timeframe]
st.markdown(f"### 🎯 Tipo de Operação: **{tipo_trade}**")

# Preço atual, variação e volume
try:
    df_price = get_hist(symbol, "histoday", aggregate=1)
    price = df_price["close"].iloc[-1]
    var = price - df_price["open"].iloc[-1]
    var_pct = (var / df_price["open"].iloc[-1]) * 100
    volume = df_price["vol"].iloc[-1]
except:
    price = var = var_pct = volume = 0

colv1, colv2, colv3 = st.columns(3)
colv1.metric("💵 Preço Atual (USD)", f"${price:,.2f}")
colv2.metric("📉 Variação (24h)", f"${var:,.2f}", delta=f"{var_pct:.2f}%")
colv3.metric("📊 Volume (24h)", f"${volume:,.0f}")

# RSI
try:
    if timeframe in ("1h", "4h"):
        aggregate = 1 if timeframe == "1h" else 4
        df_rsi = get_hist(symbol, "histohour", aggregate)
    else:
        aggregate = 1 if timeframe == "1d" else 7
        df_rsi = get_hist(symbol, "histoday", aggregate)
    rsi_val = round(RSIIndicator(df_rsi["close"]).rsi().iloc[-1], 2)
except:
    rsi_val = st.number_input("RSI (manual)", 0.0, 100.0)

# EMAs semanais
try:
    df_week = get_hist(symbol, "histoday", aggregate=7)
    ema8 = round(EMAIndicator(df_week["close"], 8 ).ema_indicator().iloc[-1], 2)
    ema21 = round(EMAIndicator(df_week["close"], 21).ema_indicator().iloc[-1], 2)
    ema56 = round(EMAIndicator(df_week["close"], 56).ema_indicator().iloc[-1], 2)
    ema200= round(EMAIndicator(df_week["close"], 200).ema_indicator().iloc[-1], 2)
except:
    ema8 = ema21 = ema56 = ema200 = 0

# Volume
try:
    vol_hoje = df_rsi["vol"].iloc[-1]
    vol_ontem = df_rsi["vol"].iloc[-2]
    tendencia_volume = "🔼 Subindo" if vol_hoje > vol_ontem else "🔽 Caindo"
except:
    tendencia_volume = "❔ Indefinido"

# Classificação RSI
rsi_class = "🟢 Sobrevendida" if rsi_val <= 30 else "🔴 Sobrecomprada" if rsi_val >= 70 else "⚪ Neutra"

# Estrutura EMAs semanais
if ema8 > ema21 > ema56 > ema200:
    estrutura = "📈 Alta consolidada"
elif ema8 < ema21 < ema56 < ema200:
    estrutura = "📉 Baixa consolidada"
else:
    estrutura = "⚪ Neutra / transição"

# Confluência
if rsi_val <= 30 and estrutura == "📈 Alta consolidada" and "Subindo" in tendencia_volume:
    rec = "🟢 Forte sinal de entrada (RSI sobrevendido + volume subindo + tendência de alta)"
elif estrutura == "📈 Alta consolidada" and rsi_class == "⚪ Neutra":
    rec = "🟡 Tendência de alta, RSI neutro"
elif estrutura == "📉 Baixa consolidada":
    rec = "🔴 Tendência de baixa consolidada, evitar entrada"
else:
    rec = "⚪ Sem confluência clara"

st.markdown(f"""
### 📋 Resultado da Análise
- **Moeda:** {symbol_name}
- **Timeframe RSI:** {timeframe}  
- **RSI Atual:** {rsi_val} → {rsi_class}  
- **EMAs Semanais:**
  - EMA 8: ${ema8:,.2f}
  - EMA 21: ${ema21:,.2f}
  - EMA 56: ${ema56:,.2f}
  - EMA 200: ${ema200:,.2f}  
- **Tendência pelas EMAs:** {estrutura}  
- **Volume:** {tendencia_volume}  
- **📌 Recomendação Final:** {rec}
""")

# Histórico
res = {
    "Moeda": symbol_name, "Timeframe RSI": timeframe, "RSI": rsi_val, "Classificação RSI": rsi_class,
    "EMA8": ema8, "EMA21": ema21, "EMA56": ema56, "EMA200": ema200,
    "Tendência": estrutura, "Volume": tendencia_volume, "Recomendação": rec,
    "Data": datetime.now().strftime("%d/%m %H:%M")
}

colh1, colh2 = st.columns([1, 1])
if colh1.button("💾 Salvar Análise"):
    st.session_state["historico"].append(res)
    st.success("Análise salva!")

if st.session_state["historico"]:
    st.subheader("📚 Histórico de Análises")
    df_hist = pd.DataFrame(st.session_state["historico"])
    st.dataframe(df_hist, use_container_width=True, hide_index=True)
    st.download_button("⬇️ Baixar CSV", df_hist.to_csv(index=False).encode(), "historico.csv", "text/csv")

if colh2.button("🧹 Limpar Tudo"):
    st.session_state["historico"] = []
    st.experimental_rerun()
