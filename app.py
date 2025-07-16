import streamlit as st
import pandas as pd
import requests
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator
import plotly.graph_objects as go

st.set_page_config(page_title="Análise Técnica de Criptomoedas", layout="wide")
st.title("\U0001F4CA Análise Técnica de Criptomoedas")

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
    if timeframe == "1h": return "histohour", 200
    elif timeframe == "4h": return "histohour", 800
    else: return "histoday", 400

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
    df = df.resample("4H").agg({"close": "last", "volume": "sum", "open": "first", "high": "max", "low": "min"}).dropna().reset_index()
    return df

def classificar_rsi(rsi):
    if rsi < 30: return "Sobrevendido"
    elif rsi > 70: return "Sobrecomprado"
    else: return "Neutro"

def classificar_tendencia(ema8, ema21, ema56, ema200, ema8_ant, ema21_ant, ema56_ant, ema200_ant, preco_atual):
    def inclinacao_positiva(atual, anterior): return atual > anterior
    def distancia_segura(e1, e2, pct=0.01): return abs(e1 - e2) / e2 >= pct

    inclinadas_para_cima = all([
        inclinacao_positiva(ema8, ema8_ant),
        inclinacao_positiva(ema21, ema21_ant),
        inclinacao_positiva(ema56, ema56_ant),
        inclinacao_positiva(ema200, ema200_ant)
    ])
    inclinadas_para_baixo = all([
        not inclinacao_positiva(ema8, ema8_ant),
        not inclinacao_positiva(ema21, ema21_ant),
        not inclinacao_positiva(ema56, ema56_ant),
        not inclinacao_positiva(ema200, ema200_ant)
    ])

    if ema8 > ema21 > ema56 > ema200 and inclinadas_para_cima and all([
        distancia_segura(ema8, ema21),
        distancia_segura(ema21, ema56),
        distancia_segura(ema56, ema200)
    ]):
        return "Alta consolidada"

    elif ema8 < ema21 < ema56 < ema200 and inclinadas_para_baixo and all([
        distancia_segura(ema21, ema8),
        distancia_segura(ema56, ema21),
        distancia_segura(ema200, ema56)
    ]):
        return "Baixa consolidada"

    elif abs(preco_atual - ema200) / ema200 < 0.01 or abs(preco_atual - ema56) / ema56 < 0.01:
        return "Zona de Suporte"

    elif preco_atual < ema8 and (abs(preco_atual - ema8) / ema8 < 0.01 or abs(preco_atual - ema21) / ema21 < 0.01):
        return "Zona de Resistência"

    return "Transição / Neutra"

def classificar_volume(v_atual, v_medio):
    return "Subindo" if v_atual >= v_medio else "Caindo"

def obter_recomendacao(tendencia, rsi, volume):
    if tendencia == "Alta consolidada":
        if rsi == "Sobrevendido" and volume == "Subindo": return "Compra"
        elif rsi == "Neutro" and volume == "Subindo": return "Acumular / Espera"
        elif rsi == "Sobrecomprado": return "Aguardar correção"
        else: return "Manter posição e monitorar"
    elif tendencia == "Baixa consolidada":
        if rsi == "Sobrevendido" and volume == "Subindo": return "Observar reversão potencial com stop curto"
        elif volume == "Caindo": return "Venda / Evitar"
        elif rsi == "Neutro" and volume == "Subindo": return "Observar com cautela"
        else: return "Fora do ativo"
    elif tendencia == "Zona de Suporte":
        if rsi == "Sobrevendido" and volume == "Subindo": return "Entrada tática com stop abaixo do suporte"
        elif rsi == "Neutro": return "Observar reação no suporte"
        else: return "Aguardar confirmação de suporte"
    elif tendencia == "Zona de Resistência":
        if rsi == "Sobrecomprado" and volume == "Caindo": return "Possível topo - avaliar venda parcial"
        elif rsi == "Neutro" and volume == "Caindo": return "Evitar entrada próximo à resistência"
        elif volume == "Subindo": return "Observar possível rompimento com cautela"
        else: return "Zona arriscada - aguardar definição"
    elif tendencia == "Transição / Neutra":
        if rsi == "Sobrevendido": return "Observar para possível entrada em reversão"
        elif rsi == "Neutro": return "Esperar definição de tendência"
        elif rsi == "Sobrecomprado": return "Venda parcial / Observar possível topo"
        else: return "Sem ação definida - aguardar"
    return "Aguardar"

