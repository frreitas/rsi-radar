import streamlit as st
import pandas as pd
import requests
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator
import plotly.graph_objects as go

st.set_page_config(page_title="Análise Técnica de Criptomoedas", layout="wide")

# --- Estilo CSS para visual limpo e profissional ---
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

    # Agrupamento especial para 4h
    if timeframe == "4h":
        df = agrupar_4h(df)

    # AGRUPAR para RSI SEMANAL e MENSAL:
    if timeframe == "1w":
        df = df.copy()
        df.set_index("time", inplace=True)
        df = df.resample("W-MON").last().dropna().reset_index()
    elif timeframe == "1M":
        df = df.copy()
        df.set_index("time", inplace=True)
        df = df.resample("M").last().dropna().reset_index()

    # Calcular RSI
    rsi_valor = RSIIndicator(close=df["close"], window=14).rsi().iloc[-1]
    rsi_class = classificar_rsi(rsi_valor)

    # Para EMAs e volume sempre usar dados diários (melhor base)
    df_diario = get_crypto_data(simbolo, "histoday", 400)
    if df_diario.empty or len(df_diario) < 50:
        st.error("Dados insuficientes para análise. Tente novamente mais tarde.")
        st.stop()
    df_diario["date"] = pd.to_datetime(df_diario["time"])

    # EMAs semanais
    df_semanal = df_diario.resample("W-MON", on="date").last().dropna()
    ema8 = EMAIndicator(close=df_semanal["close"], window=8).ema_indicator().iloc[-1]
    ema21 = EMAIndicator(close=df_semanal["close"], window=21).ema_indicator().iloc[-1]
    ema56 = EMAIndicator(close=df_semanal["close"], window=56).ema_indicator().iloc[-1]
    ema200 = EMAIndicator(close=df_semanal["close"], window=200).ema_indicator().iloc[-1]
    tendencia = classificar_tendencia(ema8, ema21, ema56, ema200, ema8_ant, ema21_ant, ema56_ant, ema200_ant, preco_atual)

    volume_atual = df_diario["volume"].iloc[-1]
    volume_medio = df_diario["volume"].mean()
    volume_class = classificar_volume(volume_atual, volume_medio)

    recomendacao = obter_recomendacao(tendencia, rsi_class, volume_class)
    texto_card, classe_card = style_recomendacao_card(recomendacao)

    preco_atual = df_diario["close"].iloc[-1]
    preco_ontem = df_diario["close"].iloc[-2]
    variacao = (preco_atual - preco_ontem) / preco_ontem * 100

# --- Exibição de Métricas ---
colA, colB, colC = st.columns(3)
colA.metric("💵 Preço Atual (USD)", f"${preco_atual:,.2f}", f"{variacao:.2f}%")
colB.metric("📊 Volume (24h)", f"${volume_atual:,.2f}")
colC.metric("📉 Volume Médio", f"${volume_medio:,.2f}")

st.divider()

# --- Análise Técnica ---
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

# --- Fear & Greed Index ---
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
    st.markdown("## 🔎 Análise por Filtros")

col_rsi, col_tendencia = st.columns(2)
with col_rsi:
    rsi_filtro = st.multiselect("Filtrar por RSI", ["Sobrevendido", "Neutro", "Sobrecomprado"])
with col_tendencia:
    tendencia_filtro = st.multiselect("Filtrar por Tendência", [
        "Alta consolidada", "Baixa consolidada",
        "Zona de Suporte", "Zona de Resistência", "Transição / Neutra"
    ])

resultados = []
moedas_data = get_top_100_cryptos()
for moeda in moedas_data:
    nome = moeda["CoinInfo"]["FullName"]
    simbolo = moeda["CoinInfo"]["Name"]

    df = get_crypto_data(simbolo, "histoday", 400)
    if df.empty or len(df) < 60:
        continue

    preco_atual = df["close"].iloc[-1]
    preco_ontem = df["close"].iloc[-2]
    variacao = (preco_atual - preco_ontem) / preco_ontem * 100

    rsi_valor = RSIIndicator(close=df["close"], window=14).rsi().iloc[-1]
    rsi_class = classificar_rsi(rsi_valor)

    df["date"] = pd.to_datetime(df["time"])
    df_semanal = df.resample("W-MON", on="date").last().dropna()
    if len(df_semanal) < 60:
        continue

    ema8 = EMAIndicator(close=df_semanal["close"], window=8).ema_indicator().iloc[-1]
    ema21 = EMAIndicator(close=df_semanal["close"], window=21).ema_indicator().iloc[-1]
    ema56 = EMAIndicator(close=df_semanal["close"], window=56).ema_indicator().iloc[-1]
    ema200 = EMAIndicator(close=df_semanal["close"], window=200).ema_indicator().iloc[-1]
    ema8_ant = EMAIndicator(close=df_semanal["close"], window=8).ema_indicator().iloc[-2]
    ema21_ant = EMAIndicator(close=df_semanal["close"], window=21).ema_indicator().iloc[-2]
    ema56_ant = EMAIndicator(close=df_semanal["close"], window=56).ema_indicator().iloc[-2]
    ema200_ant = EMAIndicator(close=df_semanal["close"], window=200).ema_indicator().iloc[-2]

    volume_atual = df["volume"].iloc[-1]
    volume_medio = df["volume"].mean()
    volume_class = classificar_volume(volume_atual, volume_medio)

    tendencia = classificar_tendencia(
        ema8, ema21, ema56, ema200,
        ema8_ant, ema21_ant, ema56_ant, ema200_ant,
        preco_atual
    )
    recomendacao = obter_recomendacao(tendencia, rsi_class, volume_class)

    if (not rsi_filtro or rsi_class in rsi_filtro) and (not tendencia_filtro or tendencia in tendencia_filtro):
        resultados.append({
            "Moeda": nome,
            "Variação (%)": round(variacao, 2),
            "RSI": f"{rsi_valor:.2f} ({rsi_class})",
            "Tendência": tendencia,
            "Volume": volume_class,
            "Recomendação": recomendacao
        })

if resultados:
    st.dataframe(pd.DataFrame(resultados).sort_values(by="Variação (%)", ascending=False))
else:
    st.warning("Nenhuma moeda corresponde aos filtros selecionados.")
