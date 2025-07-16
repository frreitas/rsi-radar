import streamlit as st
import pandas as pd
import requests
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator
import plotly.graph_objects as go

st.set_page_config(page_title="Análise Técnica de Criptomoedas", layout="wide")

# --- Estilo CSS ---
st.markdown("""
<style>
.main .block-container { max-width: 1100px; padding: 1rem 2rem; }
h1 { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-weight: 700; color: #1e293b; }
.stMetric {
    border-radius: 10px; box-shadow: 0 2px 6px rgb(0 0 0 / 0.1);
    background: #f9fafb; padding: 15px 20px; margin-bottom: 15px;
}
.analysis-container {
    background: #f3f4f6; padding: 20px 25px; border-radius: 12px;
    box-shadow: 0 3px 8px rgb(0 0 0 / 0.08); margin-top: 15px;
}
.recommendation-card {
    border-radius: 14px; padding: 25px 30px; font-weight: 700;
    font-size: 28px; max-width: 400px; margin: 20px auto;
    box-shadow: 0 5px 20px rgb(0 0 0 / 0.12); text-align: center; color: white;
}
.rec-compra { background-color: #2d7a2d; }
.rec-acumular { background-color: #d1a939; }
.rec-agardar { background-color: #d96f18; }
.rec-venda { background-color: #b02a2a; }
.rec-observar { background-color: #2b5bb1; }
.rec-espera { background-color: #6b7280; }
.rec-vendaparcial { background-color: #db8f91; }
.rec-default { background-color: #6b7280; }
.gauge-container { max-width: 500px; margin: 0 auto 35px auto; }
</style>
""", unsafe_allow_html=True)

st.title("📊 Análise Técnica de Criptomoedas")

# --- Funções auxiliares ---
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
    if timeframe == "1h":
        return "histohour", 200
    elif timeframe == "4h":
        return "histohour", 800
    else:
        return "histoday", 400

@st.cache_data(ttl=600)
def get_crypto_data(symbol, endpoint="histoday", limit=200):
    url = f"https://min-api.cryptocompare.com/data/v2/{endpoint}?fsym={symbol}&tsym=USD&limit={limit}"
    try:
        r = requests.get(url)
        r.raise_for_status()
        data = r.json()["Data"]["Data"]
        df = pd.DataFrame(data)
        df["close"] = df["close"].astype(float)
        df["volume"] = df["volumeto"].astype(float)
        df["time"] = pd.to_datetime(df["time"], unit='s')
        return df
    except:
        return pd.DataFrame()

def agrupar_4h(df):
    df = df.copy()
    df.set_index("time", inplace=True)
    df = df.resample("4H").agg({
        "close": "last",
        "volume": "sum",
        "open": "first",
        "high": "max",
        "low": "min"
    }).dropna().reset_index()
    return df

@st.cache_data(ttl=1800)
def get_fear_greed_index():
    url = "https://api.alternative.me/fng/?limit=1"
    try:
        r = requests.get(url)
        r.raise_for_status()
        return int(r.json()["data"][0]["value"])
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
        elif rsi == "Sobrecomprado":
            return "Aguardar correção"
    elif tendencia == "Baixa consolidada":
        if rsi == "Sobrevendido" and volume == "Subindo":
            return "Observar reversão potencial com stop curto"
        elif volume == "Caindo":
            return "Venda / Evitar"
        elif rsi == "Neutro" and volume == "Subindo":
            return "Observar cautelosamente"
    elif tendencia == "Neutra/Transição":
        if rsi == "Sobrevendido":
            return "Observar"
        elif rsi == "Neutro":
            return "Espera"
        elif rsi == "Sobrecomprado":
            return "Venda parcial para quem já está comprado; observar topo para quem não está dentro"
    return "Aguardar"

def style_recomendacao_card(text):
    estilos = {
        "Compra": ("Compra Forte", "rec-compra"),
        "Acumular / Espera": ("Atenção", "rec-acumular"),
        "Aguardar correção": ("Aguardar", "rec-agardar"),
        "Venda / Evitar": ("Venda Forte", "rec-venda"),
        "Observar": ("Observar", "rec-observar"),
        "Espera": ("Espera", "rec-espera"),
        "Venda parcial para quem já está comprado; observar topo para quem não está dentro": ("Venda Parcial", "rec-vendaparcial"),
        "Observar reversão potencial com stop curto": ("Observar Reversão", "rec-observar"),
        "Observar cautelosamente": ("Observar Cautelosamente", "rec-observar"),
        "Aguardar": ("Aguardar", "rec-default"),
    }
    return estilos.get(text, ("Desconhecido", "rec-default"))

