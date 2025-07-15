import streamlit as st
import requests
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator

st.set_page_config(page_title="Análise Técnica Cripto", layout="wide")
st.title("📊 Análise Técnica - RSI e EMAs Semanais")

# Histórico de análises
if "historico" not in st.session_state:
    st.session_state["historico"] = []

# === Função para buscar top moedas ===
@st.cache_data(ttl=3600)
def get_top_cryptos(limit=100):
    url = f"https://min-api.cryptocompare.com/data/top/mktcapfull"
    params = {"limit": limit, "tsym": "USD"}
    try:
        res = requests.get(url, params=params)
        res.raise_for_status()
        data = res.json()["Data"]
        return {
            f"{coin['CoinInfo']['FullName']} ({coin['CoinInfo']['Name']})": coin["CoinInfo"]["Name"]
            for coin in data if "CoinInfo" in coin
        }
    except:
        st.error("Erro ao buscar a lista de moedas.")
        return {}

# Buscar moedas
moedas_disponiveis = get_top_cryptos()
if not moedas_disponiveis:
    st.stop()

# === Interface de seleção ===
col1, col2 = st.columns(2)
with col1:
    moeda_nome = st.selectbox("🪙 Escolha a moeda", list(moedas_disponiveis.keys()))
with col2:
    timeframe_rsi = st.selectbox("⏱️ Timeframe do RSI", ["1d", "1w"])

symbol = moedas_disponiveis[moeda_nome]

# === Função para buscar candles ===
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
        df = pd.DataFrame(res.json()["Data"]["Data"])
        df["close"] = df["close"].astype(float)
        df["open"] = df["open"].astype(float)
        return df
    except:
        return None

# Obter dados
df = get_candles(symbol, aggregate=1 if timeframe_rsi == "1d" else 7, limit=200)
auto_ok = df is not None and not df.empty

if auto_ok:
    preco = df["close"].iloc[-1]
    variacao = preco - df["open"].iloc[-1]
    variacao_pct = (variacao / df["open"].iloc[-1]) * 100
    rsi = round(RSIIndicator(close=df["close"]).rsi().iloc[-1], 2)
    ema8 = round(EMAIndicator(close=df["close"], window=8).ema_indicator().iloc[-1], 2)
    ema21 = round(EMAIndicator(close=df["close"], window=21).ema_indicator().iloc[-1], 2)
    ema56 = round(EMAIndicator(close=df["close"], window=56).ema_indicator().iloc[-1], 2)
    ema200 = round(EMAIndicator(close=df["close"], window=200).ema_indicator().iloc[-1], 2)
else:
    st.warning("⚠️ Dados automáticos indisponíveis. Preencha manualmente:")
    preco = st.number_input("💰 Preço atual (USD)", min_value=0.0, step=0.01)
    variacao = 0
    variacao_pct = 0
    rsi = st.number_input("📈 RSI", min_value=0.0, max_value=100.0, step=0.1)
    ema8 = st.number_input("EMA 8 (semanal)", min_value=0.0, step=0.1)
    ema21 = st.number_input("EMA 21 (semanal)", min_value=0.0, step=0.1)
    ema56 = st.number_input("EMA 56 (semanal)", min_value=0.0, step=0.1)
    ema200 = st.number_input("EMA 200 (semanal)", min_value=0.0, step=0.1)

# Mostrar métricas principais
st.subheader("💵 Preço Atual e Variação")
colA, colB = st.columns(2)
colA.metric("Preço Atual", f"${preco:,.2f}")
colB.metric("Variação do Dia", f"${variacao:,.2f}", delta=f"{variacao_pct:.2f}%")

# Classificações
rsi_class = (
    "Sobrevendida" if rsi <= 30 else
    "Sobrecomprada" if rsi >= 70 else
    "Neutra"
)

estrutura = (
    "Alta consolidada" if ema8 > ema21 > ema56 > ema200 else
    "Baixa consolidada" if ema8 < ema21 < ema56 < ema200 else
    "Estrutura neutra / transição"
)

recomendacao = (
    "🟢 Bom sinal de entrada" if rsi <= 30 and estrutura == "Alta consolidada" else
    "🟡 Tendência de alta com RSI neutro" if estrutura == "Alta consolidada" and rsi_class == "Neutra" else
    "🔴 Tendência de baixa - Cautela" if estrutura == "Baixa consolidada" else
    "⚪ Sem sinal claro"
)

# Mostrar resultado da análise
resultado = {
    "Moeda": moeda_nome,
    "Timeframe RSI": timeframe_rsi,
    "Preço Atual": f"${preco:,.2f}",
    "RSI": rsi,
    "Classificação RSI": rsi_class,
    "EMA 8": f"${ema8:,.2f}",
    "EMA 21": f"${ema21:,.2f}",
    "EMA 56": f"${ema56:,.2f}",
    "EMA 200": f"${ema200:,.2f}",
    "Tendência": estrutura,
    "Recomendação": recomendacao
}

st.subheader("📋 Resultado da Análise")
st.dataframe(pd.DataFrame([resultado]), use_container_width=True, hide_index=True)

# Salvar histórico
if st.button("📌 Salvar Análise no Histórico"):
    st.session_state["historico"].append(resultado)
    st.success("Análise salva!")

# Mostrar histórico
if st.session_state["historico"]:
    st.subheader("📚 Histórico de Análises")
    hist_df = pd.DataFrame(st.session_state["historico"])
    st.dataframe(hist_df, use_container_width=True, hide_index=True)
    csv = hist_df.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Baixar Histórico CSV", csv, "historico.csv", "text/csv")

# Reset
if st.button("🧹 Limpar Tudo"):
    st.session_state["historico"] = []
    st.experimental_rerun()
