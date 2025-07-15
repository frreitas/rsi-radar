import streamlit as st
import requests
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator

st.set_page_config(page_title="Análise Técnica Cripto", layout="wide")
st.title("📊 Análise Técnica – RSI + EMAs Semanais")

# Inicializa histórico
if "historico" not in st.session_state:
    st.session_state["historico"] = []

# ---------- utilidades ----------
@st.cache_data(ttl=3600)
def get_top_cryptos(limit=100):
    url = "https://min-api.cryptocompare.com/data/top/mktcapfull"
    params = {"limit": limit, "tsym": "USD"}
    r = requests.get(url, params=params, timeout=15); r.raise_for_status()
    data = r.json()["Data"]
    return {f"{c['CoinInfo']['FullName']} ({c['CoinInfo']['Name']})": c["CoinInfo"]["Name"]
            for c in data if "CoinInfo" in c}

@st.cache_data(ttl=600)
def get_hist(symbol:str, endpoint:str, aggregate:int, limit:int=200):
    url = f"https://min-api.cryptocompare.com/data/v2/{endpoint}"
    params = {"fsym": symbol, "tsym": "USD", "aggregate": aggregate, "limit": limit}
    r = requests.get(url, params=params, timeout=15); r.raise_for_status()
    df = pd.DataFrame(r.json()["Data"]["Data"])
    df["close"] = df["close"].astype(float); df["open"] = df["open"].astype(float)
    return df

# ---------- UI ----------
moedas = get_top_cryptos()
if not moedas:
    st.stop()

col1, col2 = st.columns(2)
symbol_name = col1.selectbox("🪙 Moeda", list(moedas.keys()))
timeframe = col2.selectbox("⏱️ Timeframe RSI", ["1h", "4h", "1d", "1w"])
symbol = moedas[symbol_name]

# Tipo de operação baseado no timeframe
mapa_trade = {"1h": "Day Trade", "4h": "Swing Trade", "1d": "Position Trade", "1w": "Longo Prazo"}
tipo_trade = mapa_trade[timeframe]
st.info(f"🧭 **Tipo de operação sugerido com base no RSI:** {tipo_trade}")

# -------- PREÇO e VARIAÇÃO DIÁRIA (sempre 24h) --------
try:
    df_price = get_hist(symbol, "histoday", aggregate=1)
    price = df_price["close"].iloc[-1]
    var = price - df_price["open"].iloc[-1]
    var_pct = (var / df_price["open"].iloc[-1]) * 100
except:
    price = 0
    var = var_pct = 0

# -------- RSI conforme timeframe escolhido --------
try:
    if timeframe in ("1h", "4h"):
        aggregate = 1 if timeframe == "1h" else 4
        df_rsi = get_hist(symbol, "histohour", aggregate)
    else:
        aggregate = 1 if timeframe == "1d" else 7
        df_rsi = get_hist(symbol, "histoday", aggregate)
    rsi_val = round(RSIIndicator(df_rsi["close"]).rsi().iloc[-1], 2)
except:
    df_rsi = None
    rsi_val = st.number_input("📈 RSI (manual)", 0.0, 100.0, step=0.1)

# -------- EMAs SEMPRE SEMANAIS --------
try:
    df_week = get_hist(symbol, "histoday", aggregate=7)
    ema8  = round(EMAIndicator(df_week["close"], window=8 ).ema_indicator().iloc[-1], 2)
    ema21 = round(EMAIndicator(df_week["close"], window=21).ema_indicator().iloc[-1], 2)
    ema56 = round(EMAIndicator(df_week["close"], window=56).ema_indicator().iloc[-1], 2)
    ema200= round(EMAIndicator(df_week["close"], window=200).ema_indicator().iloc[-1], 2)
except:
    st.warning("❗ Erro ao carregar EMAs — insira manualmente:")
    ema8  = st.number_input("EMA 8w" , 0.0, step=0.1)
    ema21 = st.number_input("EMA 21w", 0.0, step=0.1)
    ema56 = st.number_input("EMA 56w", 0.0, step=0.1)
    ema200= st.number_input("EMA 200w", 0.0, step=0.1)

# ---------- métricas ----------
st.subheader("💵 Preço & Variação")
m1, m2 = st.columns(2)
m1.metric("Preço Atual", f"${price:,.2f}")
m2.metric("Variação (24h)", f"${var:,.2f}", delta=f"{var_pct:.2f}%")

# classificação RSI
rsi_class = "Sobrevendida" if rsi_val<=30 else "Sobrecomprada" if rsi_val>=70 else "Neutra"

# estrutura semanal
if ema8 > ema21 > ema56 > ema200:
    estrutura = "Alta consolidada"
elif ema8 < ema21 < ema56 < ema200:
    estrutura = "Baixa consolidada"
else:
    estrutura = "Neutra / transição"

# recomendação
if rsi_val<=30 and estrutura=="Alta consolidada":
    rec = "🟢 Bom sinal de entrada"
elif estrutura=="Alta consolidada" and rsi_class=="Neutra":
    rec = "🟡 Tendência forte; RSI neutro"
elif estrutura=="Baixa consolidada":
    rec = "🔴 Tendência de baixa"
else:
    rec = "⚪ Sem sinal claro"

# ---------- resultado ----------
resultado = {
    "Moeda": symbol_name,
    "Tipo de Trade": tipo_trade,
    "Timeframe RSI": timeframe,
    "Preço": f"${price:,.2f}",
    "RSI": rsi_val,
    "Classificação RSI": rsi_class,
    "EMA 8w": f"${ema8:,.2f}",
    "EMA 21w": f"${ema21:,.2f}",
    "EMA 56w": f"${ema56:,.2f}",
    "EMA 200w": f"${ema200:,.2f}",
    "Estrutura Semanal": estrutura,
    "Recomendação": rec
}

st.subheader("📋 Resultado da Análise")
st.dataframe(pd.DataFrame([resultado]), use_container_width=True, hide_index=True)

# histórico
if st.button("📌 Salvar Análise"):
    st.session_state["historico"].append(resultado)
    st.success("Salvo no histórico!")

if st.session_state["historico"]:
    st.subheader("📚 Histórico da Sessão")
    hist_df = pd.DataFrame(st.session_state["historico"])
    st.dataframe(hist_df, use_container_width=True, hide_index=True)
    st.download_button("⬇️ Baixar CSV", hist_df.to_csv(index=False).encode(),
                       file_name="historico_analises.csv", mime="text/csv")

if st.button("🧹 Limpar Tudo"):
    st.session_state["historico"] = []
    st.experimental_rerun()
