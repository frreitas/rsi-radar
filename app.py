# --- IMPORTAÇÕES E CONFIGURAÇÕES INICIAIS ---
import streamlit as st
import pandas as pd
import requests
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator
import plotly.graph_objects as go

# Configuração da página do Streamlit
st.set_page_config(page_title="Análise Técnica de Criptomoedas", layout="wide")

# --- ESTILOS CSS PERSONALIZADOS ---
st.markdown("""
<style>
.main .block-container { max-width: 1100px; padding: 1rem 2rem; }
h1 { font-family: 'Segoe UI'; font-weight: 700; color: #1e293b; }
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
</style>
""", unsafe_allow_html=True)

# Título principal
st.title("📊 Análise Técnica de Criptomoedas")

# --- FUNÇÕES AUXILIARES ---
@st.cache_data(ttl=3600)
def get_crypto_data(symbol, endpoint="histoday", limit=200):
    """Busca dados históricos de preço e volume via API CryptoCompare"""
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

def agrupar_por(df, freq):
    """Agrupa o DataFrame pela frequência desejada (ex: 4H, W, M)"""
    df = df.set_index("time")
    df = df.resample(freq).agg({
        "close": "last",
        "volume": "sum",
        "open": "first",
        "high": "max",
        "low": "min",
    }).dropna().reset_index()
    return df

def classificar_rsi(rsi):
    """Classifica o RSI em Sobrevendido, Neutro ou Sobrecomprado"""
    if rsi < 30: return "Sobrevendido"
    elif rsi > 70: return "Sobrecomprado"
    else: return "Neutro"

def classificar_tendencia(ema8, ema21, ema56, ema200):
    """Define a tendência geral com base nas EMAs"""
    if ema8 > ema21 > ema56 > ema200:
        return "Alta consolidada"
    elif ema8 < ema21 < ema56 < ema200:
        return "Baixa consolidada"
    return "Neutra/Transição"

def classificar_volume(v_atual, v_medio):
    """Compara o volume atual com a média histórica"""
    return "Subindo" if v_atual >= v_medio else "Caindo"

def obter_recomendacao(tendencia, rsi, volume):
    """Combina estrutura de tendência, RSI e volume para dar a recomendação final"""
    if tendencia == "Alta consolidada":
        if rsi == "Sobrevendido" and volume == "Subindo":
            return "✅ Compra"
        elif rsi == "Neutro" and volume == "Subindo":
            return "🟡 Acumular / Espera"
        elif rsi == "Sobrecomprado" and volume == "Subindo":
            return "⚠️ Aguardar correção"
    elif tendencia == "Baixa consolidada":
        if rsi == "Sobrevendido" and volume == "Subindo":
            return "⚠️ Observar reversão potencial com stop curto"
        elif volume == "Caindo":
            return "❌ Venda / Evitar"
        elif rsi == "Neutro" and volume == "Subindo":
            return "⚠️ Observar cautelosamente"
    elif tendencia == "Neutra/Transição":
        if rsi == "Sobrevendido" and volume == "Subindo":
            return "⚠️ Observar"
        elif rsi == "Neutro" and volume == "Caindo":
            return "🟡 Espera"
        elif rsi == "Sobrecomprado":
            return "⚠️ Venda parcial ou esperar topo confirmado"
    return "🟡 Espera"

# --- INTERFACE DO USUÁRIO ---
moeda = st.selectbox("Selecione a moeda", ["Bitcoin (BTC)", "Ethereum (ETH)", "Solana (SOL)"])
simbolo = moeda.split("(")[-1].replace(")", "")  # extrai "BTC" do texto
timeframe = st.selectbox("Timeframe do RSI", ["1h", "4h", "1d", "1w", "1M"], index=2)

# --- CARREGAMENTO DOS DADOS ---
with st.spinner("Carregando dados..."):
    # Seleção do endpoint adequado
    df_base = get_crypto_data(simbolo, "histohour" if timeframe in ["1h", "4h"] else "histoday", 800)
    if df_base.empty:
        st.error("Erro ao buscar dados"); st.stop()

    # Mapeamento de timeframes para frequência de agrupamento
    freq_map = {"4h": "4H", "1d": "1D", "1w": "W", "1M": "M"}
    df = agrupar_por(df_base, freq_map.get(timeframe, "1D")) if timeframe != "1h" else df_base.copy()

    # --- CÁLCULO DE INDICADORES ---
    rsi_valor = RSIIndicator(close=df["close"], window=14).rsi().iloc[-1]
    rsi_class = classificar_rsi(rsi_valor)

    volume_atual = df["volume"].iloc[-1]
    volume_medio = df["volume"].mean()
    volume_class = classificar_volume(volume_atual, volume_medio)

    # EMAs são SEMPRE calculadas com base semanal para indicar tendência macro
    df_semanal = agrupar_por(df_base, "W")
    ema8 = EMAIndicator(close=df_semanal["close"], window=8).ema_indicator().iloc[-1]
    ema21 = EMAIndicator(close=df_semanal["close"], window=21).ema_indicator().iloc[-1]
    ema56 = EMAIndicator(close=df_semanal["close"], window=56).ema_indicator().iloc[-1]
    ema200 = EMAIndicator(close=df_semanal["close"], window=200).ema_indicator().iloc[-1]
    tendencia = classificar_tendencia(ema8, ema21, ema56, ema200)

    recomendacao_final = obter_recomendacao(tendencia, rsi_class, volume_class)

# --- EXIBIÇÃO DOS RESULTADOS ---
st.markdown(f"""
<div class='analysis-container'>
<h4>Estrutura EMAs Semanais: <strong>{tendencia}</strong></h4>
<h4>RSI ({timeframe}): <strong>{rsi_valor:.2f} – {rsi_class}</strong></h4>
<h4>Volume: <strong>{volume_class}</strong></h4>
</div>
""", unsafe_allow_html=True)

# Recomendação visual com tag do timeframe
st.markdown(f"""
<div class='recommendation-card rec-default'>
    <strong>{recomendacao_final}</strong><br>
    <small>(Baseado em RSI {timeframe})</small>
</div>
""", unsafe_allow_html=True)