# --- Interface ---
top_moedas = get_top_100_cryptos()
col1, col2 = st.columns([2, 1])

with col1:
    moeda = st.selectbox("Selecione a moeda", top_moedas)
    simbolo = extrair_simbolo(moeda)
with col2:
    timeframe = st.selectbox("Timeframe RSI", ["1h", "4h", "1d", "1w", "1M"], index=2)

st.divider()
st.subheader("📈 Análise Técnica")

with st.spinner("Carregando dados..."):
    endpoint, limite = get_timeframe_endpoint(timeframe)
    df = get_crypto_data(simbolo, endpoint, limite)
    if df.empty:
        st.error("Erro ao carregar dados.")
        st.stop()

    if timeframe == "4h":
        df = agrupar_4h(df)

    elif timeframe == "1M":
        df = df.copy()
        df.set_index("time", inplace=True)
        df = df.resample("M").agg({
            "close": "last",
            "volume": "sum",
            "open": "first",
            "high": "max",
            "low": "min"
        }).dropna().reset_index()

    rsi_valor = RSIIndicator(close=df["close"], window=14).rsi().iloc[-1]
    rsi_class = classificar_rsi(rsi_valor)

    df_diario = get_crypto_data(simbolo, "histoday", 400)
    df_diario["date"] = pd.to_datetime(df_diario["time"])
    df_semanal = df_diario.resample("W-MON", on="date").last().dropna()

    ema8 = EMAIndicator(close=df_semanal["close"], window=8).ema_indicator().iloc[-1]
    ema21 = EMAIndicator(close=df_semanal["close"], window=21).ema_indicator().iloc[-1]
    ema56 = EMAIndicator(close=df_semanal["close"], window=56).ema_indicator().iloc[-1]
    ema200 = EMAIndicator(close=df_semanal["close"], window=200).ema_indicator().iloc[-1]

    tendencia = classificar_tendencia(ema8, ema21, ema56, ema200)

    volume_atual = df_diario["volume"].iloc[-1]
    volume_medio = df_diario["volume"].mean()
    volume_class = classificar_volume(volume_atual, volume_medio)

    recomendacao = obter_recomendacao(tendencia, rsi_class, volume_class)
    texto_card, classe_card = style_recomendacao_card(recomendacao)

    preco_atual = df_diario["close"].iloc[-1]
    preco_ontem = df_diario["close"].iloc[-2]
    variacao = (preco_atual - preco_ontem) / preco_ontem * 100

# --- Exibição ---
colA, colB, colC = st.columns(3)
colA.metric("💵 Preço Atual (USD)", f"${preco_atual:,.2f}", f"{variacao:.2f}%")
colB.metric("📊 Volume (24h)", f"${volume_atual:,.2f}")
colC.metric("📉 Volume Médio", f"${volume_medio:,.2f}")

st.divider()

st.markdown(f"""
<div class="analysis-container">
    <h4 style="color:#334155;">Tendência (EMAs Semanais): <strong>{tendencia}</strong></h4>
    <h4 style="color:#334155;">RSI ({timeframe}): <strong>{rsi_valor:.2f} – {rsi_class}</strong></h4>
    <h4 style="color:#334155;">Volume Atual vs. Médio: <strong>{volume_class}</strong></h4>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="recommendation-card {classe_card}">
    {texto_card}
</div>
""", unsafe_allow_html=True)

# --- Índice de Medo e Ganância ---
fng = get_fear_greed_index()
if fng is not None:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=fng,
        title={"text": "Índice de Medo e Ganância"},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": "#1f77b4"},
            "steps": [
                {"range": [0, 25], "color": "#d62728"},
                {"range": [25, 50], "color": "#ff7f0e"},
                {"range": [50, 75], "color": "#bcbd22"},
                {"range": [75, 100], "color": "#2ca02c"}
            ],
            "threshold": {"line": {"color": "black", "width": 4}, "value": fng}
        }
    ))
    st.markdown('<div class="gauge-container">', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("""
    <div style="text-align:center; font-size: 14px; color: #64748b; margin-bottom: 35px;">
        0-25: Medo Extremo | 25-50: Medo | 50-75: Ganância | 75-100: Ganância Extrema
    </div>
    """, unsafe_allow_html=True)
else:
    st.info("Não foi possível carregar o Índice de Medo e Ganância.")