def style_recomendacao_card(text):
    estilos = {
        "Compra": ("Compra Forte", "rec-compra"),
        "Acumular / Espera": ("Atenção", "rec-acumular"),
        "Aguardar correção": ("Aguardar", "rec-aguardar"),
        "Venda / Evitar": ("Venda Forte", "rec-venda"),
        "Observar reversão potencial com stop curto": ("Observar", "rec-observar"),
        "Observar com cautela": ("Observar", "rec-observar"),
        "Entrada tática com stop abaixo do suporte": ("Entrada Estratégica", "rec-compra"),
        "Observar reação no suporte": ("Observar Suporte", "rec-observar"),
        "Aguardar confirmação de suporte": ("Aguardar", "rec-aguardar"),
        "Possível topo - avaliar venda parcial": ("Venda Parcial", "rec-vendaparcial"),
        "Evitar entrada próximo à resistência": ("Evitar Entrada", "rec-venda"),
        "Observar possível rompimento com cautela": ("Observar", "rec-observar"),
        "Observar para possível entrada em reversão": ("Observar Reversão", "rec-observar"),
        "Esperar definição de tendência": ("Espera", "rec-espera"),
        "Venda parcial / Observar possível topo": ("Venda Parcial", "rec-vendaparcial"),
        "Fora do ativo": ("Fora do Ativo", "rec-venda"),
        "Manter posição e monitorar": ("Manter Posição", "rec-espera"),
        "Sem ação definida - aguardar": ("Aguardar", "rec-default")
    }
    return estilos.get(text, ("Desconhecido", "rec-default"))

# Interface
moedas = get_top_100_cryptos()
col1, col2 = st.columns([2, 1])
with col1:
    moeda = st.selectbox("Selecione a moeda", moedas)
    simbolo = extrair_simbolo(moeda)
with col2:
    timeframe = st.selectbox("Timeframe RSI", ["1h", "4h", "1d", "1w", "1M"], index=2)

st.divider()
st.subheader("\U0001F4C8 Análise Técnica")

with st.spinner("Carregando dados..."):
    endpoint, limite = get_timeframe_endpoint(timeframe)
    df = get_crypto_data(simbolo, endpoint, limite)

    if df.empty:
        st.error("Erro ao carregar dados.")
        st.stop()

    if timeframe == "4h":
        df = agrupar_4h(df)
    elif timeframe == "1w":
        df = df.set_index("time").resample("W-MON").last().dropna().reset_index()
    elif timeframe == "1M":
        df = df.set_index("time").resample("M").last().dropna().reset_index()

    rsi_valor = RSIIndicator(close=df["close"], window=14).rsi().iloc[-1]
    rsi_class = classificar_rsi(rsi_valor)

    df_diario = get_crypto_data(simbolo, "histoday", 400)
    df_diario["date"] = pd.to_datetime(df_diario["time"])
    df_semanal = df_diario.resample("W-MON", on="date").last().dropna()

    ema8 = EMAIndicator(close=df_semanal["close"], window=8).ema_indicator().iloc[-1]
    ema21 = EMAIndicator(close=df_semanal["close"], window=21).ema_indicator().iloc[-1]
    ema56 = EMAIndicator(close=df_semanal["close"], window=56).ema_indicator().iloc[-1]
    ema200 = EMAIndicator(close=df_semanal["close"], window=200).ema_indicator().iloc[-1]
    ema8_ant = EMAIndicator(close=df_semanal["close"], window=8).ema_indicator().iloc[-2]
    ema21_ant = EMAIndicator(close=df_semanal["close"], window=21).ema_indicator().iloc[-2]
    ema56_ant = EMAIndicator(close=df_semanal["close"], window=56).ema_indicator().iloc[-2]
    ema200_ant = EMAIndicator(close=df_semanal["close"], window=200).ema_indicator().iloc[-2]

    preco_atual = df_diario["close"].iloc[-1]
    preco_ontem = df_diario["close"].iloc[-2]
    variacao = (preco_atual - preco_ontem) / preco_ontem * 100

    tendencia = classificar_tendencia(ema8, ema21, ema56, ema200, ema8_ant, ema21_ant, ema56_ant, ema200_ant, preco_atual)
    volume_atual = df_diario["volume"].iloc[-1]
    volume_medio = df_diario["volume"].mean()
    volume_class = classificar_volume(volume_atual, volume_medio)
    recomendacao = obter_recomendacao(tendencia, rsi_class, volume_class)
    texto_card, classe_card = style_recomendacao_card(recomendacao)

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

# Fear & Greed Index
@st.cache_data(ttl=3600)
def get_fear_greed_index():
    url = "https://api.alternative.me/fng/?limit=1"
    try:
        r = requests.get(url)
        r.raise_for_status()
        return int(r.json()["data"][0]["value"])
    except:
        return None

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
